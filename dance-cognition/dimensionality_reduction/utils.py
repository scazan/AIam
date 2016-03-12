import numpy

class PositionComparison:
    def __init__(self, source, target):
        self._vector_towards_target = target - source
        self._distance_to_target = numpy.linalg.norm(self._vector_towards_target)
        if self._distance_to_target > 0:
            self._direction_as_unit_vector = self._vector_towards_target / self._distance_to_target

    def get_distance_to_target(self):
        return self._distance_to_target

    def get_direction_as_unit_vector(self):
        return self._direction_as_unit_vector
