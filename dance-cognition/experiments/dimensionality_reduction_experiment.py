from experiment import *
from dimensionality_reduction_teacher import *
from dimensionality_reduction import PCA
import random
from leaky_integrator import LeakyIntegrator
from navigator import Navigator, PathFollower
import envelope as envelope_module

class DimensionalityReductionToolbar(ExperimentToolbar):
    def __init__(self, *args):
        ExperimentToolbar.__init__(self, *args)
        self._layout = QtGui.QVBoxLayout()
        self._add_mode_tabs()
        self._set_exploration_ranges()
        self._add_reduction_sliders()
        self.setLayout(self._layout)

    def _add_mode_tabs(self):
        self.tabs = QtGui.QTabWidget()
        self._add_follow_tab()
        self._add_explore_tab()
        self._add_improvise_tab()
        self._layout.addWidget(self.tabs)

        if self.args.improvise:
            self.tabs.setCurrentWidget(self.improvise_tab)
        elif self.args.explore:
            self.tabs.setCurrentWidget(self.explore_tab)
        else:
            self.tabs.setCurrentWidget(self.follow_tab)

    def _add_follow_tab(self):
        self.follow_tab = QtGui.QWidget()
        self._follow_tab_layout = QtGui.QVBoxLayout()
        self._add_velocity_view()
        self._follow_tab_layout.addStretch(1)
        self.follow_tab.setLayout(self._follow_tab_layout)
        self.tabs.addTab(self.follow_tab, "Follow")

    def _add_velocity_view(self):
        layout = QtGui.QHBoxLayout()
        layout.addWidget(QtGui.QLabel("Input velocity: "))
        self.velocity_label = QtGui.QLabel("")
        layout.addWidget(self.velocity_label)
        self._follow_tab_layout.addLayout(layout)

    def _add_explore_tab(self):
        self.explore_tab = QtGui.QWidget()
        self._explore_tab_layout = QtGui.QVBoxLayout()
        self._add_random_button()
        self._add_deviate_button()
        self._explore_tab_layout.addStretch(1)
        self.explore_tab.setLayout(self._explore_tab_layout)
        self.tabs.addTab(self.explore_tab, "Explore")

    def _add_random_button(self):
        button = QtGui.QPushButton("Random", self)
        button.clicked.connect(self._set_random_reduction)
        self._explore_tab_layout.addWidget(button)

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
        self._explore_tab_layout.addLayout(layout)

    def _add_improvise_tab(self):
        self.improvise_tab = QtGui.QWidget()
        self._improvise_tab_layout = QtGui.QVBoxLayout()
        self.add_parameter_fields(
            self.experiment.improviser_params, self._improvise_tab_layout)
        self.improvise_tab.setLayout(self._improvise_tab_layout)
        self.tabs.addTab(self.improvise_tab, "Improvise")

    def _set_random_reduction(self):
        for n in range(self.experiment.student.n_components):
            self._set_random_reduction_n(
                n, self.experiment.student.reduction_range[n])

    def _set_random_reduction_n(self, n, reduction_range):
        self._sliders[n].setValue(self._normalized_reduction_value_to_slider_value(
                n, random.uniform(reduction_range["explored_min"],
                                  reduction_range["explored_max"])))

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
        normalized_reduction = self.experiment.student.normalize_reduction(reduction)
        for n in range(self.experiment.student.n_components):
            self._sliders[n].setValue(self._normalized_reduction_value_to_slider_value(
                    n, normalized_reduction[n]))

    def _set_exploration_ranges(self):
        for n in range(self.experiment.student.n_components):
            self._set_exploration_range(self.experiment.student.reduction_range[n])

    def _set_exploration_range(self, reduction_range):
        reduction_range["explored_range"] = (1.0 + self.args.explore_beyond_observations)
        reduction_range["explored_min"] = .5 - reduction_range["explored_range"]/2
        reduction_range["explored_max"] = .5 + reduction_range["explored_range"]/2

    def _add_reduction_sliders(self):
        group_box = QtGui.QGroupBox("Reduction")
        layout = QtGui.QVBoxLayout()
        self._sliders = []
        for n in range(self.experiment.student.n_components):
            slider = QtGui.QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, SLIDER_PRECISION)
            slider.setSingleStep(1)
            slider.setValue(self._normalized_reduction_value_to_slider_value(n, 0.5))
            layout.addWidget(slider)
            self._sliders.append(slider)
        layout.addStretch(1)
        group_box.setLayout(layout)
        self._layout.addWidget(group_box)

    def refresh(self):
        if self.tabs.currentWidget() != self.explore_tab:
            normalized_reduction = self.experiment.student.normalize_reduction(self.experiment.reduction)
            for n in range(self.experiment.student.n_components):
                self._sliders[n].setValue(
                    self._normalized_reduction_value_to_slider_value(n, normalized_reduction[n]))

    def _normalized_reduction_value_to_slider_value(self, n, value):
        range_n = self.experiment.student.reduction_range[n]
        return int((value - range_n["explored_min"]) / \
            range_n["explored_range"] * SLIDER_PRECISION)

    def _slider_value_to_normalized_reduction_value(self, n, value):
        range_n = self.experiment.student.reduction_range[n]
        return float(value) / SLIDER_PRECISION * range_n["explored_range"] + \
            range_n["explored_min"]

    def get_reduction(self):
        normalized_reduction = numpy.array(
            [self._slider_value_to_normalized_reduction_value(n, self._sliders[n].value())
             for n in range(self.experiment.student.n_components)])
        return self.experiment.student.unnormalize_reduction(normalized_reduction)

