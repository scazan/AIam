import numpy

class FeatureExtractor:
    FEATURES = ["left_hand_elevation",
                "right_hand_elevation"]
    INPUT_JOINTS = [
        "left_hand",
        "left_forearm",
        "left_shoulder",
        "right_hand",
        "right_forearm",
        "right_shoulder",
        "neck"]

    def get_num_features(self):
        return len(self.FEATURES)

    def extract_features(self,
                         left_hand_position,
                         left_forearm_position,
                         left_shoulder_position,
                         right_hand_position,
                         right_forearm_position,
                         right_shoulder_position,
                         neck_position):
        left_arm_length = self._get_arm_length(
            left_hand_position, left_forearm_position, left_shoulder_position, neck_position)
        left_hand_elevation = self._get_hand_elevation(
            left_hand_position, neck_position, left_arm_length)
        right_arm_length = self._get_arm_length(
            right_hand_position, right_forearm_position, right_shoulder_position, neck_position)
        right_hand_elevation = self._get_hand_elevation(
            right_hand_position, neck_position, right_arm_length)
        return [left_hand_elevation, right_hand_elevation]

    def _get_arm_length(self, hand_position, forearm_position, shoulder_position, neck_position):
        return  self._distance(hand_position, forearm_position) + \
            self._distance(forearm_position, shoulder_position) + \
            self._distance(shoulder_position, neck_position)

    def _get_hand_elevation(self, hand_position, neck_position, arm_length):
        hand_y = hand_position[1]
        neck_y = neck_position[1]
        return ((hand_y - neck_y) / arm_length + 1) / 2

    def _distance(self, p1, p2):
        return numpy.linalg.norm(p1 - p2)
