from vector import *

class SensoryAdapter:
    def __init__(self, adaptation_factor):
        self._adaptation_factor = adaptation_factor
        self._sensed_center = Vector3d(0.0, 0.0, 0.0)

    def process(self, position, time_increment):
        output = position - self._sensed_center
        factor = self._adaptation_factor * time_increment / max(output.mag(), 0.0001)
        self._sensed_center += output * min(factor, 1.0)
        return output