class DimensionalityReductionExperiment(Experiment):
    @staticmethod
    def add_parser_arguments(parser):
        Experiment.add_parser_arguments(parser)
        parser.add_argument("--num-components", "-n", type=int, default=4)
        parser.add_argument("--explore-beyond-observations", type=float, default=0.2)
        parser.add_argument("--improvise", action="store_true")
        parser.add_argument("--explore", action="store_true")
        parser.add_argument("--plot-velocity")
        parser.add_argument("--analyze-components", action="store_true")
        parser.add_argument("--training-data-stats", action="store_true")

    def __init__(self, parser):
        self.profiles_dir = "profiles/dimensionality_reduction"
        Experiment.__init__(self, parser)
        self.reduction = None
        self._velocity_integrator = LeakyIntegrator()

    def run(self):
        teacher = Teacher(self.stimulus, self.args.training_data_frame_rate, self.args.profile)
        self._training_data = teacher.get_training_data(self._training_duration())

        if self.args.training_data_stats:
            self._print_training_data_stats()

        if self.args.train:
            self.student = PCA(n_components=self.args.num_components)
            self._train_model()
            save_model(self.student, self._model_path)

        elif self.args.plot_velocity:
            self.student = load_model(self._model_path)
            self._plot_velocity()

        elif self.args.analyze_components:
            self.student = load_model(self._model_path)
            self._analyze_components()

        else:
            self.student = load_model(self._model_path)
            self.navigator = Navigator(map_points=self.student.normalized_observed_reductions)
            self.improviser_params = ImproviserParameters()
            self._improviser = Improviser(self, self.improviser_params)

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

    def _print_training_data_stats(self):
        format = "%-5s%-20s%-8s%-8s%-8s%-8s"
        print format % ("n", "descr", "min", "max", "mean", "var")
        for n in range(len(self._training_data[0])):
            parameter_info = self.stimulus.parameter_info(n)
            col = self._training_data[:,n]
            stats = ["%.2f" % v for v in [min(col), max(col), numpy.mean(col), numpy.var(col)]]
            print format % (
                n, "%s %s" % (parameter_info["category"], parameter_info["component"]),
                stats[0],
                stats[1],
                stats[2],
                stats[3])

    def proceed(self):
        if self.window.toolbar.tabs.currentWidget() == self.window.toolbar.explore_tab:
            self.reduction = self.window.toolbar.get_reduction()
        elif self.window.toolbar.tabs.currentWidget() == self.window.toolbar.follow_tab:
            self._follow()
            if hasattr(self, "_velocity"):
                self.window.toolbar.velocity_label.setText("%.3f" % self._velocity)
        elif self.window.toolbar.tabs.currentWidget() == self.window.toolbar.improvise_tab:
            self._improviser.proceed(self.time_increment)
            self.reduction = self._improviser.current_position()
        self.output = self.student.inverse_transform(numpy.array([self.reduction]))[0]

    def _follow(self):
        self.stimulus.proceed(self.time_increment)
        self.input = self.stimulus.get_value()
        next_reduction = self.student.transform(numpy.array([self.input]))[0]
        if self.reduction is not None:
            self._measure_velocity(
                self.student.normalize_reduction(self.reduction),
                self.student.normalize_reduction(next_reduction))
        self.reduction = next_reduction

    def _measure_velocity(self, r1, r2):
        distance = numpy.linalg.norm(r1 - r2)
        self._velocity_integrator.integrate(
            distance / self.time_increment, self.time_increment)
        self._velocity = self._velocity_integrator.value()

    def _plot_velocity(self):
        f = open(self.args.plot_velocity, "w")
        t = 0
        self.time_increment = 1.0 / self.args.frame_rate
        self._follow()
        while t < self.stimulus.get_duration():
            self._follow()
            print >>f, self._velocity
            t += self.time_increment
        f.close()

    def _analyze_components(self):
        for n in range(self.student.n_components):
            self._analyze_component(n)

    def _analyze_component(self, n, resolution=10, group_by_parameter_category=True):
        print "component %s:" % n

        num_output_components = len(self.stimulus.get_value())
        output_components = []
        for output_component_index in range(num_output_components):
            parameter_info = self.stimulus.parameter_info(output_component_index)
            output_components.append({"parameter_category": parameter_info["category"],
                                      "parameter_components": [parameter_info["component"]],
                                      "variance": 0.})

        for normalized_reduction in self.student.normalized_observed_reductions:
            reconstructions = []
            for x in numpy.arange(0., 1., 1./resolution):
                normalized_reduction[n] = x
                reduction = self.student.unnormalize_reduction(normalized_reduction)
                reconstruction = self.student.inverse_transform(reduction)[0]
                reconstructions.append(reconstruction)
            reconstructions = numpy.array(reconstructions)

            for output_component_index in range(num_output_components):
                variance = numpy.var(reconstructions[:,output_component_index])
                output_components[output_component_index]["variance"] += variance

        if group_by_parameter_category:
            output_components = self._group_components_by_category(output_components)
        output_components_sorted_by_variance = sorted(
            output_components,
            key=lambda output_component: -output_component["variance"])
        for i in range(10):
            output_component = output_components_sorted_by_variance[i]
            print "  %s [%s] (%s)" % (
                output_component["parameter_category"],
                ",".join(output_component["parameter_components"]),
                output_component["variance"])

    def _group_components_by_category(self, components):
        result = []
        for component in components:
            self._add_component_to_result(component, result)
        return result

    def _add_component_to_result(self, component, result):
        for other in result:
            if other["parameter_category"] == component["parameter_category"]:
                other["parameter_components"].extend(component["parameter_components"])
                other["variance"] += component["variance"]
                return result
        result.append(component)
        return result

