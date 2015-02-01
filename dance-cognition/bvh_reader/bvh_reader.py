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
from transformations import euler_matrix
from collections import defaultdict
import math

CHANNEL_TO_AXIS = {
    "Xrotation": "x",
    "Yrotation": "y",
    "Zrotation": "z",
}

class JointDefinition:
    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.child_definitions = []
        self.channels = []
        self.translation_matrix = array([
            [0.,0.,0.,0.],
            [0.,0.,0.,0.],
            [0.,0.,0.,0.],
            [0.,0.,0.,0.] ])
        self.has_parent = False
        self.parent = None
        self.has_rotation = False
        self.has_static_rotation = False

    def add_child_definition(self, child_definition):
        self.child_definitions.append(child_definition)
        child_definition.has_parent = True
        child_definition.parent = self

    def create_joint(self, parent=None):
        joint = Joint(self, parent)
        for child_definition in self.child_definitions:
            child = child_definition.create_joint(parent=joint)
            joint.add_child(child)
        return joint

    def populate_edges_from_vertices_recurse(self, vertices, edgelist):
        if self.has_parent:
            new_edge = edge(
              vertices[self.parent.index],
              vertices[self.index])
            edgelist.append(new_edge)

        for child_definition in self.child_definitions:
            child_definition.populate_edges_from_vertices_recurse(vertices, edgelist)

class Joint:
    def __init__(self, definition, parent=None):
        self.definition = definition
        self.parent = parent
        self.translation = array([0.,0.,0.])
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def get_vertex(self):
        return array([
            self.worldpos[0],
            self.worldpos[1],
            self.worldpos[2],
            1])

    def get_vertices(self):
        result = []
        self._add_vertices_recurse(result)
        return result

    def _add_vertices_recurse(self, vertices):
        vertices.append(self.get_vertex())
        for child in self.children:
            child._add_vertices_recurse(vertices)

    def Xposition(self):
        return self.worldpos[0]

    def Yposition(self):
        return self.worldpos[1]

    def Zposition(self):
        return self.worldpos[2]

    def Xrotation(self):
        return math.degrees(self.angles[0])

    def Yrotation(self):
        return math.degrees(self.angles[1])

    def Zrotation(self):
        return math.degrees(self.angles[2])

    def set_vertices(self, vertices, recurse=True):
        self.worldpos = vertices[self.definition.index]
        if recurse:
            for child in self.children:
                child.set_vertices(vertices)

class Hierarchy:
    def __init__(self, root_node):
        self._joint_index = 0
        self._joint_definitions = {}
        self._root_joint_definition = self._process_node(root_node)
        self.num_joints = self._joint_index

    def _process_node(self, node, parentname='root'):
        name = node.name
        if (name == "End Site") or (name == "end site"):
            name = parentname + "End"
        joint_definition = JointDefinition(name, self._joint_index)
        self._joint_index += 1
        joint_definition.channels = node.channels

        joint_definition.offset = node.offset
        joint_definition.translation_matrix = make_translation_matrix(
            node.offset[0],
            node.offset[1],
            node.offset[2])

        if "Xrotation" in node.channels:
            joint_definition.rotation_channels = filter(
                lambda channel: channel in ["Xrotation", "Yrotation", "Zrotation"],
                node.channels)
            joint_definition.axes = "r" + "".join([
                    CHANNEL_TO_AXIS[channel] for channel in joint_definition.rotation_channels])
            joint_definition.has_rotation = True
        else:
            joint_definition.has_rotation = False

        for child_node in node.children:
            child_definition = self._process_node(child_node, name)
            joint_definition.add_child_definition(child_definition)

        self._joint_definitions[name] = joint_definition
        return joint_definition

    def create_pose(self):
        return Pose(self)

    def set_pose_vertices(self, pose, vertices, recurse=True):
        pose.get_root_joint().set_vertices(vertices, recurse)

    def set_pose_from_frame(self, pose, frame):
        self._set_joint_from_bvh_recurse(frame, pose.get_root_joint())
        self.update_pose_world_positions(pose)

    def get_root_joint_definition(self):
        return self._root_joint_definition

    def get_joint_definition(self, name):
        return self._joint_definitions[name]

    def _set_joint_from_bvh_recurse(self, frame, joint, frame_data_index=0):
        frame_dict = dict()
        for channel in joint.definition.channels:
            frame_dict[channel] = frame[frame_data_index]
            frame_data_index += 1

        if "Xposition" in frame_dict:
            joint.translation = array([
                    frame_dict["Xposition"],
                    frame_dict["Yposition"],
                    frame_dict["Zposition"]])

        if joint.definition.has_rotation:
            joint.angles = [radians(frame_dict[channel])
                            for channel in joint.definition.rotation_channels]
            joint.rotation = Euler(joint.angles, joint.definition.axes)

        for child in joint.children:
            frame_data_index = self._set_joint_from_bvh_recurse(frame, child, frame_data_index)
            if(frame_data_index == 0):
                raise Exception("fatal error")

        return frame_data_index

    def update_pose_world_positions(self, pose):
        self._update_world_position_recurse(pose.get_root_joint())

    def _update_world_position_recurse(self, joint):
        if joint.definition.has_parent:
            parent_trtr = joint.parent.trtr
            localtoworld = dot(parent_trtr, joint.definition.translation_matrix)
        else:
            translation_matrix = make_translation_matrix(*joint.translation)
            localtoworld = dot(joint.definition.translation_matrix, translation_matrix)

        if joint.definition.has_rotation:
            if joint.definition.has_static_rotation:
                rotation_matrix = self._static_rotation_matrix(joint)
            else:
                rotation_matrix = euler_matrix(*joint.angles, axes=joint.definition.axes)
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
            self._update_world_position_recurse(child)

    def _static_rotation_matrix(self, joint):
        if not hasattr(joint, "static_rotation_matrix"):
            joint.definition.static_rotation_matrix = euler_matrix(*joint.angles, axes=joint.definition.axes)
        return joint.definition.static_rotation_matrix

