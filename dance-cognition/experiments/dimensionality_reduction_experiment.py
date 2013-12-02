from experiment import *
from dimensionality_reduction_teacher import *
import random

SLIDER_PRECISION = 1000

class DimensionalityReductionToolbar(ExperimentToolbar):
    def __init__(self, *args):
        ExperimentToolbar.__init__(self, *args)
        self._layout = QtGui.QVBoxLayout()
        self._add_buttons()
        self._set_exploration_ranges()
        self._add_sliders()
        self.setLayout(self._layout)

    def _add_buttons(self):
        self._add_interactive_control_button()
        self._add_random_button()
        self._add_deviate_button()

    def _add_interactive_control_button(self):
        button = QtGui.QCheckBox("Explore interactively", self)
        button.stateChanged.connect(self._changed_interactive_control)
        self._layout.addWidget(button)

    def _add_random_button(self):
        button = QtGui.QPushButton("Random", self)
        button.clicked.connect(self._set_random_reduction)
        self._layout.addWidget(button)

    def _set_random_reduction(self):
        for n in range(self.experiment.student.n_components):
            self._set_random_reduction_n(
                n, self.experiment.student.reduction_range[n])

    def _set_random_reduction_n(self, n, reduction_range):
        self._sliders[n].setValue(self._reduction_value_to_slider_value(
                n, random.uniform(reduction_range["explored_min"],
                                  reduction_range["explored_max"])))

    def _add_deviate_button(self):
        layout = QtGui.QHBoxLayout()
        self._deviation_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self._deviation_slider.setRange(0, SLIDER_PRECISION)
        self._deviation_slider.setSingleStep(1)
        self._deviation_slider.setValue(0.0)
        layout.addWidget(self._deviation_slider)
        button = QtGui.QPushButton("Deviate", self)
        button.clicked.connect(self._set_deviated_reduction)
        layout.addWidget(button)
        self._layout.addLayout(layout)

    def _set_deviated_reduction(self):
        random_observation = self.experiment.stimulus.get_random_value()
        undeviated_reduction = self.experiment.student.transform(numpy.array([
                    random_observation]))[0]
        deviated_reduction = undeviated_reduction + self._random_deviation()
        self._set_reduction(deviated_reduction)

    def _random_deviation(self):
        return [self._random_deviation_n(n)
                for n in range(self.experiment.student.n_components)]
    
    def _random_deviation_n(self, n):
        reduction_range = self.experiment.student.reduction_range[n]
        max_deviation = float(self._deviation_slider.value()) / SLIDER_PRECISION \
            * (reduction_range["max"] - reduction_range["min"])
        return random.uniform(-max_deviation, max_deviation)

    def _set_reduction(self, reduction):
        for n in range(self.experiment.student.n_components):
            self._sliders[n].setValue(self._reduction_value_to_slider_value(
                    n, reduction[n]))

    def _set_exploration_ranges(self):
        for n in range(self.experiment.student.n_components):
            self._set_exploration_range(self.experiment.student.reduction_range[n])

    def _set_exploration_range(self, reduction_range):
        center = (reduction_range["min"] + reduction_range["max"]) / 2
        reduction_range["explored_range"] = \
            (reduction_range["max"] - reduction_range["min"]) \
            * (1.0 + self.args.explore_beyond_observations)
        reduction_range["explored_min"] = \
            center - reduction_range["explored_range"]/2
        reduction_range["explored_max"] = \
            center + reduction_range["explored_range"]/2

    def _add_sliders(self):
        group_box = QtGui.QGroupBox("Reduction")
        layout = QtGui.QVBoxLayout()
        self._sliders = []
        for n in range(self.experiment.student.n_components):
            slider = QtGui.QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, SLIDER_PRECISION)
            slider.setSingleStep(1)
            slider.setValue(self._reduction_value_to_slider_value(n, 0.5))
            layout.addWidget(slider)
            self._sliders.append(slider)
        layout.addStretch(1)
        group_box.setLayout(layout)
        self._layout.addWidget(group_box)

    def _changed_interactive_control(self, state):
        self.experiment.interactive_control = (state == QtCore.Qt.Checked)

    def refresh(self):
        if not self.experiment.interactive_control:
            for n in range(self.experiment.student.n_components):
                self._sliders[n].setValue(
                    self._reduction_value_to_slider_value(n, self.experiment.reduction[n]))

    def _reduction_value_to_slider_value(self, n, value):
        range_n = self.experiment.student.reduction_range[n]
        return int((value - range_n["explored_min"]) / \
            range_n["explored_range"] * SLIDER_PRECISION)

    def _slider_value_to_reduction_value(self, n, value):
        range_n = self.experiment.student.reduction_range[n]
        return float(value) / SLIDER_PRECISION * range_n["explored_range"] + \
            range_n["explored_min"]

    def get_reduction(self):
        return numpy.array(
            [self._slider_value_to_reduction_value(n, self._sliders[n].value())
             for n in range(self.experiment.student.n_components)])


class DimensionalityReductionExperiment(Experiment):
    @staticmethod
    def add_parser_arguments(parser):
        Experiment.add_parser_arguments(parser)
        parser.add_argument("--num-components", "-n", type=int, default=4)
        parser.add_argument("--explore-beyond-observations", type=float, default=0.2)

    def __init__(self, parser):
        Experiment.__init__(self, parser)
        if self.args.model is None:
            self.args.model = "models/dimensionality_reduction/%s.model" % self.args.entity
        self.reduction = None
        self.interactive_control = False

    def run(self, student):
        self.student = student

        if self.args.train:
            teacher = Teacher(self.stimulus, self.args.training_data_frame_rate)
            self._train_model(teacher)
            self.save_model(self.args.model)

        else:
            self.student = self.load_model(self.args.model)

            app = QtGui.QApplication(sys.argv)
            app.setStyleSheet(open("stylesheet.qss").read())
            self.window = MainWindow(
                self, self._scene_class, DimensionalityReductionToolbar, self.args)
            self.window.show()
            app.exec_()

    def _train_model(self, teacher):
        training_data = teacher.get_training_data(self._training_duration())

        print "training model..."
        self.student.fit(training_data)
        print "ok"

        print "probing model..."
        self.student.probe(training_data)
        print "ok"

    def proceed(self, time_increment):
        if self.interactive_control:
            self.reduction = self.window.toolbar.get_reduction()
        else:
            self.stimulus.proceed(time_increment)
            self.input = self.stimulus.get_value()
            self.reduction = self.student.transform(numpy.array([self.input]))[0]
        self.output = self.student.inverse_transform(numpy.array([self.reduction]))[0]
