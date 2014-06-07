from experiment import *

class ReductionSliders(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self)
        self._parent = parent
        self.experiment = parent.experiment
        self._set_exploration_ranges()
        self._layout = QtGui.QVBoxLayout()
        self._add_sliders()
        self._layout.addStretch(1)
        self.setLayout(self._layout)

    def slider(self, n):
        return self._sliders[n]

    def reduction_changed(self, normalized_reduction):
        self._update_sliders(normalized_reduction)

    def _update_sliders(self, normalized_reduction):
        for n in range(self.experiment.student.n_components):
            self._sliders[n].setValue(self._normalized_reduction_value_to_slider_value(
                    n, normalized_reduction[n]))

    def _set_exploration_ranges(self):
        for n in range(self.experiment.student.n_components):
            self._set_exploration_range(self.experiment.student.reduction_range[n])

    def _set_exploration_range(self, reduction_range):
        reduction_range["explored_range"] = (1.0 + self.experiment.args.explore_beyond_observations)
        reduction_range["explored_min"] = .5 - reduction_range["explored_range"]/2
        reduction_range["explored_max"] = .5 + reduction_range["explored_range"]/2

    def _add_sliders(self):
        self._sliders = []
        for n in range(self.experiment.student.n_components):
            slider = QtGui.QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, SLIDER_PRECISION)
            slider.setSingleStep(1)
            slider.setValue(self._normalized_reduction_value_to_slider_value(n, 0.5))
            slider.sliderReleased.connect(
                lambda: self._parent.reduction_changed_interactively(self))
            self._layout.addWidget(slider)
            self._sliders.append(slider)

    def set_enabled(self, enabled):
        for slider in self._sliders:
            slider.setEnabled(enabled)
            
    def _normalized_reduction_value_to_slider_value(self, n, value):
        range_n = self.experiment.student.reduction_range[n]
        return int((value - range_n["explored_min"]) / \
            range_n["explored_range"] * SLIDER_PRECISION)

    def _slider_value_to_normalized_reduction_value(self, n, value):
        range_n = self.experiment.student.reduction_range[n]
        return float(value) / SLIDER_PRECISION * range_n["explored_range"] + \
            range_n["explored_min"]

    def get_normalized_reduction(self):
        normalized_reduction = numpy.array(
            [self._slider_value_to_normalized_reduction_value(n, self._sliders[n].value())
             for n in range(self.experiment.student.n_components)])
        return normalized_reduction
