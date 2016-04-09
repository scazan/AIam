from flaneur import Flaneur
from parameters import *
from event import Event
from dimensionality_reduction.behavior import Behavior

class FlaneurParameters(Parameters):
    def __init__(self):
        Parameters.__init__(self)
        self.add_parameter("translational_speed", type=float, default=.6,
                           choices=ParameterFloatRange(0., 3.))
        self.add_parameter("directional_speed", type=float, default=1.1,
                           choices=ParameterFloatRange(0., 3.))
        self.add_parameter("look_ahead_distance", type=float, default=.2,
                           choices=ParameterFloatRange(0., 1.))

class FlaneurBehavior(Behavior):
    def __init__(self, experiment, parameters, map_points):
        self._experiment = experiment
        self._parameters = parameters
        parameters.add_listener(self._parameter_changed)
        self._flaneur = Flaneur(map_points)
        self._update_flaneur_from_parameters()

    def _update_flaneur_from_parameters(self):
        for parameter in self._parameters:
            self._update_flaneur_from_parameter(parameter)

    def _parameter_changed(self, parameter):
        self._update_flaneur_from_parameter(parameter)

    def _update_flaneur_from_parameter(self, parameter):
        setattr(self._flaneur, parameter.name, parameter.value())

    def proceed(self, time_increment):
        self._flaneur.proceed(time_increment)
        self._experiment.send_event_to_ui(
            Event(Event.NEIGHBORS_CENTER, self._flaneur.get_neighbors_center()))

    def get_reduction(self):
        normalized_position = self._flaneur.get_position()
        return self._experiment.student.unnormalize_reduction(normalized_position)

    def set_reduction(self, reduction):
        pass
