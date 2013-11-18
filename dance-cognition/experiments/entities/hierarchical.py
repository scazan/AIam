from experiment import *
import math
from angle_parameters import radians3d_to_vector6d, vector6d_to_radians3d
from bvh_reader.geo import *
from numpy import array, dot

class Stimulus(BaseStimulus):
    def get_value(self):
        hips = self.bvh_reader.get_hips(self._t * self.args.bvh_speed)
        return self._joint_to_parameters(hips)

    def get_duration(self):
        return self.bvh_reader.get_duration() / self.args.bvh_speed

    def filename(self):
        return self.bvh_reader.filename

    def _joint_to_parameters(self, hips):
        parameters = []
        self._add_joint_parameters_recurse(hips, parameters, is_hips=True)
        return parameters

    def _add_joint_parameters_recurse(self, joint, parameters, is_hips=False):
        if not joint.hasparent and not is_hips:
            self._add_joint_transposition_parameters(joint, parameters)
        if joint.rotation_definition:
            self._add_joint_rotation_parameters(joint, parameters)
        for child in joint.children:
            self._add_joint_parameters_recurse(child, parameters)

    def _add_joint_transposition_parameters(self, joint, parameters):
        vertex = joint.get_vertex()
        normalized_vector = self.bvh_reader.normalize_vector(
            self.bvh_reader.vertex_to_vector(vertex))
        parameters.extend(normalized_vector)

    def _add_joint_rotation_parameters(self, joint, parameters):
        rotation_radians = [math.radians(degrees)
                            for channel, degrees in joint.rotation_definition]
        rotation_parameters = radians3d_to_vector6d(*rotation_radians)
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
        self._parameters_to_joint_recurse(parameters, hips, is_hips=True)
        return hips

    def _parameters_to_joint_recurse(self, parameters, joint, parameter_index=0, is_hips=False):
        if joint.hasparent:
            parent_trtr = joint.parent.trtr
            localtoworld = dot(parent_trtr, joint.transposition_matrix)
        else:
            if is_hips:
                localtoworld = joint.transposition_matrix
            else:
                normalized_vector = parameters[parameter_index:parameter_index+3]
                parameter_index += 3
                scaled_vector = self.bvh_reader.skeleton_scale_vector(normalized_vector)
                transposition_matrix = make_transposition_matrix(*scaled_vector)
                localtoworld = dot(joint.transposition_matrix, transposition_matrix)
            trtr = localtoworld

        if joint.rotation_definition:
            rotation_parameters = parameters[parameter_index:parameter_index+6]
            parameter_index += 6
            rotation_radians = vector6d_to_radians3d(rotation_parameters)

            index = 0
            rotation_definition = []
            for channel, _degrees in joint.rotation_definition:
                degrees = math.degrees(rotation_radians[index])
                rotation_definition.append((channel, degrees))
                index += 1
            rotation_matrix = make_rotation_matrix(rotation_definition)

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
