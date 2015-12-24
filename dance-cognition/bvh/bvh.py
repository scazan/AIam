# adopted from BVHplay (http://sourceforge.net/projects/bvhplay/)

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from numpy import array, dot
from transformations import euler_matrix
import math
from geo import Euler, make_translation_matrix, edge

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
    def __init__(self, root_node_definition):
        self.num_joints = 0
        self._joint_definitions = {}
        self._root_joint_definition = root_node_definition
        self._process_joint_definition(root_node_definition)

    def _process_joint_definition(self, joint_definition):
        for child_definition in joint_definition.child_definitions:
            self._process_joint_definition(child_definition)
        self._joint_definitions[joint_definition.name] = joint_definition
        self.num_joints += 1

    def create_pose(self):
        return Pose(self)

    def set_pose_vertices(self, pose, vertices, recurse=True):
        pose.get_root_joint().set_vertices(vertices, recurse)

    def set_pose_from_frame(self, pose, frame):
        self._set_joint_from_frame_recurse(frame, pose.get_root_joint())
        self.update_pose_world_positions(pose)

    def get_root_joint_definition(self):
        return self._root_joint_definition

    def get_joint_definition(self, name):
        return self._joint_definitions[name]

    def _set_joint_from_frame_recurse(self, frame, joint, frame_data_index=0):
        joint_dict = dict()
        for channel in joint.definition.channels:
            joint_dict[channel] = frame[frame_data_index]
            frame_data_index += 1

        self._set_joint_from_dict(joint, joint_dict)

        for child in joint.children:
            frame_data_index = self._set_joint_from_frame_recurse(frame, child, frame_data_index)
            if(frame_data_index == 0):
                raise Exception("fatal error")

        return frame_data_index

    def _set_joint_from_dict(self, joint, joint_dict):
        if "Xposition" in joint_dict:
            joint.translation = array([
                    joint_dict["Xposition"],
                    joint_dict["Yposition"],
                    joint_dict["Zposition"]])

        if joint.definition.has_rotation:
            joint.angles = [math.radians(joint_dict[channel])
                            for channel in joint.definition.rotation_channels]
            joint.rotation = Euler(joint.angles, joint.definition.axes)

    def set_pose_from_joint_dicts(self, pose, joint_dicts):
        self._set_joint_from_dicts_recurse(pose.get_root_joint(), joint_dicts)
        self.update_pose_world_positions(pose)

    def _set_joint_from_dicts_recurse(self, joint, joint_dicts):
        self._set_joint_from_dict(joint, joint_dicts[joint.definition.index])
        for child in joint.children:
            self._set_joint_from_dicts_recurse(child, joint_dicts)

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
            joint.definition.static_rotation_matrix = euler_matrix(
                *joint.definition.static_angles, axes=joint.definition.axes)
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
