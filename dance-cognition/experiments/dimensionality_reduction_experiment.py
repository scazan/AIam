from experiment import *
from dimensionality_reduction_teacher import *
import random
from leaky_integrator import LeakyIntegrator
from navigator import Navigator, PathFollower

SLIDER_PRECISION = 1000

class DimensionalityReductionToolbar(ExperimentToolbar):
    def __init__(self, *args):
        ExperimentToolbar.__init__(self, *args)
        self._layout = QtGui.QVBoxLayout()
        self._add_buttons()
        self._set_exploration_ranges()
        self._add_velocity_view()
        self._add_reduction_sliders()
        self.setLayout(self._layout)

    def _add_buttons(self):
        self._add_mode_buttons()
        self._add_random_button()
        self._add_deviate_button()

    def _add_mode_buttons(self):
        layout = QtGui.QVBoxLayout()

        self.follow_button = QtGui.QRadioButton("Follow", self)
        layout.addWidget(self.follow_button)

        self.improvise_button = QtGui.QRadioButton("Improvise", self)
        layout.addWidget(self.improvise_button)

        self.explore_button = QtGui.QRadioButton("Explore interactively", self)
        layout.addWidget(self.explore_button)

        if self.args.improvise:
            self.improvise_button.setChecked(True)
        else:
            self.follow_button.setChecked(True)

        self._layout.addLayout(layout)

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
        self.deviation_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.deviation_slider.setRange(0, SLIDER_PRECISION)
        self.deviation_slider.setSingleStep(1)
        self.deviation_slider.setValue(0.0)
        layout.addWidget(self.deviation_slider)
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
        max_deviation = float(self.deviation_slider.value()) / SLIDER_PRECISION \
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

    def _add_reduction_sliders(self):
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

    def refresh(self):
        if not self.explore_button.isChecked():
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

    def _add_velocity_view(self):
        self.velocity_label = QtGui.QLabel("")
        self._layout.addWidget(self.velocity_label)

class DimensionalityReductionExperiment(Experiment):
    @staticmethod
    def add_parser_arguments(parser):
        Experiment.add_parser_arguments(parser)
        parser.add_argument("--num-components", "-n", type=int, default=4)
        parser.add_argument("--explore-beyond-observations", type=float, default=0.2)
        parser.add_argument("--improvise", action="store_true")

    def __init__(self, parser):
        Experiment.__init__(self, parser)
        if self.args.model is None:
            self.args.model = "models/dimensionality_reduction/%s.model" % self.args.entity
        self.reduction = None
        self._velocity_integrator = LeakyIntegrator()

    def run(self, student):
        self.student = student
        teacher = Teacher(self.stimulus, self.args.training_data_frame_rate)
        self._training_data = teacher.get_training_data(self._training_duration())

        if self.args.train:
            self._train_model()
            self.save_model(self.args.model)

        else:
            self.student = self.load_model(self.args.model)
            self._improviser = None
            self._navigator = Navigator(map_points=self.student.observed_reductions)

            app = QtGui.QApplication(sys.argv)
            app.setStyleSheet(open("stylesheet.qss").read())
            self.window = MainWindow(
                self, self._scene_class, DimensionalityReductionToolbar, self.args)
            self.window.show()
            app.exec_()

    def _train_model(self):
        print "training model..."
        self.student.fit(self._training_data)
        print "ok"

        print "probing model..."
        self.student.probe(self._training_data)
        print "ok"

    def proceed(self):
        if self.window.toolbar.explore_button.isChecked():
            self.reduction = self.window.toolbar.get_reduction()
        elif self.window.toolbar.follow_button.isChecked():
            self._follow()
        elif self.window.toolbar.improvise_button.isChecked():
            if self._improviser is None or self._improviser.reached_destination():
                self._start_improvisation()
            self._improviser.proceed(self.time_increment)
            self.reduction = self._improviser.current_position()
        self.output = self.student.inverse_transform(numpy.array([self.reduction]))[0]

    def _follow(self):
        self.stimulus.proceed(self.time_increment)
        self.input = self.stimulus.get_value()
        next_reduction = self.student.transform(numpy.array([self.input]))[0]
        if self.reduction is not None:
            self._measure_velocity(self.reduction, next_reduction)
        self.reduction = next_reduction

    def _measure_velocity(self, r1, r2):
        distance = numpy.linalg.norm(r1 - r2)
        self._velocity_integrator.integrate(
            distance / self.time_increment, self.time_increment)
        self.window.toolbar.velocity_label.setText("%.1f" %
            self._velocity_integrator.value())

    def _start_improvisation(self):
        if self.reduction is None:
            departure = self.student.transform(numpy.array([
                        self.stimulus.get_value()]))[0]
        else:
            departure = self.reduction
        path = self._navigator.generate_path(
            departure=departure,
            destination=random.choice(self.student.observed_reductions),
            num_segments=100)
        self._improviser = PathFollower(path, duration=5.0)
