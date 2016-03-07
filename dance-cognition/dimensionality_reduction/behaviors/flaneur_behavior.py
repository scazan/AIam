from flaneur import Flaneur
from parameters import *
from event import Event
import numpy
import math

class FlaneurParameters(Parameters):
    def __init__(self):
        Parameters.__init__(self)
        self.add_parameter("translational_speed", type=float, default=.2,
                           choices=ParameterFloatRange(0., 1.))
        self.add_parameter("directional_speed", type=float, default=.05,
                           choices=ParameterFloatRange(0., 1.))
        self.add_parameter("look_ahead_distance", type=float, default=.1,
                           choices=ParameterFloatRange(0., 1.))

class FlaneurBehavior:
    def __init__(self, experiment, params, map_points,
                 enable_features=False, sampled_feature_vectors=None):
        self._experiment = experiment
        self.params = params
        params.add_listener(self._parameter_changed)
        self._flaneur = Flaneur(map_points)
        if enable_features:
            self._sampled_feature_vectors = sampled_feature_vectors
            self._target_features = None
            self._flaneur.weight_function = self._vicinity_to_target_features

    def _parameter_changed(self, parameter):
        setattr(self._flaneur, parameter.name, parameter.value())

    def proceed(self, time_increment):
        self._flaneur.proceed(time_increment)
        self._experiment.send_event_to_ui(
            Event(Event.NEIGHBORS_CENTER, self._flaneur.get_neighbors_center()))
        self._experiment.send_event_to_ui(
            Event(Event.NEIGHBORS, (self._flaneur.get_neighbors(),
                                    self._flaneur.get_weights())))

    def get_reduction(self):
        normalized_position = self._flaneur.get_position()
        return self._experiment.student.unnormalize_reduction(normalized_position)

    def set_reduction(self, reduction):
        pass

    def _vicinity_to_target_features(self, point_index):
        if self._target_features is None:
            return 1
        else:
            features = self._sampled_feature_vectors[point_index]
            distance_to_target_features = numpy.linalg.norm(features - self._target_features)
            if distance_to_target_features == 0:
                return 1
            else:
                return max(0, 1 - math.pow(distance_to_target_features, 3))

    def set_target_features(self, target_features):
        self._target_features = target_features
