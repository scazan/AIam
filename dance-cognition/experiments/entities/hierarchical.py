from experiment import *
import math
from angle_parameters import EulerTo3Vectors, EulerToQuaternion
from bvh_reader.geo import *
from numpy import array, dot
from transformations import euler_matrix
import random

rotation_parametrizations = {
    "vectors": EulerTo3Vectors,
    "quaternion": EulerToQuaternion,
    }

class Entity(BaseEntity):
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("--rotation-parametrization", "-r",
                            choices=["vectors", "quaternion"])
        parser.add_argument("--translate", action="store_true")
        parser.add_argument("--translation-weight", type=float, default=1.)

    def __init__(self, args):
        self.rotation_parametrization = rotation_parametrizations[
            args.rotation_parametrization]

class Stimulus(BaseStimulus):
    def get_value(self):
        hips = self.bvh_reader.get_hips(self._t * self.args.bvh_speed)
        return self._joint_to_parameters(hips)

    def get_random_value(self):
        hips = self.bvh_reader.get_hips(
            random.uniform(0, self.bvh_reader.get_duration()))
        return self._joint_to_parameters(hips)

    def get_duration(self):
        return self.bvh_reader.get_duration() / self.args.bvh_speed

    def filename(self):
        return "%s.%s" % (self.bvh_reader.filename, self.args.rotation_parametrization)

    def _joint_to_parameters(self, hips):
        parameters = []
        self._add_joint_parameters_recurse(hips, parameters)
        return parameters

    def _add_joint_parameters_recurse(self, joint, parameters):
        if not joint.hasparent and self.args.translate:
            self._add_joint_translation_parameters(joint, parameters)
        if joint.rotation:
            self._add_joint_rotation_parameters(joint, parameters)
        for child in joint.children:
            self._add_joint_parameters_recurse(child, parameters)

    def _add_joint_translation_parameters(self, joint, parameters):
        vertex = joint.get_vertex()
        normalized_vector = self.bvh_reader.normalize_vector(
            self.bvh_reader.vertex_to_vector(vertex))
        weighted_vector = self.args.translation_weight * normalized_vector
        parameters.extend(weighted_vector)

    def _add_joint_rotation_parameters(self, joint, parameters):
        rotation_parameters = self.entity.rotation_parametrization.rotation_to_parameters(
            joint.rotation)
        parameters.extend(rotation_parameters)

class Scene(BaseScene):
    def draw_input(self, parameters):
        glColor3f(0, 1, 0)
        self._draw_skeleton(parameters)

    def draw_output(self, parameters):
        glColor3f(0.5, 0.5, 1.0)
        self._draw_skeleton(parameters)

    def _draw_skeleton(self, parameters):
        hips = self._parameters_to_joint(parameters)
        vertices = hips.get_vertices()
        
        glLineWidth(2.0)
        edges = self.bvh_reader.vertices_to_edges(vertices)
        for edge in edges:
            vector1 = self.bvh_reader.normalize_vector(self.bvh_reader.vertex_to_vector(edge.v1))
            vector2 = self.bvh_reader.normalize_vector(self.bvh_reader.vertex_to_vector(edge.v2))
            self._draw_line(vector1, vector2)

    def _parameters_to_joint(self, parameters):
        any_frame = 0
        hips = self.bvh_reader.get_hips(any_frame)
        self._parameters_to_joint_recurse(parameters, hips)
        return hips

    def _parameters_to_joint_recurse(self, parameters, joint, parameter_index=0):
        if joint.hasparent:
            parent_trtr = joint.parent.trtr
            localtoworld = dot(parent_trtr, joint.translation_matrix)
        else:
            if self.args.translate:
                weighted_vector = parameters[parameter_index:parameter_index+3]
                parameter_index += 3
                normalized_vector = numpy.array(weighted_vector) / self.args.translation_weight
                scaled_vector = self.bvh_reader.skeleton_scale_vector(normalized_vector)
                translation_matrix = make_translation_matrix(*scaled_vector)
                localtoworld = dot(joint.translation_matrix, translation_matrix)
            else:
                localtoworld = joint.translation_matrix
            trtr = localtoworld

        if joint.rotation:
            rotation_parameters = parameters[
                parameter_index:parameter_index+self.entity.rotation_parametrization.num_parameters]
            parameter_index += self.entity.rotation_parametrization.num_parameters
            rotation_angles = self.entity.rotation_parametrization.parameters_to_rotation(
                rotation_parameters, joint.rotation.axes)
            rotation_matrix = euler_matrix(*rotation_angles, axes=joint.rotation.axes)

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

    def _draw_line(self, v1, v2):
        glBegin(GL_LINES)
        glVertex3f(*v1)
        glVertex3f(*v2)
        glEnd()
