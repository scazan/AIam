import numpy
from event import Event

class Explore:
    def __init__(self, experiment, enable_features=False, feature_matcher=None, sampled_reductions=None):
        self._experiment = experiment
        self._enable_features = enable_features
        self._feature_matcher = feature_matcher
        self._sampled_reductions = sampled_reductions
        normalized_reduction = numpy.array([.5] * experiment.args.num_components)
        self._reduction = self._experiment.student.unnormalize_reduction(normalized_reduction)
        if enable_features:
            self._target_reduction = None

    def get_reduction(self):
        if self._enable_features and self._target_reduction is not None:
            self._move_reduction_towards_target_features()
        return self._reduction

    def set_reduction(self, reduction):
        self._reduction = reduction

    def set_target_features(self, target_features):
        self._target_features = target_features
        if self._target_features is None:
            self._target_reduction = None
        else:
            distances_list, sampled_reductions_indices_list = self._feature_matcher.kneighbors(
                self._target_features, return_distance=True)
            distances = distances_list[0]
            sampled_reductions_indices = sampled_reductions_indices_list[0]
            nearest_neighbor_index = min(range(len(distances)),
                                         key=lambda neighbor_index: distances[neighbor_index])
            best_sampled_reductions_index = sampled_reductions_indices[nearest_neighbor_index]
            self._target_reduction = self._sampled_reductions[best_sampled_reductions_index]

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

    def _move_reduction_towards_target_features(self):
        direction_vector = self._target_reduction - self._reduction
        max_norm = self._experiment.args.feature_matching_speed
        direction_vector_norm = numpy.linalg.norm(direction_vector)
        if direction_vector_norm > 0:
            if direction_vector_norm > max_norm:
                direction_vector *= max_norm / direction_vector_norm
            self._reduction += direction_vector

    def showing_feature_matches(self):
        return (self._enable_features and
                self._target_reduction is not None and
                self._experiment.args.show_all_feature_matches)
