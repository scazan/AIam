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
import interpolation
import sklearn.neighbors

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
        parser.add_argument("--max-novelty", type=float, default=1.)
        parser.add_argument("--plot-velocity")
        parser.add_argument("--analyze-components", action="store_true")
        parser.add_argument("--analyze-accuracy", action="store_true")
        parser.add_argument("--training-data-stats", action="store_true")
        parser.add_argument("--export-stills")
        parser.add_argument("--preferred-location", type=str)
        parser.add_argument("--enable-features", action="store_true")
        parser.add_argument("--train-feature-matcher", action="store_true")
        ImproviserParameters().add_parser_arguments(parser)

    def __init__(self, parser):
        self.profiles_dir = "profiles/dimensionality_reduction"
        Experiment.__init__(self, parser, event_handlers={
                Event.MODE: self._handle_mode_event,
                Event.REDUCTION: self._set_reduction,
                Event.PARAMETER: self._handle_parameter_event,
                Event.ABORT_PATH: self._abort_path,
                Event.TARGET_FEATURES: self._handle_target_features,
                })
        self.reduction = None
        self._velocity_integrator = LeakyIntegrator()
        self._mode = self.args.mode
        if self.args.enable_features:
            self._target_reduction = None
            self._pose_for_feature_extraction = self.bvh_reader.get_hierarchy().create_pose()
            self._feature_matcher_path = "%s/%s.features" % (self.profiles_dir, self.args.profile)

    def ui_connected(self, handler):
        Experiment.ui_connected(self, handler)
        handler.send_event(Event(Event.MODE, self._mode))
        if self.reduction is not None:
            handler.send_event(Event(Event.REDUCTION, self.reduction))
        self._improviser_params.add_notifier(handler)
        self._improviser_params.notify_changed_all()

    def ui_disconnected(self, handler):
        Experiment.ui_disconnected(self, handler)
        self._improviser_params.remove_notifier(handler)

    def _handle_mode_event(self, event):
        self._mode = event.content

    def _set_reduction(self, event):
        self.reduction = event.content

    def run(self):
        teacher = Teacher(self.entity, self.args.training_data_frame_rate)

        if self.args.training_data_stats:
            self._training_data = storage.load(self._training_data_path)
            self._print_training_data_stats()

        if self.args.train:
            pca_class = getattr(pca, self.args.pca_type)
            self.student = pca_class(n_components=self.args.num_components)
            self._training_data = teacher.create_training_data(self._training_duration())
            self._train_model()
            storage.save([self.student, self.entity.model], self._model_path)
            storage.save(self._training_data, self._training_data_path)

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
            self._training_data = storage.load(self._training_data_path)
            self.student.analyze_accuracy(self._training_data)

        elif self.args.export_stills:
            self._load_model()
            StillsExporter(self, self.args.export_stills).export()

        elif self.args.train_feature_matcher:
            self._load_model()
            self._training_data = storage.load(self._training_data_path)
            self._train_feature_matcher()

        else:
            self._load_model()
            if not self.args.ui_only:
                self._training_data = storage.load(self._training_data_path)
                if self.args.enable_features:
                    self._feature_matcher, self._sampled_reductions = storage.load(
                        self._feature_matcher_path)
                self.navigator = Navigator(
                    map_points=self.student.normalized_observed_reductions)
                if self.args.preferred_location:
                    self.preferred_location = numpy.array([
                            float(s) for s in self.args.preferred_location.split(",")])
                    self.navigator.set_preferred_location(self.preferred_location)
                self._improviser_params = ImproviserParameters()
                self._improviser_params.set_values_from_args(self.args)
                self._improviser = Improviser(
                    self, self._improviser_params,
                    on_changed_path=lambda: \
                        self.send_event_to_ui(Event(Event.IMPROVISER_PATH, self._improviser.path())))
            self.run_backend_and_or_ui()

    def _abort_path(self, event):
        self._improviser.select_next_move()

    def add_ui_parser_arguments(self, parser):
        from ui.dimensionality_reduction_ui import DimensionalityReductionMainWindow
        DimensionalityReductionMainWindow.add_parser_arguments(parser)

    def run_ui(self, client):
        from PyQt4 import QtGui
        app = QtGui.QApplication(sys.argv)
        app.setStyleSheet(open("dimensionality_reduction/ui/stylesheet.qss").read())
        app.setWindowIcon(QtGui.QIcon("ui/icon.png"))
        window = self._create_ui_window(client)
        window.start()
        if client:
            client.connect()
        window.show()
        app.exec_()

    def _create_ui_window(self, client):
        from ui.dimensionality_reduction_ui import DimensionalityReductionMainWindow, \
            DimensionalityReductionToolbar
        return DimensionalityReductionMainWindow(client, 
            self.entity, self.student, self.bvh_reader, self._scene_class,
            DimensionalityReductionToolbar, self.args)

    def _load_model(self):
        self.student, entity_model = storage.load(self._model_path)
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
            self.send_event_to_ui(Event(Event.REDUCTION, self.reduction))
        elif self._mode == modes.IMPROVISE:
            self.reduction = self._improviser.current_position()
            self.send_event_to_ui(Event(Event.REDUCTION, self.reduction))
        elif self._mode == modes.EXPLORE:
            if self.reduction is None:
                normalized_reduction = numpy.array([.5] * self.args.num_components)
                self.reduction = self.student.unnormalize_reduction(normalized_reduction)
            if self.args.enable_features and self._target_reduction is not None:
                self._move_reduction_towards_target_features()
                self.send_event_to_ui(Event(Event.REDUCTION, self.reduction))
        self.output = self.student.inverse_transform(numpy.array([self.reduction]))[0]

        if self.args.enable_features:
            self.entity.parameters_to_processed_pose(self.output, self._pose_for_feature_extraction)
            features = self.entity.extract_features(self._pose_for_feature_extraction)
            self.send_event_to_ui(Event(Event.FEATURES, features))

    def proceed(self):
        if self._mode == modes.FOLLOW:
            self.entity.proceed(self.time_increment)
            if hasattr(self, "_velocity"):
                self.send_event_to_ui(Event(Event.VELOCITY, self._velocity))
            self.send_event_to_ui(Event(
                    Event.CURSOR,
                    self.entity.get_cursor() / self.entity.get_duration()))
            self._potentially_send_bvh_index_to_ui()
        elif self._mode == modes.IMPROVISE:
            self._improviser.proceed(self.time_increment)

    def update_cursor(self, event):
        Experiment.update_cursor(self, event)
        self._potentially_send_bvh_index_to_ui()

    def _potentially_send_bvh_index_to_ui(self):
        if self.args.bvh:
            bvh_index = self._get_current_bvh_index()
            self.send_event_to_ui(Event(Event.BVH_INDEX, bvh_index))

    def _get_current_bvh_index(self):
        bvh_reader = self.bvh_reader.get_reader_at_time(self.entity.get_cursor())
        return bvh_reader.index
            
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

    def _handle_parameter_event(self, event):
        self._improviser_params.handle_event(event)
        self._broadcast_event_to_other_uis(event)

    def _broadcast_event_to_other_uis(self, event):
        self.send_event_to_ui(event)

    def _handle_target_features(self, event):
        self._target_features = event.content
        if self._target_features is None:
            self._target_reduction = None
        else:
            sampled_reductions_indices = self._feature_matcher.kneighbors(
                self._target_features, return_distance=False)[0]
            sampled_reductions_index = sampled_reductions_indices[0]
            self._target_reduction = self._sampled_reductions[sampled_reductions_index]
            self._broadcast_event_to_other_uis(event)

    def _move_reduction_towards_target_features(self):
        direction_vector = self._target_reduction - self.reduction
        max_norm = .5
        direction_vector_norm = numpy.linalg.norm(direction_vector)
        if direction_vector_norm > 0:
            if direction_vector_norm > max_norm:
                direction_vector *= max_norm / direction_vector_norm
            self.reduction += direction_vector

    def _train_feature_matcher(self):
        print "training feature matcher..."
        feature_matcher = sklearn.neighbors.KNeighborsClassifier(
            n_neighbors=1, weights='uniform')
        sampled_reductions = self._sample_reduction_space()
        feature_vectors = [
            self._reduction_to_feature_vector(reduction)
            for reduction in sampled_reductions]
        feature_matcher.fit(feature_vectors, sampled_reductions)
        storage.save((feature_matcher, sampled_reductions), self._feature_matcher_path)

    def _sample_reduction_space(self, num_training_data=100, samples_per_training_data=10):
        sampled_reductions = []
        for n in range(num_training_data):
            training_data_index = int(float(n) / num_training_data * len(self._training_data))
            parameters = self._training_data[training_data_index]
            reduction = self.student.transform(numpy.array([parameters]))[0]
            sampled_reductions += self._sample_reductions_around(
                reduction, samples_per_training_data)
        return sampled_reductions

    def _sample_reductions_around(self, reduction, num_samples):
        return [reduction + self._random_vector(magnitude=0.1)
                for n in range(num_samples)]

    def _random_vector(self, magnitude):
        return (numpy.random.rand(self.args.num_components) - 0.5) * magnitude

    def _reduction_to_feature_vector(self, reduction):
        output = self.student.inverse_transform(numpy.array([reduction]))[0]
        self.entity.parameters_to_processed_pose(
            output, self._pose_for_feature_extraction)
        features = self.entity.extract_features(self._pose_for_feature_extraction)
        return features

