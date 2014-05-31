from experiment import *
from dimensionality_reduction_teacher import *
from component_analysis import ComponentAnalysis
import pca
import random
from leaky_integrator import LeakyIntegrator
from navigator import Navigator, PathFollower
import envelope as envelope_module

REDUCTION_PLOT_PATH = "reduction.dat"

class DimensionalityReductionMainWindow(MainWindow):
    def __init__(self, *args, **kwargs):
        MainWindow.__init__(self, *args, **kwargs)
        self._add_toggleable_action(
            '&Plot reduction', self.experiment.start_plot_reduction,
            '&Stop plot', self.experiment.stop_plot_reduction,
            False, 'F1')

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
        if hasattr(self.experiment.entity, "get_duration"):
            self._add_cursor_slider()
        self._add_velocity_view()
        self._follow_tab_layout.addStretch(1)
        self.follow_tab.setLayout(self._follow_tab_layout)
        self.tabs.addTab(self.follow_tab, "Follow")

    def _add_cursor_slider(self):
        self.cursor_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.cursor_slider.setRange(0, SLIDER_PRECISION)
        self.cursor_slider.setSingleStep(1)
        self.cursor_slider.setValue(0.0)
        self.cursor_slider.valueChanged.connect(self.experiment.cursor_changed)
        self._follow_tab_layout.addWidget(self.cursor_slider)

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
        random_observation = self.experiment.entity.get_random_value()
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
        parser.add_argument("--pca-type",
                            choices=["LinearPCA", "KernelPCA"],
                            default="LinearPCA")
        parser.add_argument("--num-components", "-n", type=int, default=4)
        parser.add_argument("--explore-beyond-observations", type=float, default=0.2)
        parser.add_argument("--improvise", action="store_true")
        parser.add_argument("--explore", action="store_true")
        parser.add_argument("--plot-velocity")
        parser.add_argument("--analyze-components", action="store_true")
        parser.add_argument("--analyze-accuracy", action="store_true")
        parser.add_argument("--training-data-stats", action="store_true")
        parser.add_argument("--export-stills")

    def __init__(self, parser):
        self.profiles_dir = "profiles/dimensionality_reduction"
        Experiment.__init__(self, parser)
        self.reduction = None
        self._velocity_integrator = LeakyIntegrator()
        self._reduction_plot = None

    def run(self):
        teacher = Teacher(self.entity, self.args.training_data_frame_rate)

        if self.args.training_data_stats:
            self._training_data = load_training_data(self._training_data_path)
            self._print_training_data_stats()

        if self.args.train:
            pca_class = getattr(pca, self.args.pca_type)
            self.student = pca_class(n_components=self.args.num_components)
            self._training_data = teacher.create_training_data(self._training_duration())
            self._train_model()
            save_model([self.student, self.entity.model], self._model_path)
            save_training_data(self._training_data, self._training_data_path)

        elif self.args.plot_velocity:
            self._load_model()
            self._plot_velocity()

        elif self.args.analyze_components:
            self._load_model()
            ComponentAnalysis(
                pca=self.student,
                num_output_components=len(self.entity.get_value()),
                parameter_info_getter=self.entity.parameter_info).analyze()

        elif self.args.analyze_accuracy:
            self._load_model()
            self._training_data = load_training_data(self._training_data_path)
            self.student.analyze_accuracy(self._training_data)

        elif self.args.export_stills:
            self._load_model()
            app = QtGui.QApplication(sys.argv)
            self.improviser_params = ImproviserParameters()
            self.window = DimensionalityReductionMainWindow(
                self, self._scene_class, DimensionalityReductionToolbar, self.args)
            StillsExporter(self, self.args.export_stills).export()

        else:
            self._load_model()
            self._training_data = load_training_data(self._training_data_path)
            self.navigator = Navigator(map_points=self.student.normalized_observed_reductions)
            self.improviser_params = ImproviserParameters()
            self._improviser = Improviser(self, self.improviser_params)

            app = QtGui.QApplication(sys.argv)
            app.setStyleSheet(open("stylesheet.qss").read())
            self.window = DimensionalityReductionMainWindow(
                self, self._scene_class, DimensionalityReductionToolbar, self.args)
            self.window.show()
            app.exec_()

    def _load_model(self):
        self.student, entity_model = load_model(self._model_path)
        self.entity.model = entity_model

    def _train_model(self):
        if hasattr(self.entity, "probe"):
            print "probing entity..."
            self.entity.probe(self._training_data)
            self._training_data = map(self.entity.adapt_value_to_model, self._training_data)
            print "ok"

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
            parameter_info = self.entity.parameter_info(n)
            col = self._training_data[:,n]
            stats = ["%.2f" % v for v in [min(col), max(col), numpy.mean(col), numpy.var(col)]]
            print format % (
                n, "%s %s" % (parameter_info["category"], parameter_info["component"]),
                stats[0],
                stats[1],
                stats[2],
                stats[3])

    def update(self):
        if self.window.toolbar.tabs.currentWidget() == self.window.toolbar.explore_tab:
            self.reduction = self.window.toolbar.get_reduction()
        elif self.window.toolbar.tabs.currentWidget() == self.window.toolbar.follow_tab:
            self._follow()
        elif self.window.toolbar.tabs.currentWidget() == self.window.toolbar.improvise_tab:
            self.reduction = self._improviser.current_position()
        self.output = self.student.inverse_transform(numpy.array([self.reduction]))[0]

    def proceed(self):
        if self.window.toolbar.tabs.currentWidget() == self.window.toolbar.follow_tab:
            self.entity.proceed(self.time_increment)
            if hasattr(self, "_velocity"):
                self.window.toolbar.velocity_label.setText("%.3f" % self._velocity)
            if hasattr(self.window.toolbar, "cursor_slider"):
                self.window.toolbar.cursor_slider.setValue(
                    self.entity.get_cursor() / self.entity.get_duration() * SLIDER_PRECISION)
        elif self.window.toolbar.tabs.currentWidget() == self.window.toolbar.improvise_tab:
            self._improviser.proceed(self.time_increment)

        if self._reduction_plot:
            print >>self._reduction_plot, " ".join([
                    str(v) for v in self.student.normalize_reduction(self.reduction)])

    def cursor_changed(self, value):
        self.entity.set_cursor(float(value) / SLIDER_PRECISION * self.entity.get_duration())

    def _follow(self):
        self.input = self.get_adapted_stimulus_value()
        next_reduction = self.student.transform(numpy.array([self.input]))[0]
        if self.reduction is not None:
            self._measure_velocity(
                self.student.normalize_reduction(self.reduction),
                self.student.normalize_reduction(next_reduction))
        self.reduction = next_reduction

    def get_adapted_stimulus_value(self):
        return self.entity.adapt_value_to_model(self.entity.get_value())

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
        while t < self.entity.get_duration():
            self._follow()
            print >>f, self._velocity
            t += self.time_increment
        f.close()

    def start_plot_reduction(self):
        self._reduction_plot = open(REDUCTION_PLOT_PATH, "w")
        print "plotting reduction"

    def stop_plot_reduction(self):
        self._reduction_plot.close()
        self._reduction_plot = None
        print "saved reduction data to %s" % REDUCTION_PLOT_PATH