class ImproviserParameters(Parameters):
    def __init__(self):
        Parameters.__init__(self)
        self.add_parameter("novelty", type=float, default=0,
                           choices=ParameterFloatRange(0., 1.))
        self.add_parameter("num_segments", type=int, default=10)
        self.add_parameter("resolution", type=int, default=100)
        self.add_parameter("velocity", type=float, default=.5)
        self.add_parameter("min_relative_velocity", type=float, default=.3,
                           choices=ParameterFloatRange(.001, 1.))
        self.add_parameter("envelope", choices=["constant", "sine", "exponential"], default="sine")

class Improviser:
    def __init__(self, experiment, params):
        self.experiment = experiment
        self.params = params
        self._path_follower = None

    def _select_next_move(self):
        path_segments = self._generate_path()
        path = self._interpolate_path(path_segments)
        self._path_follower = self._create_path_follower(path)

    def _generate_path(self):
        return self.experiment.navigator.generate_path(
            departure=self._departure(),
            destination=self._select_destination(),
            num_segments=self.params.num_segments,
            novelty=self.params.novelty)

    def _departure(self):
        if self.experiment.reduction is None:
            unnormalized_departure = self.experiment.student.transform(numpy.array([
                        self.experiment.stimulus.get_value()]))[0]
        else:
            unnormalized_departure = self.experiment.reduction
        return self.experiment.student.normalize_reduction(unnormalized_departure)

    def _select_destination(self):
        return self.experiment.navigator.select_destination(novelty=self.params.novelty)

    def _interpolate_path(self, path_segments):
        return self.experiment.navigator.interpolate_path(
            path_segments,
            resolution=self.params.resolution)

    def _create_path_follower(self, path):
        envelope_class = getattr(envelope_module, "%s_envelope" % self.params.envelope)
        envelope = envelope_class(min_relative_velocity=self.params.min_relative_velocity)
        return PathFollower(path, self.params.velocity, envelope)

    def proceed(self, time_increment):
        if self._path_follower is None:
            self._select_next_move()
        if self._path_follower.reached_destination():
            self._select_next_move()
        self._path_follower.proceed(time_increment)

    def current_position(self):
        normalized_position = self._path_follower.current_position()
        return self.experiment.student.unnormalize_reduction(normalized_position)
