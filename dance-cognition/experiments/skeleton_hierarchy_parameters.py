import math
from angle_parameters import radians3d_to_vector6d, vector6d_to_radians3d
from bvh_reader.geo import *
from numpy import array, dot

class SkeletonHierarchyParametrization:
    def __init__(self, bvh_reader):
        self.bvh_reader = bvh_reader

    def joint_to_parameters(self, hips):
        parameters = []
        self._add_joint_parameters_recurse(hips, parameters)
        return parameters

    def _add_joint_parameters_recurse(self, joint, parameters):
        if not joint.hasparent:
            self._add_joint_transposition_parameters(joint, parameters)
        if joint.rotation:
            self._add_joint_rotation_parameters(joint, parameters)
        for child in joint.children:
            self._add_joint_parameters_recurse(child, parameters)

    def _add_joint_transposition_parameters(self, joint, parameters):
        vertex = joint.get_vertex()
        normalized_vector = self.bvh_reader.normalize_vector(
            self.bvh_reader.vertex_to_vector(vertex))
        parameters.extend(normalized_vector)

    def _add_joint_rotation_parameters(self, joint, parameters):
        rotation_radians = [math.radians(d) for d in joint.rotation]
        rotation_parameters = radians3d_to_vector6d(*rotation_radians)
        parameters.extend(rotation_parameters)


    def parameters_to_joint(self, parameters):
        any_frame = 0
        hips = self.bvh_reader.get_hips(any_frame)
        self._parameters_to_joint_recurse(parameters, hips)
        return hips

    def _parameters_to_joint_recurse(self, parameters, joint, parameter_index=0):
        if joint.hasparent:
            parent_trtr = joint.parent.trtr
            localtoworld = dot(parent_trtr, joint.transposition_matrix)
        else:
            normalized_vector = parameters[parameter_index:parameter_index+3]
            parameter_index += 3
            scaled_vector = self.bvh_reader.skeleton_scale_vector(normalized_vector)
            transposition_matrix = make_transposition_matrix(*scaled_vector)

            localtoworld = dot(joint.transposition_matrix, transposition_matrix)            
            trtr = localtoworld

        if joint.rotation:
            rotation_parameters = parameters[parameter_index:parameter_index+6]
            parameter_index += 6
            rotation_radians = vector6d_to_radians3d(rotation_parameters)
            rotation_degrees = [math.degrees(r) for r in rotation_radians]
            rotation_matrix = make_rotation_matrix(*rotation_degrees)
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
            parameter_index = self._parameters_to_joint_recurse(parameters, child, parameter_index)

        return parameter_index