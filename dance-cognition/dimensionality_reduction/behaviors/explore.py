import numpy

class Explore:
    def __init__(self, experiment):
        self._experiment = experiment
        normalized_reduction = numpy.array([.5] * experiment.args.num_components)
        self._reduction = self._experiment.student.unnormalize_reduction(normalized_reduction)

    def get_reduction(self):
        return self._reduction

    def set_reduction(self, reduction):
        self._reduction = reduction
