import numpy
from event import Event
from parameters import *
from dimensionality_reduction.utils import PositionComparison

class ImitateParameters(Parameters):
    def __init__(self):
        Parameters.__init__(self)
        self.add_parameter("translational_speed", type=float, default=0.5,
                           choices=ParameterFloatRange(0., 1.))
        self.add_parameter("directional_speed", type=float, default=3,
                           choices=ParameterFloatRange(0., 3.))

THRESHOLD_DISTANCE_TO_TARGET = 0.01

class Imitate:
    def __init__(self,
                 experiment,
                 feature_matcher,
                 sampled_reductions,
                 params):
        self._experiment = experiment
        self._feature_matcher = feature_matcher
        self._sampled_reductions = sampled_reductions
        self.params = params
        self._target_normalized_reduction = None
        self._new_target_features = None
        self.set_reduction(numpy.array([.5] * experiment.args.num_components))
        self._direction = None

    def proceed(self, time_increment):
        self._process_potential_new_target_features()
        if self._target_normalized_reduction is not None:
            self._time_increment = time_increment
            self._move_normalized_reduction_towards_target_features()

    def get_reduction(self):
        return self._experiment.student.unnormalize_reduction(self._normalized_reduction)

    def set_reduction(self, reduction):
        self._reduction = reduction
        self._normalized_reduction = self._experiment.student.normalize_reduction(reduction)

    def set_target_features(self, target_features):
        self._new_target_features = target_features

    def _process_potential_new_target_features(self):
        if self._new_target_features is not None:
            self._process_target_features(self._new_target_features)
            self._new_target_features = None

    def _process_target_features(self, target_features):
        distances_list, sampled_reductions_indices_list = self._feature_matcher.kneighbors(
            target_features, return_distance=True)
        distances = distances_list[0]
        sampled_reductions_indices = sampled_reductions_indices_list[0]
        nearest_neighbor_index = min(range(len(distances)),
                                     key=lambda neighbor_index: distances[neighbor_index])
        best_sampled_reductions_index = sampled_reductions_indices[nearest_neighbor_index]
        target_reduction = self._sampled_reductions[best_sampled_reductions_index]
        self._experiment.send_event_to_ui(Event(Event.TARGET_REDUCTION, target_reduction))
        self._target_normalized_reduction = self._experiment.student.normalize_reduction(
            target_reduction)

        if self._experiment.args.show_all_feature_matches:
            match_result_as_tuples = [
                (self._reduction_to_processed_output(
                        self._sampled_reductions[sampled_reductions_index]),
                 distance)
                for sampled_reductions_index, distance
                in zip(sampled_reductions_indices, distances)]
            self._experiment.send_event_to_ui(Event(Event.FEATURE_MATCH_RESULT, match_result_as_tuples))

    def _reduction_to_processed_output(self, reduction):
        output = self._experiment.student.inverse_transform(numpy.array([reduction]))[0]
        return self._experiment.entity.process_output(output)

    def _move_normalized_reduction_towards_target_features(self):
        self._process_direction()
        if self._distance_to_target_normalized_reduction > THRESHOLD_DISTANCE_TO_TARGET:
            self._move_in_direction()

    def _process_direction(self):
        target_comparison = PositionComparison(
            source=self._normalized_reduction,
            target=self._target_normalized_reduction)
        self._distance_to_target_normalized_reduction = target_comparison.get_distance_to_target()
        if self._distance_to_target_normalized_reduction > 0:
            target_direction = target_comparison.get_direction_as_unit_vector()
            if self._direction is None:
                self._direction = target_direction
            else:
                self._move_towards_direction(target_direction)
        
    def _move_towards_direction(self, target_direction):
        difference = target_direction - self._direction
        norm = numpy.linalg.norm(difference)
        if norm > 0:
            self._direction += difference / norm * min(
                self.params.directional_speed * self._time_increment, 1)

    def _move_in_direction(self):
        norm = numpy.linalg.norm(self._direction)
        if norm > 0:
            scaled_directional_vector = self._direction / norm * \
                min(self._time_increment * self.params.translational_speed, 1)
            scaled_directional_vector_norm = numpy.linalg.norm(
                scaled_directional_vector)
            if scaled_directional_vector_norm > self._distance_to_target_normalized_reduction:
                scaled_directional_vector *= self._distance_to_target_normalized_reduction / \
                    scaled_directional_vector_norm
            self._normalized_reduction += scaled_directional_vector

    def showing_feature_matches(self):
        return (self._target_normalized_reduction is not None and
                self._experiment.args.show_all_feature_matches)
