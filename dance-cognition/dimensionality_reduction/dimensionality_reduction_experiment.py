from experiment import *
from dimensionality_reduction_teacher import *
from component_analysis import ComponentAnalysis
import pca
import random
import modes
from parameters import *
from behaviors.follow import Follow
from behaviors.explore import Explore
from behaviors.improvise import ImproviseParameters, Improvise
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
                            default=modes.EXPLORE)
        parser.add_argument("--max-novelty", type=float, default=1.)
        parser.add_argument("--analyze-components", action="store_true")
        parser.add_argument("--analyze-accuracy", action="store_true")
        parser.add_argument("--training-data-stats", action="store_true")
        parser.add_argument("--export-stills")
        parser.add_argument("--preferred-location", type=str)
        parser.add_argument("--enable-features", action="store_true")
        parser.add_argument("--train-feature-matcher", action="store_true")
        parser.add_argument("--feature-matching-speed", type=float, default=1.5)
        parser.add_argument("--num-feature-matches", type=int, default=1)
        parser.add_argument("--show-all-feature-matches", action="store_true")
        parser.add_argument("--face-forward", action="store_true")
        ImproviseParameters().add_parser_arguments(parser)

    def __init__(self, parser):
        self.profiles_dir = "profiles/dimensionality_reduction"
        Experiment.__init__(self, parser, event_handlers={
                Event.MODE: self._handle_mode_event,
                Event.REDUCTION: lambda event: self._set_reduction(event.content),
                Event.PARAMETER: self._handle_parameter_event,
                Event.ABORT_PATH: self._abort_path,
                Event.TARGET_FEATURES: self._handle_target_features,
                })
        self.reduction = None
        self._mode = self.args.mode
        if self.args.face_forward:
            self.entity.face_forward = True
        if self.args.enable_features:
            self._pose_for_feature_extraction = self.bvh_reader.get_hierarchy().create_pose()
            self._feature_matcher_path = "%s/%s.features" % (self.profiles_dir, self.args.profile)

    def ui_connected(self, handler):
        Experiment.ui_connected(self, handler)
        handler.send_event(Event(Event.MODE, self._mode))
        if self.reduction is not None:
            handler.send_event(Event(Event.REDUCTION, self.reduction))
        self._improvise_params.add_notifier(handler)
        self._improvise_params.notify_changed_all()

    def ui_disconnected(self, handler):
        Experiment.ui_disconnected(self, handler)
        self._improvise_params.remove_notifier(handler)

    def _handle_mode_event(self, event):
        self._mode = event.content

    def _set_reduction(self, new_reduction):
        if self.reduction is None or not numpy.array_equal(new_reduction, self.reduction):
            self.reduction = new_reduction
            for behavior in self._behaviors:
                behavior.set_reduction(self.reduction)
            self.send_event_to_ui(Event(Event.REDUCTION, self.reduction))

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

                self._follow = self._create_follow_behavior()
                self._explore = self._create_explore_behavior()
                self._improvise = self._create_improvise_behavior()
                self._behaviors = [self._explore, self._improvise]

            self.run_backend_and_or_ui()

    def _create_follow_behavior(self):
        return Follow(self)

    def _create_explore_behavior(self):
        kwargs = {}
        if self.args.enable_features:
            feature_matcher, sampled_reductions = storage.load(self._feature_matcher_path)
            kwargs["enable_features"] = True
            kwargs["feature_matcher"] = feature_matcher
            kwargs["sampled_reductions"] = sampled_reductions
        return Explore(self, **kwargs)

    def _create_improvise_behavior(self):
        if self.args.preferred_location:
            preferred_location = numpy.array([
                    float(s) for s in self.args.preferred_location.split(",")])
        else:
            preferred_location = None
        self._improvise_params = ImproviseParameters()
        self._improvise_params.set_values_from_args(self.args)
        return Improvise(
            self, self._improvise_params,
            preferred_location,
            on_changed_path=lambda: \
                self.send_event_to_ui(Event(Event.IMPROVISE_PATH, self._improvise.path())))

    def _abort_path(self, event):
        self._improvise.select_next_move()

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
            self.input = self._follow.get_input()
            self._set_reduction(self._follow.get_reduction())
        elif self._mode == modes.IMPROVISE:
            self._set_reduction(self._improvise.get_reduction())
        elif self._mode == modes.EXPLORE:
            self._set_reduction(self._explore.get_reduction())
        self.output = self.student.inverse_transform(numpy.array([self.reduction]))[0]

        if self.args.enable_features:
            self.entity.parameters_to_processed_pose(self.output, self._pose_for_feature_extraction)
            features = self.entity.extract_features(self._pose_for_feature_extraction)
            self.send_event_to_ui(Event(Event.FEATURES, features))

    def process_and_broadcast_output(self):
        if not (self._mode == modes.EXPLORE and
                self._explore.showing_feature_matches()):
            Experiment.process_and_broadcast_output(self)

    def proceed(self):
        if self._mode == modes.FOLLOW:
            self._follow.proceed(self.time_increment)
        elif self._mode == modes.IMPROVISE:
            self._improvise.proceed(self.time_increment)

    def update_cursor(self, cursor):
        Experiment.update_cursor(self, cursor)
        self._follow.on_updated_cursor()

    def _handle_parameter_event(self, event):
        self._improvise_params.handle_event(event)
        self._broadcast_event_to_other_uis(event)

    def _broadcast_event_to_other_uis(self, event):
        self.send_event_to_ui(event)

    def _handle_target_features(self, event):
        self._explore.set_target_features(event.content)
        self._broadcast_event_to_other_uis(event)

    def _train_feature_matcher(self):
        print "training feature matcher..."
        feature_matcher = sklearn.neighbors.KNeighborsClassifier(
            n_neighbors=self.args.num_feature_matches, weights='uniform')
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

    def should_read_bvh_frames(self):
        return self.args.train or self.args.mode == modes.FOLLOW

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
