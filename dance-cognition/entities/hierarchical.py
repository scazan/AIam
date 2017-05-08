from experiment import *
from angle_parameters import EulerTo3Vectors, EulerToQuaternion
from numpy import array, dot
from transformations import euler_matrix, quaternion_from_euler, euler_from_quaternion
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
        parser.add_argument("--pose-scale", type=float, default=.5)
        parser.add_argument("--random-slide", type=float)
        parser.add_argument("--circle-slide", action="store_true")
        parser.add_argument("--left-foot")
        parser.add_argument("--left-hand")
        parser.add_argument("--left-forearm")
        parser.add_argument("--left-shoulder")
        parser.add_argument("--left-knee")
        parser.add_argument("--left-hip")
        parser.add_argument("--right-foot")
        parser.add_argument("--right-hand")
        parser.add_argument("--right-forearm")
        parser.add_argument("--right-shoulder")
        parser.add_argument("--right-knee")
        parser.add_argument("--right-hip")
        parser.add_argument("--torso")
        parser.add_argument("--neck")
        parser.add_argument("--head")

    def __init__(self, *args, **kwargs):
        BaseEntity.__init__(self, *args, **kwargs)
        self.rotation_parametrization = rotation_parametrizations[
            self.args.rotation_parametrization]
        self._create_parameter_info_table()
        if self.experiment.args.z_up:
            self._vertical_axis = "z"
            self._coordinate_up = 2
        else:
            self._vertical_axis = "y"
            self._coordinate_up = 1
        self._normalized_constrainers = self._create_constrainers()
        self._unnormalized_constrainers = self._create_constrainers()
        self.modified_root_vertical_orientation = None
        self._last_root_vertical_orientation = None
        if self.args.enable_features:
            self.feature_extractor = FeatureExtractor(self._coordinate_up)

    def _create_constrainers(self):
        result = []
        if self.experiment.args.friction and not self.experiment.args.show_all_feature_matches:
            result.append(FrictionConstrainer(BalanceDetector(self._coordinate_up)))
        if self.experiment.args.floor:
            result.append(FloorConstrainer(self._coordinate_up))
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

    def get_value_length(self):
        return len(self._parameter_info)

    def get_value(self):
        self.bvh_reader.set_pose_from_time(self.pose, self._t * self.args.bvh_speed)
        return self._joint_to_parameters(self.pose.get_root_joint())

    def get_value_from_frame(self, frame):
        self.bvh_reader.set_pose_from_frame(self.pose, frame)
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
        return self._parameters_to_scaled_normalized_vertices(parameters)

    def process_output(self, parameters):
        return self._constrained_output_vertices(parameters)

    def _constrained_output_vertices(self, parameters):
        vertices = self._parameters_to_scaled_normalized_vertices(parameters)
        for constrainer in self._normalized_constrainers:
            vertices = constrainer.constrain(vertices)
        return vertices

    def _parameters_to_scaled_normalized_vertices(self, parameters):
        self._set_pose_from_parameters(parameters)
        root_joint = self.pose.get_root_joint()
        vertices = root_joint.get_vertices()
        normalized_vertices = [
            self.bvh_reader.normalize_vector_without_translation(vertex) * self.args.pose_scale
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
            self.rotation_parametrization.num_parameters]
        parameter_index += self.rotation_parametrization.num_parameters
        radians = self.rotation_parametrization.parameters_to_rotation(
            rotation_parameters, joint.definition.axes)
        if joint.parent is None:
            radians = self._process_root_orientation(joint, radians)
        joint.angles = radians
        return parameter_index

    def _process_root_orientation(self, root_joint, radians):
        return self._process_vertical_axis(radians, root_joint.definition.axes)

    def _process_vertical_axis(self, euler_angles, axes):
        if axes[1] == self._vertical_axis:
            return self._process_vertical_orientation_as_first_axis(euler_angles)
        else:
            if self._vertical_axis == "y":
                axes_with_vertical_first = "ryxz"
            elif self._vertical_axis == "z":
                axes_with_vertical_first = "rzxy"
            euler_angles_vertical_axis_first = euler_from_quaternion(
                quaternion_from_euler(*euler_angles, axes=axes),
                axes=axes_with_vertical_first)
            euler_angles_vertical_axis_first_reoriented = \
                self._process_vertical_orientation_as_first_axis(
                euler_angles_vertical_axis_first)
            return euler_from_quaternion(
                quaternion_from_euler(
                    *euler_angles_vertical_axis_first_reoriented,
                     axes=axes_with_vertical_first),
                axes=axes)

    def _process_vertical_orientation_as_first_axis(self, euler_angles):
        euler_angles = list(euler_angles)
        self._last_root_vertical_orientation = euler_angles[0]
        if self.modified_root_vertical_orientation is not None:
            euler_angles[0] = self.modified_root_vertical_orientation
        return euler_angles

    def get_last_root_vertical_orientation(self):
        return self._last_root_vertical_orientation

    def parameters_to_processed_pose(self, parameters, output_pose):
        self._set_pose_from_parameters(parameters)
        root_joint = self.pose.get_root_joint()
        vertices = root_joint.get_vertices()
        for constrainer in self._unnormalized_constrainers:
            vertices = constrainer.constrain(vertices)
        self.bvh_reader.get_hierarchy().set_pose_vertices(
            output_pose, vertices, not ASSUME_NO_TRANSLATIONAL_OFFSETS_IN_NON_ROOT)

    def extract_features(self, pose):
        positions = [
            pose.get_joint(getattr(self.args, joint_name)).worldpos
            for joint_name in self.feature_extractor.INPUT_JOINTS]
        return self.feature_extractor.extract_features(*positions)
