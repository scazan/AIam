from parameters import *
from navigator import Navigator, PathFollower
import interpolation
import dynamics as dynamics_module
import numpy

class ImproviseParameters(Parameters):
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

class Improvise:
    def __init__(self, experiment, params, preferred_location, on_changed_path=None):
        self.experiment = experiment
        self.params = params
        self._preferred_location = preferred_location
        self._path = None
        self._path_follower = None
        self._on_changed_path = on_changed_path
        self._navigator = Navigator(
            map_points=experiment.student.normalized_observed_reductions)
        if preferred_location is not None:
            self._navigator.set_preferred_location(preferred_location)
        self._reduction = None

    def set_reduction(self, reduction):
        self._reduction = reduction

    def select_next_move(self):
        found_non_empty_path = False
        while not found_non_empty_path:
            path_segments = self._generate_path()
            self._path = self._interpolate_path(path_segments)
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
        return self._navigator.generate_path(
            departure = self._departure(),
            num_segments = self.params.num_segments,
            novelty = self.params.novelty * self.experiment.args.max_novelty,
            extension = self.params.extension,
            location_preference = self.params.location_preference)

    def _departure(self):
        if self._reduction is None:
            if self._preferred_location is not None:
                return self._preferred_location
            else:
                unnormalized_departure = numpy.array([.5] * self.experiment.args.num_components)
        else:
            unnormalized_departure = self._reduction
        return self.experiment.student.normalize_reduction(unnormalized_departure)

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

    def get_reduction(self):
        normalized_position = self._path_follower.current_position()
        return self.experiment.student.unnormalize_reduction(normalized_position)

    def path(self):
        return self._path
