class ReductionTab:
    def __init__(self, parent):
        self._parent = parent
            
    def normalized_reduction_value_to_exploration_value(self, n, value):
        range_n = self._parent.reduction_range[n]
        return (value - range_n["explored_min"]) / range_n["explored_range"]

    def exploration_value_to_normalized_reduction_value(self, n, value):
        range_n = self._parent.reduction_range[n]
        return value * range_n["explored_range"] + range_n["explored_min"]

    def update_qgl_widgets(self):
        pass
