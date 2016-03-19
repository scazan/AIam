import numpy

class FeatureExtractor:
    FEATURES = ["left_hand_elevation",
                "right_hand_elevation",
                "head_elevation",
                "knee_distance"]
    INPUT_JOINTS = [
        "left_hand",
        "left_forearm",
        "left_shoulder",
        "left_knee",
        "left_hip",
        "right_hand",
        "right_forearm",
        "right_shoulder",
        "right_knee",
        "right_hip",
        "torso",
        "neck",
        "head"]

    def __init__(self, coordinate_up=1):
        self._coordinate_up = 1

    def get_num_features(self):
        return len(self.FEATURES)

    def extract_features(self,
                         left_hand_position,
                         left_forearm_position,
                         left_shoulder_position,
                         left_knee_position,
                         left_hip_position,
                         right_hand_position,
                         right_forearm_position,
                         right_shoulder_position,
                         right_knee_position,
                         right_hip_position,
                         torso_position,
                         neck_position,
                         head_position):
        left_arm_length = self._get_total_distance(
            [left_hand_position, left_forearm_position, left_shoulder_position, neck_position])
        left_hand_elevation = self._get_elevation(
            left_hand_position, neck_position, left_arm_length)

        right_arm_length = self._get_total_distance(
            [right_hand_position, right_forearm_position, right_shoulder_position, neck_position])
        right_hand_elevation = self._get_elevation(
            right_hand_position, neck_position, right_arm_length)

        torso_head_distance = self._get_total_distance(
            [torso_position, neck_position, head_position])
        head_elevation = self._get_elevation(
            torso_position, head_position, torso_head_distance)

        max_knee_distance = self._get_total_distance(
            [left_knee_position, left_hip_position, right_hip_position, right_knee_position])
        knee_distance = self._distance(left_knee_position, right_knee_position)
        relative_knee_distance = knee_distance / max_knee_distance

        return [
            left_hand_elevation,
            right_hand_elevation,
            head_elevation,
            relative_knee_distance]

    def _get_total_distance(self, positions):
        return sum([self._distance(positions[i], positions[i+1])
                    for i in range(len(positions)-1)])

    def _get_elevation(self, start_position, end_position, total_distance):
        start_up = start_position[self._coordinate_up]
        end_up = end_position[self._coordinate_up]
        return ((start_up - end_up) / total_distance + 1) / 2

    def _distance(self, p1, p2):
        return numpy.linalg.norm(p1 - p2)