class Pose:
    def __init__(self, hierarchy):
        self._hierarchy = hierarchy
        self._root_joint = hierarchy.get_root_joint_definition().create_joint()
        self._create_joints_dict()

    def _create_joints_dict(self):
        self._joints_by_name = dict()
        self._populate_joints_dict_recurse(self._root_joint)

    def _populate_joints_dict_recurse(self, joint):
        self._joints_by_name[joint.definition.name] = joint
        for child in joint.children:
            self._populate_joints_dict_recurse(child)

    def get_root_joint(self):
        return self._root_joint

    def get_vertices(self):
        return self._root_joint.get_vertices()

    def get_joint(self, name):
        return self._joints_by_name[name]

class ScaleInfo:
    min_x = None

    def update_with_vector(self, x, y, z):
        if self.min_x is None:
            self.min_x = self.max_x = x
            self.min_y = self.max_y = y
            self.min_z = self.max_z = z
        else:
            self.min_x = min(self.min_x, x)
            self.min_y = min(self.min_y, y)
            self.min_z = min(self.min_z, z)
            self.max_x = max(self.max_x, x)
            self.max_y = max(self.max_y, y)
            self.max_z = max(self.max_z, z)

    def update_scale_factor(self):
        self.scale_factor = max([
                self.max_x - self.min_x,
                self.max_y - self.min_y,
                self.max_z - self.min_z])

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
        self.hierarchy = Hierarchy(self._root_nood)
        self.num_joints = self.hierarchy.num_joints
        self._duration = self.num_frames * self.frame_time

    def get_duration(self):
        return self._duration

    def set_pose_from_time(self, pose, t):
        frame_index = self._frame_index(t)
        return self.hierarchy.set_pose_from_frame(pose, self.frames[frame_index])

    def get_hierarchy(self):
        return self.hierarchy

    def create_pose(self):
        return self.hierarchy.create_pose()

    def _frame_index(self, t):
        return int(t / self.frame_time) % self.num_frames

    def vertices_to_edges(self, vertices):
        edges = []
        self.hierarchy.get_root_joint_definition().populate_edges_from_vertices_recurse(
            vertices, edges)
        return edges

    def onHierarchy(self, root_nood):
        self._root_nood = root_nood
        self.frames = []

    def onMotion(self, num_frames, frame_time):
        self.num_frames = num_frames
        self.frame_time = frame_time

    def onFrame(self, values):
        self.frames.append(values)

    def _probe_vertex_range(self):
        print "probing BVH vertex range..."
        self._scale_info = ScaleInfo()
        pose = self.hierarchy.create_pose()
        for n in range(self.num_frames):
            self.hierarchy.set_pose_from_frame(pose, self.frames[n])
            vertices = pose.get_vertices()
            for vertex in vertices:
                self._scale_info.update_with_vector(*vertex[0:3])
        self._scale_info.update_scale_factor()
        print "ok"

    def _probe_static_rotations(self):
        print "probing static rotations..."
        self._unique_rotations = defaultdict(set)
        pose = self.hierarchy.create_pose()
        for n in range(self.num_frames):
            self.hierarchy.set_pose_from_frame(pose, self.frames[n])
            root_joint = pose.get_root_joint()
            self._process_static_rotations_recurse(root_joint)
        print "ok"

    def _process_static_rotations_recurse(self, joint):
        if joint.definition.has_rotation:
            self._update_rotations(joint)
        for child in joint.children:
            self._process_static_rotations_recurse(child)

    def _update_rotations(self, joint):
        previous_unique_rotations = self._unique_rotations[joint.definition.name]
        if len(previous_unique_rotations) < 2:
            self._unique_rotations[joint.definition.name].add(tuple(joint.angles))

    def _set_static_rotations(self):
        for name, joints in self._unique_rotations.iteritems():
            if len(joints) == 1:
                joint_definition = self.hierarchy.get_joint_definition(name)
                joint_definition.has_static_rotation = True
