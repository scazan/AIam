from experiment import *
import math
from angle_parameters import EulerTo3Vectors, EulerToQuaternion
from bvh_reader.geo import *
from numpy import array, dot
from transformations import euler_matrix
import random
from physics import *

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
        parser.add_argument("--friction", action="store_true")

    def __init__(self, *args, **kwargs):
        BaseEntity.__init__(self, *args, **kwargs)
        self.rotation_parametrization = rotation_parametrizations[
            self.args.rotation_parametrization]
        self._create_parameter_info_table()
        self._normalized_constrainers = self._create_constrainers()
        self._unnormalized_constrainers = self._create_constrainers()

    def _create_constrainers(self):
        result = []
        if self.experiment.args.friction:
            result.append(FrictionConstrainer(BalanceDetector()))
        if self.experiment.args.floor:
            result.append(FloorConstrainer())
        return result

    def _create_parameter_info_table(self):
        self._parameter_info = []
        root_joint = self.bvh_reader.get_hierarchy().get_root_joint()
        self._extend_parameter_info_table_recurse(root_joint)

    def _extend_parameter_info_table_recurse(self, joint):
        if not joint.has_parent and self.args.translate:
            self._parameter_info.extend(
                [{"category": "translate", "component": "X"},
                 {"category": "translate", "component": "Y"},
                 {"category": "translate", "component": "Z"}])
        if joint.has_rotation and not joint.has_static_rotation:
            for n in range(self.rotation_parametrization.num_parameters):
                self._parameter_info.append({"category": joint.name, "component": str(n)})
        for child in joint.children:
            self._extend_parameter_info_table_recurse(child)

    def parameter_info(self, index):
        return self._parameter_info[index]

    def get_value(self):
        self.bvh_reader.set_skeleton_pose_from_frame(self.skeleton, self._t * self.args.bvh_speed)
        return self._joint_to_parameters(self.skeleton.get_root_joint())

    def get_random_value(self):
        self.bvh_reader.set_skeleton_pose_from_frame(self.skeleton,
            random.uniform(0, self.bvh_reader.get_duration()))
        return self._joint_to_parameters(self.skeleton.get_root_joint())

    def get_duration(self):
        return self.bvh_reader.get_duration() / self.args.bvh_speed

    def _joint_to_parameters(self, root_joint):
        parameters = []
        self._add_joint_parameters_recurse(root_joint, parameters)
        return parameters

    def _add_joint_parameters_recurse(self, joint, parameters):
        if not joint.has_parent and self.args.translate:
            self._add_joint_translation_parameters(joint, parameters)
        if joint.has_rotation and not joint.has_static_rotation:
            self._add_joint_rotation_parameters(joint, parameters)
        for child in joint.children:
            self._add_joint_parameters_recurse(child, parameters)

    def _add_joint_translation_parameters(self, joint, parameters):
        vertex = joint.get_vertex()
        normalized_vector = self.bvh_reader.normalize_vector(vertex)
        weighted_vector = self.args.translation_weight * normalized_vector
        parameters.extend(weighted_vector)

    def _add_joint_rotation_parameters(self, joint, parameters):
        rotation_parameters = self.rotation_parametrization.rotation_to_parameters(
            joint.rotation)
        parameters.extend(rotation_parameters)

    def process_input(self, parameters):
        return self._parameters_to_normalized_vertices(parameters)

    def process_output(self, parameters):
        return self._constrained_output_vertices(parameters)

    def _constrained_output_vertices(self, parameters):
        vertices = self._parameters_to_normalized_vertices(parameters)
        for constrainer in self._normalized_constrainers:
            vertices = constrainer.constrain(vertices)
        return vertices

    def _parameters_to_normalized_vertices(self, parameters):
        self._set_skeleton_pose_from_parameters(parameters)
        root_joint = self.skeleton.get_root_joint()
        vertices = root_joint.get_vertices()
        normalized_vertices = [self.bvh_reader.normalize_vector(vertex)
                               for vertex in vertices]
        return normalized_vertices

    def _set_skeleton_pose_from_parameters(self, parameters):
        self._parameters_to_joint_recurse(parameters, self.skeleton.get_root_joint())

    def _parameters_to_joint_recurse(self, parameters, joint, parameter_index=0):
        if joint.has_parent:
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

        if joint.has_rotation:
            if joint.has_static_rotation:
                rotation_matrix = self._static_rotation_matrix(joint)
            else:
                rotation_parameters = parameters[
                    parameter_index:parameter_index+
                    self.experiment.entity.rotation_parametrization.num_parameters]
                parameter_index += self.experiment.entity.rotation_parametrization.num_parameters
                radians = self.experiment.entity.rotation_parametrization.parameters_to_rotation(
                    rotation_parameters, joint.rotation.axes)
                joint.angles = [math.degrees(r) for r in radians] # possible optimization: only do this when exporting
                rotation_matrix = euler_matrix(*radians, axes=joint.rotation.axes)

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

    def _static_rotation_matrix(self, joint):
        if not hasattr(joint, "static_rotation_matrix"):
            joint.static_rotation_matrix = euler_matrix(*joint.angles, axes=joint.axes)
        return joint.static_rotation_matrix

    def parameters_to_processed_bvh_root(self, parameters):
        self._set_skeleton_pose_from_parameters(parameters)
        root_joint = self.skeleton.get_root_joint()
        vertices = root_joint.get_vertices()
        for constrainer in self._unnormalized_constrainers:
            vertices = constrainer.constrain(vertices)
        return root_joint.recreate_with_vertices(vertices)
