from experiment import *
from angle_parameters import EulerTo3Vectors, EulerToQuaternion
from numpy import array, dot
from transformations import euler_matrix
import random
from physics import *
from feature_extraction import FeatureExtractor

ASSUME_NO_TRANSLATIONAL_OFFSETS_IN_NON_ROOT = True

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
        parser.add_argument("--random-slide", type=float)
        parser.add_argument("--circle-slide", action="store_true")
        parser.add_argument("--left-hand")
        parser.add_argument("--left-forearm")
        parser.add_argument("--left-shoulder")
        parser.add_argument("--neck")

    def __init__(self, *args, **kwargs):
        BaseEntity.__init__(self, *args, **kwargs)
        self.rotation_parametrization = rotation_parametrizations[
            self.args.rotation_parametrization]
        self._create_parameter_info_table()
        self._normalized_constrainers = self._create_constrainers()
        self._unnormalized_constrainers = self._create_constrainers()
        if self.args.enable_features:
            self.feature_extractor = FeatureExtractor()

    def _create_constrainers(self):
        if self.experiment.args.z_up:
            coordinate_up = 2
        else:
            coordinate_up = 1
        result = []
        if self.experiment.args.friction:
            result.append(FrictionConstrainer(BalanceDetector(coordinate_up)))
        if self.experiment.args.floor:
            result.append(FloorConstrainer(coordinate_up))
        if self.experiment.args.random_slide > 0:
            result.append(RandomSlide(self.experiment.args.random_slide))
        if self.experiment.args.circle_slide:
            result.append(CircleSlide())
        return result

    def _create_parameter_info_table(self):
        self._parameter_info = []
        root_joint_definition = self.bvh_reader.get_hierarchy().get_root_joint_definition()
        self._extend_parameter_info_table_recurse(root_joint_definition)

    def _extend_parameter_info_table_recurse(self, joint_definition):
        if not joint_definition.has_parent and self.args.translate:
            self._parameter_info.extend(
                [{"category": "translate", "component": "X"},
                 {"category": "translate", "component": "Y"},
                 {"category": "translate", "component": "Z"}])
        if joint_definition.has_rotation and not joint_definition.has_static_rotation:
            for n in range(self.rotation_parametrization.num_parameters):
                self._parameter_info.append({"category": joint_definition.name, "component": str(n)})
        for child_definition in joint_definition.child_definitions:
            self._extend_parameter_info_table_recurse(child_definition)

    def parameter_info(self, index):
        return self._parameter_info[index]

    def get_value(self):
        self.bvh_reader.set_pose_from_time(self.pose, self._t * self.args.bvh_speed)
        return self._joint_to_parameters(self.pose.get_root_joint())

    def get_random_value(self):
        self.bvh_reader.set_pose_from_time(self.pose,
            random.uniform(0, self.bvh_reader.get_duration()))
        return self._joint_to_parameters(self.pose.get_root_joint())

    def get_duration(self):
        return self.bvh_reader.get_duration() / self.args.bvh_speed

    def _joint_to_parameters(self, root_joint):
        parameters = []
        self._add_joint_parameters_recurse(root_joint, parameters)
        return parameters

    def _add_joint_parameters_recurse(self, joint, parameters):
        if not joint.definition.has_parent and self.args.translate:
            self._add_joint_translation_parameters(joint, parameters)
        if joint.definition.has_rotation and not joint.definition.has_static_rotation:
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
        self._set_pose_from_parameters(parameters)
        root_joint = self.pose.get_root_joint()
        vertices = root_joint.get_vertices()
        normalized_vertices = [self.bvh_reader.normalize_vector(vertex)
                               for vertex in vertices]
        return normalized_vertices

    def _set_pose_from_parameters(self, parameters):
        self._parameters_to_joint_recurse(parameters, self.pose.get_root_joint())
        self.bvh_reader.get_hierarchy().update_pose_world_positions(self.pose)

    def _parameters_to_joint_recurse(self, parameters, joint, parameter_index=0):
        if not joint.definition.has_parent and self.args.translate:
            parameter_index = self._parameters_to_joint_translation(parameters, joint, parameter_index)

        if joint.definition.has_rotation and not joint.definition.has_static_rotation:
            parameter_index = self._parameters_to_joint_rotation(parameters, joint, parameter_index)

        for child in joint.children:
            parameter_index = self._parameters_to_joint_recurse(parameters, child, parameter_index)

        return parameter_index

    def _parameters_to_joint_translation(self, parameters, joint, parameter_index):
        weighted_vector = parameters[parameter_index:parameter_index+3]
        parameter_index += 3
        normalized_vector = numpy.array(weighted_vector) / self.args.translation_weight
        joint.translation = self.bvh_reader.skeleton_scale_vector(normalized_vector)
        return parameter_index

    def _parameters_to_joint_rotation(self, parameters, joint, parameter_index):
        rotation_parameters = parameters[
            parameter_index:parameter_index+
            self.experiment.entity.rotation_parametrization.num_parameters]
        parameter_index += self.experiment.entity.rotation_parametrization.num_parameters
        radians = self.experiment.entity.rotation_parametrization.parameters_to_rotation(
            rotation_parameters, joint.definition.axes)
        joint.angles = radians
        return parameter_index

    def parameters_to_processed_pose(self, parameters, output_pose):
        self._set_pose_from_parameters(parameters)
        root_joint = self.pose.get_root_joint()
        vertices = root_joint.get_vertices()
        for constrainer in self._unnormalized_constrainers:
            vertices = constrainer.constrain(vertices)
        self.bvh_reader.get_hierarchy().set_pose_vertices(
            output_pose, vertices, not ASSUME_NO_TRANSLATIONAL_OFFSETS_IN_NON_ROOT)

    def extract_features(self, pose):
        left_hand_position = pose.get_joint(self.args.left_hand).worldpos
        left_forearm_position = pose.get_joint(self.args.left_forearm).worldpos
        left_shoulder_position = pose.get_joint(self.args.left_shoulder).worldpos
        neck_position = pose.get_joint(self.args.neck).worldpos
        return self.feature_extractor.extract_features(
            left_hand_position,
            left_forearm_position,
            left_shoulder_position,
            neck_position)
