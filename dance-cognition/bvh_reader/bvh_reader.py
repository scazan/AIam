# adopted from BVHplay (http://sourceforge.net/projects/bvhplay/)

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../libs")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../experiments")

import cgkit.bvh
from geo import *
from numpy import array, dot
import numpy
import os
import cPickle
import copy
from transformations import euler_matrix
from collections import defaultdict

ASSUME_NO_TRANSLATIONAL_OFFSETS_IN_NON_ROOT = True

CHANNEL_TO_AXIS = {
    "Xrotation": "x",
    "Yrotation": "y",
    "Zrotation": "z",
}

class Joint:
    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.children = []
        self.channels = []
        self.has_parent = False
        self.parent = None
        self.translation = array([0.,0.,0.])
        self.translation_matrix = array([
            [0.,0.,0.,0.],
            [0.,0.,0.,0.],
            [0.,0.,0.,0.],
            [0.,0.,0.,0.] ])
        self.has_rotation = False
        self.has_static_rotation = False

    def addchild(self, childjoint):
        self.children.append(childjoint)
        childjoint.has_parent = True
        childjoint.parent = self

    def get_vertex(self):
        return array([
            self.worldpos[0],
            self.worldpos[1],
            self.worldpos[2],
            1])

    def get_vertices(self):
        result = []
        self.add_vertices_recurse(result)
        return result

    def add_vertices_recurse(self, vertices):
        vertices.append(self.get_vertex())
        for child in self.children:
            child.add_vertices_recurse(vertices)

    def populate_edges_from_vertices_recurse(self, vertices, edgelist):
        if self.has_parent:
            new_edge = edge(
              vertices[self.parent.index],
              vertices[self.index])
            edgelist.append(new_edge)

        for child in self.children:
            child.populate_edges_from_vertices_recurse(vertices, edgelist)

    def recreate_with_vertices(self, vertices):
        result = copy.copy(self)
        result.worldpos = vertices[self.index]
        if not ASSUME_NO_TRANSLATIONAL_OFFSETS_IN_NON_ROOT:
            result.children = [child.recreate_with_vertices(vertices)
                               for child in self.children]
        return result

    def Xposition(self):
        return self.worldpos[0]

    def Yposition(self):
        return self.worldpos[1]

    def Zposition(self):
        return self.worldpos[2]

    def Xrotation(self):
        return self.angles[0]

    def Yrotation(self):
        return self.angles[1]

    def Zrotation(self):
        return self.angles[2]


class Skeleton:
    def __init__(self, root_joint, keyframes, num_frames=0, dt=.033333333):
        self.root_joint = root_joint
        self.keyframes = keyframes
        self.num_frames = num_frames
        self.dt = dt
        self._get_rotation_info_by_processing_first_frame()

    def _get_rotation_info_by_processing_first_frame(self):
        self._process_bvhkeyframe(self.keyframes[0], self.root_joint)

    def set_pose_from_frame(self, t=None):
        self._process_bvhkeyframe(self.keyframes[t], self.root_joint)
        return self.root_joint

    def get_root_joint(self):
        return self.root_joint

    def get_joint(self, name):
        return self._find_joint_recurse(self.root_joint, name)

    def _find_joint_recurse(self, joint, searched_name):
        if joint.name == searched_name:
            return joint
        else:
            for child in joint.children:
                potential_find = self._find_joint_recurse(child, searched_name)
                if potential_find:
                    return potential_find

    def get_vertices(self, t):
        self._process_bvhkeyframe(self.keyframes[t], self.root_joint)
        return self.root_joint.get_vertices()

    def populate_edges_from_vertices(self, vertices, edges):
        self.root_joint.populate_edges_from_vertices_recurse(vertices, edges)

    def _process_bvhkeyframe(self, keyframe, joint, frame_data_index=0):
        keyframe_dict = dict()
        for channel in joint.channels:
            keyframe_dict[channel] = keyframe[frame_data_index]
            frame_data_index += 1

        if "Xposition" in keyframe_dict:
            translation_matrix = make_translation_matrix(
                keyframe_dict["Xposition"],
                keyframe_dict["Yposition"],
                keyframe_dict["Zposition"])

        if "Xrotation" in keyframe_dict:
            rotate = True
            rotation_channels = filter(lambda channel:
                                           channel in ["Xrotation", "Yrotation", "Zrotation"],
                                       joint.channels)
            joint.angles = [radians(keyframe_dict[channel]) for channel in rotation_channels]
            joint.axes = "r" + "".join([CHANNEL_TO_AXIS[channel] for channel in rotation_channels])
            joint.rotation = Euler(joint.angles, joint.axes)
            joint.has_rotation = True
            rotation_matrix = euler_matrix(*joint.angles, axes=joint.axes)
        else:
            rotate = False
            joint.has_rotation = False

        if joint.has_parent:
            parent_trtr = joint.parent.trtr
            localtoworld = dot(parent_trtr, joint.translation_matrix)
        else:
            localtoworld = dot(joint.translation_matrix, translation_matrix)

        if rotate:
            trtr = dot(localtoworld, rotation_matrix)
        else:
            trtr = localtoworld
        joint.trtr = trtr

        worldpos = array([
                  localtoworld[0,3],
                  localtoworld[1,3],
                  localtoworld[2,3],
                  localtoworld[3,3] ])
        joint.worldpos = worldpos

        for child in joint.children:
            frame_data_index = self._process_bvhkeyframe(keyframe, child, frame_data_index)
            if(frame_data_index == 0):
                raise Exception("fatal error")

        return frame_data_index


