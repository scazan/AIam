import numpy
from dimensionality_reduction.behavior import Behavior

class Explore(Behavior):
    def __init__(self, student, num_components):
        Behavior.__init__(self)
        normalized_reduction = numpy.array([.5] * num_components)
        self._reduction = student.unnormalize_reduction(normalized_reduction)
