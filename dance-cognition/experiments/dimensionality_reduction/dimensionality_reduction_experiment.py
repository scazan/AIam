from experiment import *
from dimensionality_reduction_teacher import *
from component_analysis import ComponentAnalysis
import pca
import random
from leaky_integrator import LeakyIntegrator
from navigator import Navigator, PathFollower
import dynamics as dynamics_module
import modes
from parameters import *

class DimensionalityReductionExperiment(Experiment):
    @staticmethod
    def add_parser_arguments(parser):
        Experiment.add_parser_arguments(parser)
        parser.add_argument("--pca-type",
                            choices=["LinearPCA", "KernelPCA"],
                            default="LinearPCA")
        parser.add_argument("--num-components", "-n", type=int, default=4)
        parser.add_argument("--explore-beyond-observations", type=float, default=0.2)
        parser.add_argument("--mode",
                            choices=[modes.FOLLOW,
                                     modes.IMPROVISE,
                                     modes.EXPLORE],
                            default=modes.FOLLOW)
        parser.add_argument("--plot-velocity")
        parser.add_argument("--analyze-components", action="store_true")
        parser.add_argument("--analyze-accuracy", action="store_true")
        parser.add_argument("--training-data-stats", action="store_true")
        parser.add_argument("--export-stills")

    def __init__(self, parser):
        self.profiles_dir = "profiles/dimensionality_reduction"
        Experiment.__init__(self, parser)
        self.add_event_handler(Event.MODE, self._handle_mode_event)
        self.reduction = None
        self._velocity_integrator = LeakyIntegrator()
        self._mode = self.args.mode

    def ui_connected(self, handler):
        Experiment.ui_connected(self, handler)
        handler.send_event(Event(Event.MODE, self._mode))
        self._improviser_params.add_notifier(handler)
        self._improviser_params.notify_changed_all()

    def ui_disconnected(self, handler):
        Experiment.ui_disconnected(self, handler)
        self._improviser_params.remove_notifier(handler)

    def _handle_mode_event(self, event):
        self._mode = event.content

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
            self._create_ui_window()
            StillsExporter(self, self.args.export_stills).export()

        else:
            self._load_model()
            if not self.args.ui_only:
                self._training_data = load_training_data(self._training_data_path)
                self.navigator = Navigator(map_points=self.student.normalized_observed_reductions)
                self._improviser_params = ImproviserParameters()
                self.add_event_handler(Event.PARAMETER, self._improviser_params.handle_event)
                self._improviser = Improviser(self, self._improviser_params)
            self.run_backend_and_or_ui()

    def run_ui(self, client):
        from PyQt4 import QtGui
        app = QtGui.QApplication(sys.argv)
        app.setStyleSheet(open("stylesheet.qss").read())
        window = self._create_ui_window(client)
        window.show()
        app.exec_()

    def _create_ui_window(self, client=None):
        from ui.dimensionality_reduction_ui import DimensionalityReductionMainWindow, \
            DimensionalityReductionToolbar
        return DimensionalityReductionMainWindow(client, 
            self.entity, self.student, self.bvh_reader, self._scene_class,
            DimensionalityReductionToolbar, self.args)

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
        if self._mode == modes.FOLLOW:
            self._follow()
        elif self._mode == modes.IMPROVISE:
            self.reduction = self._improviser.current_position()
        self.output = self.student.inverse_transform(numpy.array([self.reduction]))[0]
        self.send_event_to_ui(Event(Event.REDUCTION, self.reduction))

    def proceed(self):
        if self._mode == modes.FOLLOW:
            self.entity.proceed(self.time_increment)
            if hasattr(self, "_velocity"):
                self.send_event_to_ui(Event(Event.VELOCITY, self._velocity))
            self.send_event_to_ui(Event(
                    Event.CURSOR,
                    self.entity.get_cursor() / self.entity.get_duration()))
        elif self._mode == modes.IMPROVISE:
            self._improviser.proceed(self.time_increment)
            self.send_event_to_ui(Event(Event.IMPROVISER_PATH, self._improviser.path()))

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
        self.add_parameter("dynamics", choices=["constant", "sine", "exponential"], default="sine")

class Improviser:
    def __init__(self, experiment, params):
        self.experiment = experiment
        self.params = params
        self._path = None
        self._path_follower = None

    def _select_next_move(self):
        path_segments = self._generate_path()
        self._path = self._interpolate_path(path_segments)
        self._path_follower = self._create_path_follower(self._path)

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
        dynamics_class = getattr(dynamics_module, "%s_dynamics" % self.params.dynamics)
        dynamics = dynamics_class(min_relative_velocity=self.params.min_relative_velocity)
        return PathFollower(path, self.params.velocity, dynamics)

    def proceed(self, time_increment):
        if self._path_follower is None:
            self._select_next_move()
        if self._path_follower.reached_destination():
            self._select_next_move()
        self._path_follower.proceed(time_increment)

    def current_position(self):
        normalized_position = self._path_follower.current_position()
        return self.experiment.student.unnormalize_reduction(normalized_position)

    def path(self):
        return self._path


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
