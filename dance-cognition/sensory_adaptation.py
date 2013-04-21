from vector import *

class SensoryAdapter:
    def __init__(self):
        self._sensed_center = Vector3d(0.0, 0.0, 0.0)

    def process(self, position, time_increment):
        output = position - self._sensed_center
        factor = 0.1 * time_increment / max(output.mag(), 0.0001)
        self._sensed_center += output * min(factor, 1.0)
        return output