class ScaleInfo:
    min_x = None

class BvhReader(cgkit.bvh.BVHReader):
    def read(self):
        if self._cache_exists():
            self._read()
            self._load_from_cache()
        else:
            self._read()
            self._probe_static_rotations()
            self._probe_vertex_range()
            self._save_to_cache()
        self._set_static_rotations()

    def _cache_exists(self):
        return os.path.exists(self._cache_filename())

    def _load_from_cache(self):
        cache_filename = self._cache_filename()
        print "loading BVH cache from %s ..." % cache_filename
        f = open(cache_filename)
        self._scale_info = ScaleInfo()
        self._scale_info.__dict__ = cPickle.load(f)
        self._unique_rotations = cPickle.load(f)
        f.close()
        print "ok"

    def _save_to_cache(self):
        cache_filename = self._cache_filename()
        print "saving BVH cache to %s ..." % cache_filename
        f = open(cache_filename, "w")
        cPickle.dump(self._scale_info.__dict__, f)
        cPickle.dump(self._unique_rotations, f)
        f.close()
        print "ok"

    def _cache_filename(self):
        return "%s.cache" % self.filename

    def _read(self):
        cgkit.bvh.BVHReader.read(self)
        self._joint_index = 0
        self._joints = {}
        self._root_joint = self._process_node(self._root_nood)
        self.skeleton = self.create_skeleton()
        self.num_joints = self._joint_index

    def create_skeleton(self):
        return Skeleton(
          self._root_joint, keyframes = self.keyframes,
          num_frames=self.num_frames, dt=self.dt)

    def get_duration(self):
        return self.skeleton.num_frames * self.skeleton.dt

    def set_skeleton_pose_from_frame(self, skeleton, t):
        frame_index = self._frame_index(t)
        return self.skeleton.set_pose_from_frame(frame_index)

    def get_hierarchy(self):
        return self.skeleton

    def _frame_index(self, t):
        return int(t / self.skeleton.dt) % self.skeleton.num_frames

    def get_skeleton_vertices(self, t):
        frame_index = self._frame_index(t)
        return self.skeleton.get_vertices(frame_index)

    def vertices_to_edges(self, vertices):
        edges = []
        self.skeleton.populate_edges_from_vertices(vertices, edges)
        return edges

    def normalize_vector(self, v):
        return array([
            (v[0] - self._scale_info.min_x) / self._scale_info.scale_factor * 2 - 1,
            (v[1] - self._scale_info.min_y) / self._scale_info.scale_factor * 2 - 1,
            (v[2] - self._scale_info.min_z) / self._scale_info.scale_factor * 2 - 1])

    def skeleton_scale_vector(self, v):
        return array([
            (v[0] + 1) / 2 * self._scale_info.scale_factor + self._scale_info.min_x,
            (v[1] + 1) / 2 * self._scale_info.scale_factor + self._scale_info.min_y,
            (v[2] + 1) / 2 * self._scale_info.scale_factor + self._scale_info.min_z])

    def onHierarchy(self, root_nood):
        self._root_nood = root_nood
        self.keyframes = []

    def onMotion(self, num_frames, dt):
        self.num_frames = num_frames
        self.dt = dt

    def onFrame(self, values):
        self.keyframes.append(values)

    def _process_node(self, node, parentname='root'):
        name = node.name
        if (name == "End Site") or (name == "end site"):
            name = parentname + "End"
        b1 = Joint(name, self._joint_index)
        self._joint_index += 1
        b1.channels = node.channels
        b1.translation[0] = node.offset[0]
        b1.translation[1] = node.offset[1]
        b1.translation[2] = node.offset[2]

        b1.translation_matrix = make_translation_matrix(
            b1.translation[0],
            b1.translation[1],
            b1.translation[2])

        for child in node.children:
            b2 = self._process_node(child, name)
            b1.addchild(b2)

        self._joints[name] = b1
        return b1

    def print_pose(self, vertices):
        self._print_joint_recurse(vertices, self.skeleton.root_joint)
        print

    def _print_joint_recurse(self, vertices, joint):
        if joint.has_parent:
            print "%-3d -> %-3d: %f" % (
                joint.parent.index, joint.index,
                numpy.linalg.norm(
                    self.vertices[joint.parent.index] -
                    self.vertices[joint.index]))

        for child in joint.children:
            self._print_joint_recurse(vertices, child)

    def _probe_vertex_range(self):
        print "probing BVH vertex range..."
        self._scale_info = ScaleInfo()
        for n in range(self.num_frames):
            vertices = self.skeleton.get_vertices(n)
            for vertex in vertices:
                self._update_range_with_vector(*vertex[0:3])
        self._scale_info.scale_factor = max([
                self._scale_info.max_x - self._scale_info.min_x,
                self._scale_info.max_y - self._scale_info.min_y,
                self._scale_info.max_z - self._scale_info.min_z])
        print "ok"

    def _update_range_with_vector(self, x, y, z):
        if self._scale_info.min_x is None:
            self._scale_info.min_x = self._scale_info.max_x = x
            self._scale_info.min_y = self._scale_info.max_y = y
            self._scale_info.min_z = self._scale_info.max_z = z
        else:
            self._scale_info.min_x = min(self._scale_info.min_x, x)
            self._scale_info.min_y = min(self._scale_info.min_y, y)
            self._scale_info.min_z = min(self._scale_info.min_z, z)
            self._scale_info.max_x = max(self._scale_info.max_x, x)
            self._scale_info.max_y = max(self._scale_info.max_y, y)
            self._scale_info.max_z = max(self._scale_info.max_z, z)

    def _probe_static_rotations(self):
        print "probing static rotations..."
        self._unique_rotations = defaultdict(set)
        for n in range(self.num_frames):
            self.skeleton.set_pose_from_frame(n)
            root_joint = self.skeleton.get_root_joint()
            self._process_static_rotations_recurse(root_joint)
        print "ok"

    def _process_static_rotations_recurse(self, joint):
        if joint.has_rotation:
            self._update_rotations(joint)
        for child in joint.children:
            self._process_static_rotations_recurse(child)

    def _update_rotations(self, joint):
        previous_unique_rotations = self._unique_rotations[joint.name]
        if len(previous_unique_rotations) < 2:
            self._unique_rotations[joint.name].add(tuple(joint.angles))

    def _set_static_rotations(self):
        for name, joints in self._unique_rotations.iteritems():
            if len(joints) == 1:
                joint = self._joints[name]
                joint.has_static_rotation = True
