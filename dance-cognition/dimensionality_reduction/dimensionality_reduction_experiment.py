from experiment import *
from dimensionality_reduction_teacher import *
from component_analysis import ComponentAnalysis
import pca
from autoencoder import AutoEncoder
import random
import collections
import modes
from parameters import *
from behaviors.follow import Follow
from behaviors.explore import Explore
from behaviors.imitate import Imitate, ImitateParameters
from behaviors.improvise import ImproviseParameters, Improvise
from behaviors.flaneur_behavior import FlaneurBehavior, FlaneurParameters
from behaviors.hybrid import Hybrid, HybridParameters
import sampling
import sklearn.neighbors
from transformations import euler_from_quaternion

class DimensionalityReductionExperiment(Experiment):
    @staticmethod
    def add_parser_arguments(parser):
        Experiment.add_parser_arguments(parser)
        parser.add_argument("--pca-type",
                            choices=["LinearPCA", "KernelPCA"],
                            default="LinearPCA")
        parser.add_argument("--incremental", action="store_true")
        parser.add_argument("--num-components", "-n", type=int, default=4)
        parser.add_argument("--explore-beyond-observations", type=float, default=0.2)
        parser.add_argument("--mode",
                            choices=[modes.FOLLOW,
                                     modes.IMPROVISE,
                                     modes.EXPLORE,
                                     modes.IMITATE,
                                     modes.FLANEUR,
                                     modes.HYBRID],
                            default=modes.EXPLORE)
        parser.add_argument("--max-novelty", type=float, default=1.)
        parser.add_argument("--analyze-components", action="store_true")
        parser.add_argument("--analyze-accuracy", action="store_true")
        parser.add_argument("--training-data-stats", action="store_true")
        parser.add_argument("--export-stills")
        parser.add_argument("--preferred-location", type=str)
        parser.add_argument("--enable-features", action="store_true")
        parser.add_argument("--train-feature-matcher", action="store_true")
        parser.add_argument("--sampling-method", default="KMeans")
        parser.add_argument("--num-feature-matches", type=int, default=1)
        parser.add_argument("--show-output-features", action="store_true")
        parser.add_argument("--show-all-feature-matches", action="store_true")
        parser.add_argument("--plot-model", action="store_true")
        parser.add_argument("--plot-pose-map-contents", action="store_true")
        parser.add_argument("--plot-args")
        parser.add_argument("--memory-size", type=int, default=1000)
        parser.add_argument("--enable-io-blending", action="store_true")
        parser.add_argument("--io-blending", type=float)
        ImproviseParameters().add_parser_arguments(parser)
        FlaneurParameters().add_parser_arguments(parser)
        HybridParameters().add_parser_arguments(parser)

    def __init__(self, parser):
        self.profiles_dir = "profiles/dimensionality_reduction"
        Experiment.__init__(self, parser, event_handlers={
            Event.MODE: self._handle_mode_event,
            Event.REDUCTION: self._handle_reduction,
            Event.PARAMETER: self._handle_parameter_event,
            Event.USER_INTENSITY: self._handle_user_intensity,
            Event.SYSTEM_STATE_CHANGED: self._abort_path,
            Event.TARGET_FEATURES: self._handle_target_features,
            Event.TARGET_ROOT_VERTICAL_ORIENTATION: self._handle_target_root_vertical_orientation,
            Event.SET_IO_BLENDING: self._set_io_blending,
                })
        self.reduction = None
        self._mode = self.args.mode

        if self.args.enable_io_blending:
            self._io_blending_entity = self.entity_class(self)
            self._io_blending_entity.pose = self.bvh_reader.get_hierarchy().create_pose()
            self._io_blending = self.args.io_blending

        if self.args.enable_features:
            if self.args.sampling_method:
                self._sampling_class = getattr(sampling, "%sSampler" % self.args.sampling_method)
                self._sampling_class.add_parser_arguments(parser)
                self._sampling_args, _remaining_args = parser.parse_known_args()

            self._pose_for_feature_extraction = self.bvh_reader.get_hierarchy().create_pose()
            self._feature_matcher_path = "%s/%s.features" % (self.profiles_dir, self.args.profile)

    def ui_connected(self, handler):
        Experiment.ui_connected(self, handler)
        handler.send_event(Event(Event.MODE, self._mode))
        if self.reduction is not None:
            handler.send_event(Event(Event.REDUCTION, self.reduction))
        if self.args.enable_io_blending:
            handler.send_event(Event(Event.IO_BLENDING, self._io_blending))
        self._add_parameters_listener(self._improvise_params)
        if self.args.enable_features:
            self._add_parameters_listener(self._imitate_params)
            self._add_parameters_listener(self._hybrid_params)

    def ui_disconnected(self, handler):
        Experiment.ui_disconnected(self, handler)
        self._improvise_params.remove_listener(self._send_changed_parameter)
        if self.args.enable_features:
            self._imitate_params.remove_listener(self._send_changed_parameter)
            self._hybrid_params.remove_listener(self._send_changed_parameter)

    def _add_parameters_listener(self, parameters):
        parameters.add_listener(self._send_changed_parameter)
        parameters.notify_changed_all()

    def _send_changed_parameter(self, parameter):
        self.send_event_to_ui(Event(
                Event.PARAMETER,
                {"class": parameter.parameters.__class__.__name__,
                 "name": parameter.name,
                 "value": parameter.value()}))

    def _handle_mode_event(self, event):
        self._mode = event.content

    def _handle_reduction(self, event):
        new_reduction = event.content
        if self.reduction is None or not numpy.array_equal(new_reduction, self.reduction):
            self.reduction = new_reduction
            for behavior in self._behaviors:
                behavior.set_reduction(self.reduction)
            self.send_event_to_ui(event)

    def _update_using_behavior(self, behavior):
        self._potentially_update_reduction_using_behavior(behavior)
        self._update_entity_root_vertical_orientation_using_behavior(behavior)

    def _potentially_update_reduction_using_behavior(self, behavior):
        new_reduction = behavior.get_reduction()
        if new_reduction is not None and (
                self.reduction is None or not numpy.array_equal(new_reduction, self.reduction)):
            self.reduction = new_reduction
            for other_behavior in self._behaviors:
                if other_behavior != behavior:
                    behavior.set_reduction(self.reduction)
            self.send_event_to_ui(Event(Event.REDUCTION, self.reduction))

    def _update_entity_root_vertical_orientation_using_behavior(self, behavior):
        self.entity.modified_root_vertical_orientation = behavior.get_root_vertical_orientation()

    def add_parser_arguments_second_pass(self, parser, args):
        if args.incremental:
            dimensionality_reduction_class = AutoEncoder
        else:
            dimensionality_reduction_class = getattr(pca, args.pca_type)
        dimensionality_reduction_class.add_parser_arguments(parser)

    def run(self):
        teacher = Teacher(self.entity, self.args.training_data_frame_rate)

        if self.args.incremental:
            dimensionality_reduction_class = AutoEncoder
        else:
            dimensionality_reduction_class = getattr(pca, self.args.pca_type)
        num_input_dimensions = self.entity.get_value_length()
        self.student = dimensionality_reduction_class(
            num_input_dimensions, self.args.num_components, self.args)
            
        if self.args.training_data_stats:
            self._training_data = storage.load(self._training_data_path)
            self._print_training_data_stats()

        if self.args.train:
            self._training_data = teacher.create_training_data(self._training_duration())
            self._train_model()
            print "saving %s..." % self._student_model_path
            self.student.save(self._student_model_path)
            print "ok"
            storage.save(self.entity.model, self._entity_model_path)
            storage.save(self._training_data, self._training_data_path)

        elif self.args.analyze_components:
            self._load_model()
            ComponentAnalysis(
                pca=self.student,
                num_output_components=len(self.entity.get_value()),
                parameter_info_getter=self.entity.parameter_info).analyze()

        elif self.args.analyze_accuracy:
            self._training_data = storage.load(self._training_data_path)
            self._train_model()
            self.student.analyze_accuracy(self._training_data)

        elif self.args.export_stills:
            self._load_model()
            StillsExporter(self, self.args.export_stills).export()

        elif self.args.train_feature_matcher:
            self._load_model()
            self._training_data = storage.load(self._training_data_path)
            self._train_feature_matcher()

        elif self.args.plot_model:
            self._plot_model()

        elif self.args.plot_pose_map_contents:
            self._training_data = storage.load(self._training_data_path)
            self._plot_pose_map_contents()
            
        else:
            self._load_model()
            if not self.args.ui_only:
                if self.args.incremental:
                    self._training_data = collections.deque([], maxlen=self.args.memory_size)
                else:
                    self._training_data = storage.load(self._training_data_path)

                self._parameter_sets = {}
                self._follow = self._create_follow_behavior()
                self._explore = self._create_explore_behavior()
                self._improvise = self._create_improvise_behavior()
                self._flaneur_behavior = self._create_flaneur_behavior()
                self._behaviors = [
                    self._explore,
                    self._improvise,
                    self._flaneur_behavior]

                if self.args.enable_features:
                    self._feature_matcher, self._sampled_reductions = storage.load(
                        self._feature_matcher_path)
                    self._imitate = self._create_imitate_behavior()
                    self._behaviors.append(self._imitate)
                    self._hybrid = self._create_hybrid_behavior()
                    self._behaviors.append(self._hybrid)

            self.run_backend_and_or_ui()

    def _create_follow_behavior(self):
        return Follow(self)

    def _create_explore_behavior(self):
        return Explore(self)

    def _create_imitate_behavior(self):
        self._imitate_params = ImitateParameters()
        self._imitate_params.set_values_from_args(self.args)
        self._add_parameter_set(self._imitate_params)
        return Imitate(self, self._feature_matcher, self._sampled_reductions, self._imitate_params)

    def _create_hybrid_behavior(self):
        self._hybrid_params = HybridParameters()
        self._hybrid_params.set_values_from_args(self.args)
        self._add_parameter_set(self._hybrid_params)
        return Hybrid(
            self, self._feature_matcher, self._sampled_reductions,
            self.student.normalized_observed_reductions,
            self._hybrid_params)

    def _create_improvise_behavior(self):
        if self.args.preferred_location:
            preferred_location = numpy.array([
                    float(s) for s in self.args.preferred_location.split(",")])
        else:
            preferred_location = None
        self._improvise_params = ImproviseParameters()
        self._improvise_params.set_values_from_args(self.args)
        self._add_parameter_set(self._improvise_params)
        return Improvise(
            self, self._improvise_params,
            preferred_location,
            on_changed_path=lambda: \
                self.send_event_to_ui(Event(Event.IMPROVISE_PATH, self._improvise.path())))

    def _create_flaneur_behavior(self):
        self._flaneur_params = FlaneurParameters()
        self._flaneur_params.set_values_from_args(self.args)
        self._add_parameter_set(self._flaneur_params)
        return FlaneurBehavior(self, self._flaneur_params, self.student.normalized_observed_reductions)

    def _add_parameter_set(self, parameters):
        self._parameter_sets[parameters.__class__.__name__] = parameters

    def _handle_user_intensity(self, event):
        user_intensity = event.content
        self._improvise.handle_user_intensity(user_intensity)
        if self.args.enable_features:
            self._hybrid.handle_user_intensity(user_intensity)

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
        print "loading %s..." % self._student_model_path
        self.student.load(self._student_model_path)
        print "ok"
        entity_model = storage.load(self._entity_model_path)

    def _train_model(self):
        if hasattr(self.entity, "probe"):
            print "probing entity..."
            self.entity.probe(self._training_data)
            self._training_data = map(self.entity.adapt_value_to_model, self._training_data)
            print "ok"

        print "training model..."
        if self.args.incremental:
            self.student.batch_train(self._training_data, self.args.num_training_epochs)
        else:
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
        if self.args.enable_io_blending or self._mode == modes.FOLLOW or self.args.receive_from_pn:
            if self.args.receive_from_pn:
                self.input = self._input_from_pn
            else:
                self.input = self._follow.get_input()

            if self.args.enable_io_blending and self.input is not None and self.output is not None:
                self._update_io_blend_and_broadcast_it_to_ui()
            
            if self.input is not None and self.args.incremental:
                self.student.train([self.input])
                self._training_data.append(self.input)
                self.student.probe(self._training_data)
                self._improvise.set_normalized_observed_reductions(self.student.normalized_observed_reductions)
                self._flaneur_behavior.set_normalized_observed_reductions(self.student.normalized_observed_reductions)
                if self.args.enable_features:
                    self._hybrid.set_normalized_observed_reductions(self.student.normalized_observed_reductions)
                self.send_event_to_ui(Event(Event.REDUCTION_RANGE, self.student.reduction_range))
                self.send_event_to_ui(
                    Event(Event.NORMALIZED_OBSERVED_REDUCTIONS, self.student.normalized_observed_reductions))
            
        if self._mode == modes.FOLLOW:
            self._update_using_behavior(self._follow)
        elif self._mode == modes.IMPROVISE:
            self._update_using_behavior(self._improvise)
        elif self._mode == modes.EXPLORE:
            self._update_using_behavior(self._explore)
        elif self._mode == modes.IMITATE:
            self._update_using_behavior(self._imitate)
        elif self._mode == modes.FLANEUR:
            self._update_using_behavior(self._flaneur_behavior)
        elif self._mode == modes.HYBRID:
            self._update_using_behavior(self._hybrid)

        if self.reduction is not None:
            self.output = self.student.inverse_transform(numpy.array([self.reduction]))[0]

        if self.args.enable_features and self.args.show_output_features:
            self.entity.parameters_to_processed_pose(self.output, self._pose_for_feature_extraction)
            features = self.entity.extract_features(self._pose_for_feature_extraction)
            self.send_event_to_ui(Event(Event.FEATURES, features))

    def _update_io_blend_and_broadcast_it_to_ui(self):
        io_blend = numpy.array(self.output) * self._io_blending + \
                   numpy.array(self.input) * (1-self._io_blending)
        processed_io_blend = self._io_blending_entity.process_output(io_blend)
        self.send_event_to_ui(Event(Event.IO_BLEND, processed_io_blend))
                
    def process_and_broadcast_output(self):
        if not (self._mode == modes.IMITATE and
                self._imitate.showing_feature_matches()):
            Experiment.process_and_broadcast_output(self)

    def proceed(self):
        if self._mode == modes.FOLLOW and not self.args.incremental:
            self._follow.proceed(self.time_increment)

        if self._mode == modes.IMITATE:
            self._imitate.proceed(self.time_increment)
        elif self._mode == modes.IMPROVISE:
            self._improvise.proceed(self.time_increment)
        elif self._mode == modes.FLANEUR:
            self._flaneur_behavior.proceed(self.time_increment)
        elif self._mode == modes.HYBRID:
            self._hybrid.proceed(self.time_increment)

    def update_cursor(self, cursor):
        Experiment.update_cursor(self, cursor)
        self._follow.on_updated_cursor()

    def _handle_parameter_event(self, event):
        class_name = event.content["class"]
        parameters = self._parameter_sets[class_name]
        parameter_name = event.content["name"]
        parameter = parameters.get_parameter(parameter_name)
        parameter.set_value(event.content["value"])
        self._broadcast_event_to_other_uis(event)

    def _broadcast_event_to_other_uis(self, event):
        self.send_event_to_ui(event)

    def _handle_target_features(self, event):
        if self.args.enable_features:
            self._imitate.set_target_features(event.content)
            self._hybrid.set_target_features(event.content)
        self._broadcast_event_to_other_uis(event)

    def _train_feature_matcher(self):
        print "training feature matcher:"
        feature_matcher = sklearn.neighbors.KNeighborsClassifier(
            n_neighbors=self.args.num_feature_matches, weights='uniform')
        print "sampling training data of size %s..." % len(
            self.student.normalized_observed_reductions)
        sampled_normalized_reductions = self._sample_normalized_reduction_space(
            self.student.normalized_observed_reductions)
        print "selected %s samples" % len(sampled_normalized_reductions)
        sampled_reductions = [
            self.student.unnormalize_reduction(normalized_reduction)
            for normalized_reduction in sampled_normalized_reductions]
        print "extracting features from samples..."
        feature_vectors = [
            self._reduction_to_feature_vector(reduction)
            for reduction in sampled_reductions]
        print "ok"
        print "training feature matcher on samples..."
        feature_matcher.fit(feature_vectors, sampled_reductions)
        print "ok"
        storage.save((feature_matcher, sampled_reductions), self._feature_matcher_path)

    def _sample_normalized_reduction_space(self, observations):
        if self.args.sampling_method:
            return self._sampling_class(observations, self._sampling_args).sample()
        else:
            return observations

    def _reduction_to_feature_vector(self, reduction):
        output = self.student.inverse_transform(numpy.array([reduction]))[0]
        self.entity.parameters_to_processed_pose(
            output, self._pose_for_feature_extraction)
        features = self.entity.extract_features(self._pose_for_feature_extraction)
        return features

    def should_read_bvh_frames(self):
        return self.args.train or self.args.mode or self.args.incremental

    def _handle_target_root_vertical_orientation(self, event):
        orientation = event.content
        for behavior in self._behaviors:
            behavior.set_target_root_vertical_orientation(orientation)

    def _set_io_blending(self, event):
        self._io_blending = event.content
        self._update_io_blend_and_broadcast_it_to_ui()
        
    def _plot_model(self):
        from plotting.model_plotter import ModelPlotter
        parser = ArgumentParser()
        ModelPlotter.add_parser_arguments(parser)
        if self.args.plot_args:
            strings = self.args.plot_args.split(" ")
        else:
            strings = []
        args = parser.parse_args(strings)
        self._load_model()
        plotter = ModelPlotter(self, args)
        plotter.plot()

    def _plot_pose_map_contents(self):
        from plotting.pose_map_contents_plotter import PoseMapContentsPlotter
        parser = ArgumentParser()
        PoseMapContentsPlotter.add_parser_arguments(parser)
        if self.args.plot_args:
            strings = self.args.plot_args.split(" ")
        else:
            strings = []
        args = parser.parse_args(strings)
        plotter = PoseMapContentsPlotter(self, args)
        plotter.plot()
        
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
