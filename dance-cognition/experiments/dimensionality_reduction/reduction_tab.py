class ReductionTab:
    def __init__(self, parent):
        self._parent = parent
        self.experiment = parent.experiment
            
    def normalized_reduction_value_to_exploration_value(self, n, value):
        range_n = self.experiment.student.reduction_range[n]
        return (value - range_n["explored_min"]) / range_n["explored_range"]

    def exploration_value_to_normalized_reduction_value(self, n, value):
        range_n = self.experiment.student.reduction_range[n]
        return value * range_n["explored_range"] + range_n["explored_min"]
