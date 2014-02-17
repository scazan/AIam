# adopted from BVHplay (http://sourceforge.

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../experiments")

import cgkit.bvh
from geo import *
from numpy import array, dot
import numpy
import os
import cPickle
from transformations import euler_matrix

CHANNEL_TO_AXIS = {
    "Xrotation": "x",
    "Yrotation": "y",
    "Zrotation": "z",
}

class joint:
    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.children = []
        self.channels = []
        self.hasparent = 0
        self.parent = 0
        self.translation = array([0.,0.,0.])
        self.translation_matrix = array([
            [0.,0.,0.,0.],
            [0.,0.,0.,0.],
            [0.,0.,0.,0.],
            [0.,0.,0.,0.] ])

    def addchild(self, childjoint):
        self.children.append(childjoint)
        childjoint.hasparent = 1
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
        if self.hasparent:
            new_edge = edge(
              vertices[self.parent.index],
              vertices[self.index])
            edgelist.append(new_edge)

        for child in self.children:
            child.populate_edges_from_vertices_recurse(vertices, edgelist)


class skeleton:
    def __init__(self, hips, keyframes, num_frames=0, dt=.033333333):
        self.hips = hips
        self.keyframes = keyframes
        self.num_frames = num_frames
        self.dt = dt

    def get_hips(self, t=None):
        self._process_bvhkeyframe(self.keyframes[t], self.hips)
        return self.hips

    def get_joint(self, name, t):
        hips = self.get_hips(t)
        return self._find_joint_recurse(hips, name)

    def _find_joint_recurse(self, joint, searched_name):
        if joint.name == searched_name:
            return joint
        else:
            for child in joint.children:
                potential_find = self._find_joint_recurse(child, searched_name)
                if potential_find:
                    return potential_find

    def get_vertices(self, t):
        self._process_bvhkeyframe(self.keyframes[t], self.hips)
        return self.hips.get_vertices()

    def populate_edges_from_vertices(self, vertices, edges):
        self.hips.populate_edges_from_vertices_recurse(vertices, edges)

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
            angles = [radians(keyframe_dict[channel]) for channel in rotation_channels]
            axes = "r" + "".join([CHANNEL_TO_AXIS[channel] for channel in rotation_channels])
            joint.rotation = Euler(angles, axes)
            rotation_matrix = euler_matrix(*angles, axes=axes)
        else:
            rotate = False
            joint.rotation = None

        if joint.hasparent:
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
            self._probe_range()
            self._save_to_cache()

    def _cache_exists(self):
        return os.path.exists(self._cache_filename())

    def _load_from_cache(self):
        cache_filename = self._cache_filename()
        print "loading BVH cache from %s ..." % cache_filename
        f = open(cache_filename)
        self._scale_info = ScaleInfo()
        self._scale_info.__dict__ = cPickle.load(f)
        f.close()
        print "ok"

    def _save_to_cache(self):
        cache_filename = self._cache_filename()
        print "saving BVH cache to %s ..." % cache_filename
        f = open(cache_filename, "w")
        cPickle.dump(self._scale_info.__dict__, f)
        f.close()
        print "ok"

    def _cache_filename(self):
        return "%s.cache" % self.filename

    def _read(self):
        cgkit.bvh.BVHReader.read(self)
        self._joint_index = 0
        hips = self._process_node(self.root)
        self.skeleton = skeleton(
          hips, keyframes = self.keyframes,
          num_frames=self.num_frames, dt=self.dt)
        self.num_joints = self._joint_index

    def get_duration(self):
        return self.skeleton.num_frames * self.skeleton.dt

    def get_hips(self, t):
        frame_index = self._frame_index(t)
        return self.skeleton.get_hips(frame_index)

    def get_joint(self, joint_name, t):
        frame_index = self._frame_index(t)
        return self.skeleton.get_joint(joint_name, frame_index)

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
            v[0] * self._scale_info.scale_factor + self._scale_info.min_x,
            v[1] * self._scale_info.scale_factor + self._scale_info.min_y,
            v[2] * self._scale_info.scale_factor + self._scale_info.min_z])

    def onHierarchy(self, root):
        self.root = root
        self.keyframes = []

    def onMotion(self, num_frames, dt):
        self.num_frames = num_frames
        self.dt = dt

    def onFrame(self, values):
        self.keyframes.append(values)

    def _process_node(self, node, parentname='hips'):
        name = node.name
        if (name == "End Site") or (name == "end site"):
            name = parentname + "End"
        b1 = joint(name, self._joint_index)
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
        return b1

    def print_pose(self, vertices):
        self._print_joint_recurse(vertices, self.skeleton.hips)
        print

    def _print_joint_recurse(self, vertices, joint):
        if joint.hasparent:
            print "%-3d -> %-3d: %f" % (
                joint.parent.index, joint.index,
                numpy.linalg.norm(
                    self.vertex_to_vector(vertices[joint.parent.index]) -
                    self.vertex_to_vector(vertices[joint.index])))

        for child in joint.children:
            self._print_joint_recurse(vertices, child)

    def _probe_range(self):
        print "probing BVH vertex range..."
        self._scale_info = ScaleInfo()
        for n in range(self.num_frames):
            vertices = self.skeleton.get_vertices(n)
            for vertex in vertices:
                self._update_range_with_vector(*self.vertex_to_vector(vertex))
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
