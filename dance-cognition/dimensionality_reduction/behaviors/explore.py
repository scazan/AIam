import numpy
from dimensionality_reduction.behavior import Behavior

class Explore(Behavior):
    def __init__(self, experiment):
        self._experiment = experiment
        normalized_reduction = numpy.array([.5] * experiment.args.num_components)
        self._reduction = self._experiment.student.unnormalize_reduction(normalized_reduction)
