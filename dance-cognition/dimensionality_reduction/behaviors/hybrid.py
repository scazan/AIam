import numpy
from flaneur import Flaneur
from flaneur_behavior import FlaneurParameters
from imitate import Imitate, ImitateParameters, THRESHOLD_DISTANCE_TO_TARGET
from event import Event
from parameters import *
from interpolation import linear_interpolation
from dimensionality_reduction.utils import PositionComparison
import math
import copy

IDLE_IMITATION = 0.5
IDLE_TARGET_FEATURES = numpy.array([0, 0, 0])

IDLE_FLANEUR_PARAMETERS = {
    "translational_speed": 0.01,
    "directional_speed": 1.1,
    "look_ahead_distance": 0.2,
}

ACTIVE_FLANEUR_PARAMETERS = {
    "translational_speed": 0.6,
    "directional_speed": 1.1,
    "look_ahead_distance": 0.2,
}

class HybridParameters(Parameters):
    def __init__(self):
        Parameters.__init__(self)
        self.add_parameter("imitation", type=float, default=0,
                           choices=ParameterFloatRange(0., 1.))
        self._add_flaneur_parameters()

    def _add_flaneur_parameters(self):
        for flaneur_parameter in FlaneurParameters():
            hybrid_parameter = self.add_parameter(
                "flaneur_%s" % flaneur_parameter.name,
                flaneur_parameter.type,
                flaneur_parameter.default,
                flaneur_parameter.choices)
            hybrid_parameter.flaneur_parameter_name = flaneur_parameter.name

class Hybrid:
    def __init__(self,
                 experiment,
                 feature_matcher,
                 sampled_reductions,
                 map_points,
                 parameters):
        self._experiment = experiment
        self._parameters = parameters
        parameters.add_listener(self._parameter_changed)
        self._create_flaneur(map_points)
        self._create_imitate(feature_matcher, sampled_reductions)
        n_dimensions = len(map_points[0])
        self._position = None
        self._direction = None
        self.handle_user_intensity(None)

    def _parameter_changed(self, hybrid_parameter):
        if hasattr(hybrid_parameter, "flaneur_parameter_name"):
            flaneur_parameter = self._flaneur_parameters.get_parameter(
                hybrid_parameter.flaneur_parameter_name)
            flaneur_parameter.set_value(hybrid_parameter.value())

    def _create_flaneur(self, map_points):
        self._flaneur_parameters = FlaneurParameters()
        self._flaneur = Flaneur(map_points)

    def _create_imitate(self, feature_matcher, sampled_reductions):
        self._imitate_parameters = ImitateParameters()
        self._imitate = Imitate(
            self._experiment, feature_matcher, sampled_reductions, self._imitate_parameters)

    def proceed(self, time_increment):
        self._time_increment = time_increment
        if self._position is None:
            self._position = copy.copy(self._imitate.get_target_position())
        self._process_direction()
        if self._parameters.imitation < 0.99 or self._distance_to_target > THRESHOLD_DISTANCE_TO_TARGET:
            self._move_in_direction()
        self._experiment.send_event_to_ui(
            Event(Event.NEIGHBORS_CENTER, self._flaneur.get_neighbors_center()))

    def _process_direction(self):
        target_position = self._get_target_position()
        target_comparison = PositionComparison(
            source=self._position,
            target=target_position)
        self._distance_to_target = target_comparison.get_distance_to_target()
        if self._distance_to_target > 0:
            target_direction = target_comparison.get_direction_as_unit_vector()
            if self._direction is None:
                self._direction = target_direction
            else:
                self._move_towards_direction(target_direction)

    def _get_target_position(self):
        flaneur_target_position = self._flaneur.get_target_position(
            self._position, self._direction)
        imitate_target_position = self._imitate.get_target_position()
        if imitate_target_position is None:
            return flaneur_target_position
        else:
            return linear_interpolation(
                flaneur_target_position, imitate_target_position, self._parameters.imitation)

    def _move_towards_direction(self, target_direction):
        difference = target_direction - self._direction
        norm = numpy.linalg.norm(difference)
        if norm > 0:
            directional_speed = linear_interpolation(
                self._flaneur_parameters.directional_speed,
                self._imitate_parameters.directional_speed,
                self._parameters.imitation)
            self._direction += difference / norm * min(directional_speed * self._time_increment, 1)

    def _move_in_direction(self):
        norm = numpy.linalg.norm(self._direction)
        if norm > 0:
            translational_speed = linear_interpolation(
                self._flaneur_parameters.translational_speed,
                self._imitate_parameters.translational_speed,
                self._parameters.imitation)
            self._position += self._direction / norm * self._time_increment * translational_speed

    def get_reduction(self):
        return self._experiment.student.unnormalize_reduction(self._position)

    def set_reduction(self, reduction):
        pass

    def set_target_features(self, target_features):
        self._imitate.set_target_features(target_features)

    def handle_user_intensity(self, relative_intensity):
        if relative_intensity is None:
            self._parameters.get_parameter("imitation").set_value(IDLE_IMITATION)
            self.set_target_features(IDLE_TARGET_FEATURES)
            self._set_flaneur_parameters(IDLE_FLANEUR_PARAMETERS)
        else:
            imitation = 1 - math.pow(relative_intensity, 0.1)
            self._parameters.get_parameter("imitation").set_value(imitation)
            self._set_flaneur_parameters(ACTIVE_FLANEUR_PARAMETERS)

    def _set_flaneur_parameters(self, parameters_dict):
        for name, value in parameters_dict.iteritems():
            self._parameters.get_parameter("flaneur_%s" % name).set_value(value)