class ImproviserParameters(Parameters):
    def __init__(self):
        Parameters.__init__(self)
        self.add_parameter("novelty", type=float, default=.5,
                           choices=ParameterFloatRange(0., 1.))
        self.add_parameter("extension", type=float, default=1.,
                           choices=ParameterFloatRange(0., 2.))
        self.add_parameter("num_segments", type=int, default=10)
        self.add_parameter("resolution", type=int, default=100)
        self.add_parameter("velocity", type=float, default=0.5,
                           choices=ParameterFloatRange(.001, 3.))
        self.add_parameter("min_relative_velocity", type=float, default=.3,
                           choices=ParameterFloatRange(.001, 1.))
        self.add_parameter("dynamics", choices=["constant", "sine", "exponential"], default="sine")
        self.add_parameter("location_preference", type=float, default=0,
                           choices=ParameterFloatRange(0., 1.))

class Improviser:
    def __init__(self, experiment, params, on_changed_path=None):
        self.experiment = experiment
        self.params = params
        self._path = None
        self._path_follower = None
        self._on_changed_path = on_changed_path

    def select_next_move(self):
        found_non_empty_path = False
        while not found_non_empty_path:
            path_segments = self._generate_path()
            print "path_segments", len(path_segments)
            self._path = self._interpolate_path(path_segments)
            print "interpolated path", len(self._path)
            if len(self._path) > 0:
                found_non_empty_path = True
        self._path_follower = self._create_path_follower(self._path)
        if self._on_changed_path:
            self._on_changed_path()

    def _generate_path(self):
        while True:
            path = self._generate_potentially_empty_path()
            if len(path) > 0:
                return path

    def _generate_potentially_empty_path(self):
        return self.experiment.navigator.generate_path(
            departure = self._departure(),
            num_segments = self.params.num_segments,
            novelty = self.params.novelty * self.experiment.args.max_novelty,
            extension = self.params.extension,
            location_preference = self.params.location_preference)

    def _departure(self):
        if self.experiment.reduction is None:
            if self.experiment.args.preferred_location:
                return self.experiment.preferred_location
            else:
                unnormalized_departure = self._get_stimulus()
        else:
            unnormalized_departure = self.experiment.reduction
        return self.experiment.student.normalize_reduction(unnormalized_departure)

    def _get_stimulus(self):
        return self.experiment.student.transform(numpy.array([
                    self.experiment.get_adapted_stimulus_value()]))[0]

    def _interpolate_path(self, path_segments):
        return interpolation.interpolate(
            path_segments,
            resolution=self.params.resolution)

    def _create_path_follower(self, path):
        dynamics_class = getattr(dynamics_module, "%s_dynamics" % self.params.dynamics)
        dynamics = dynamics_class(min_relative_velocity=self.params.min_relative_velocity)
        return PathFollower(path, dynamics)

    def proceed(self, time_increment):
        if self._path_follower is None:
            self.select_next_move()
        if self._path_follower.reached_destination():
            self.select_next_move()
        self._path_follower.proceed(time_increment * self.params.velocity)

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
        bvh_writer = BvhWriter(
            self.experiment.bvh_reader.get_hierarchy(),
            self.experiment.bvh_reader.get_frame_time())
        for reduction in self._reductions:
            output = self.experiment.student.inverse_transform(numpy.array([reduction]))[0]
            self.experiment.entity.parameters_to_processed_pose(output, self.experiment.pose)
            bvh_writer.add_pose_as_frame(self.experiment.pose)
        bvh_writer.write(self._output_path)
        print "ok"
