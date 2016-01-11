import numpy

class FeatureExtractor:
    FEATURES = ["left_hand_elevation"]

    def get_num_features(self):
        return len(self.FEATURES)

    def extract_features(self,
                         left_hand_position,
                         left_forearm_position,
                         left_shoulder_position,
                         neck_position):
        left_arm_length = \
            self._distance(left_hand_position, left_forearm_position) + \
            self._distance(left_forearm_position, left_shoulder_position) + \
            self._distance(left_shoulder_position, neck_position)
        return [self._get_hand_elevation(left_hand_position, neck_position, left_arm_length)]

    def _get_hand_elevation(self, hand_position, neck_position, arm_length):
        hand_y = hand_position[1]
        neck_y = neck_position[1]
        return ((hand_y - neck_y) / arm_length + 1) / 2

    def _distance(self, p1, p2):
        return numpy.linalg.norm(p1 - p2)