class ImproviserParameters(Parameters):
    def __init__(self):
        Parameters.__init__(self)
        self.add_parameter("novelty", type=float, default=0,
                           choices=ParameterFloatRange(0., 1.))
        self.add_parameter("min_distance", type=float, default=0.5,
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
            num_segments=self.params.num_segments,
            novelty=self.params.novelty,
            min_distance=self.params.min_distance)

    def _departure(self):
        if self.experiment.reduction is None:
            unnormalized_departure = self.experiment.student.transform(numpy.array([
                        self.experiment.get_adapted_stimulus_value()]))[0]
        else:
            unnormalized_departure = self.experiment.reduction
        return self.experiment.student.normalize_reduction(unnormalized_departure)

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

class StillsExporter:
    def __init__(self, experiment, stills_data_path):
        self.experiment = experiment
        self._reductions = self._load_stills_data(stills_data_path)
        self._output_path = "%s.bvh" % stills_data_path.replace(".dat", "")

    def _load_stills_data(self, path):
        reductions = []
        for line in open(path, "r"):
            if len(line) > 1 and not line.startswith("#"):
                strings = line.split(" ")
                if len(strings) > 0:
                    normalized_reduction = map(float, strings)
                    reduction = self.experiment.student.unnormalize_reduction(normalized_reduction)
                    reductions.append(reduction)
        return reductions

    def export(self):
        print "exported stills to %s..." % self._output_path
        bvh_writer = BvhWriter(self.experiment.bvh_reader)
        for reduction in self._reductions:
            output = self.experiment.student.inverse_transform(numpy.array([reduction]))[0]
            hips = self.experiment.window._scene.parameters_to_hips(output)
            frame = self.experiment.window._scene._joint_to_bvh_frame(hips)
            bvh_writer.add_frame(frame)
        bvh_writer.write(self._output_path)
        print "ok"
