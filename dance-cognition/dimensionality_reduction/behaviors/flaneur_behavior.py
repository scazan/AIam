from flaneur import Flaneur
from parameters import *

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
    def __init__(self, experiment, params):
        self._experiment = experiment
        self.params = params
        params.add_listener(self._parameter_changed)
        self._flaneur = Flaneur(map_points=experiment.student.normalized_observed_reductions)

    def _parameter_changed(self, parameter):
        setattr(self._flaneur, parameter.name, parameter.value())

    def proceed(self, time_increment):
        self._flaneur.proceed(time_increment)

    def get_reduction(self):
        normalized_position = self._flaneur.get_position()
        return self._experiment.student.unnormalize_reduction(normalized_position)

    def set_reduction(self, reduction):
        pass
