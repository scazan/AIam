import sklearn.neighbors
import numpy
import copy
from scipy.interpolate import InterpolatedUnivariateSpline

class Navigator:
    def __init__(self, map_points):
        self.map_points = map_points
        self._n_dimensions = len(map_points[0])
        self._nearest_neighbor_classifier = sklearn.neighbors.KNeighborsClassifier(
            n_neighbors=1, weights='uniform')
        self._nearest_neighbor_classifier.fit(map_points, map_points)

    def generate_path(self, departure, destination, num_segments):
        self._departure = departure
        self._destination = destination
        self._num_segments = num_segments
        self._segments = [departure]
        for n in range(num_segments-1):
            self._add_path_segment(n)
        return self._segments

    def interpolate_path(self, points, resolution):
        numpy_points = numpy.array(points)
        unclamped_path = numpy.column_stack(
                [self._spline_interpolation_1d(numpy_points[:,n], resolution)
                 for n in range(self._n_dimensions)])
        return list(self._clamp_path(unclamped_path, numpy_points))

    def _spline_interpolation_1d(self, points, resolution):
        x = numpy.arange(0., 1., 1./len(points))
        x_new = numpy.arange(0., 1., 1./resolution)
        curve = InterpolatedUnivariateSpline(x, points)
        return curve(x_new)

    def _clamp_path(self, path, interval_points):
        mins = [min(interval_points[:,n]) for n in range(self._n_dimensions)]
        maxs = [max(interval_points[:,n]) for n in range(self._n_dimensions)]
        return path[self._first_index_in_interval(path, mins, maxs):
                        self._last_index_in_interval(path, mins, maxs)]

    def _first_index_in_interval(self, path, mins, maxs):
        i = 0
        while i < len(path):
            if self._in_interval(path[i], mins, maxs):
                return i
            i += 1

    def _last_index_in_interval(self, path, mins, maxs):
        i = len(path) - 1
        while i >= 0:
            if self._in_interval(path[i], mins, maxs):
                return i
            i -= 1

    def _in_interval(self, point, mins, maxs):
        for n in range(self._n_dimensions):
            if point[n] < mins[n] or point[n] > maxs[n]:
                return False
        return True

    def _add_path_segment(self, n):
        previous_point = self._segments[-1]
        next_point_straightly = previous_point + (self._destination - previous_point) \
            / (self._num_segments - n - 1)
        next_point_in_map = self._nearest_neighbor_classifier.predict(
            next_point_straightly)[0]
        if not numpy.array_equal(next_point_in_map, previous_point):
            self._segments.append(next_point_in_map)


class constant_envelope:
    def envelope(self, x):
        return 1.

class SymmetricalEnvelope:
    def envelope(self, x):
        if x < .5:
            return self.rising_envelope(x*2)
        else:
            return self.rising_envelope((1-x) * 2)

class exponential_envelope(SymmetricalEnvelope):
    _min_relative_velocity = .1
    _slope = 3.

    def rising_envelope(self, x):
        return self._min_relative_velocity + (1 - self._min_relative_velocity) * pow(x, self._slope)

class PathFollower:
    def __init__(self, path, velocity, envelope="constant"):
        self._path = path
        self._desired_average_velocity = velocity
        velocity_envelope = eval("%s_envelope" % envelope)()
        self._velocity_correction = 1.
        if envelope != "constant":
            self._velocity_correction = \
                self._estimate_duration(constant_envelope()) / \
                self._estimate_duration(velocity_envelope)
        self._velocity_envelope = velocity_envelope
        self._restart()

    def _restart(self):
        self._position = self._path[0]
        self._remaining_path = copy.copy(self._path)
        self._activate_next_path_strip()

    def _estimate_duration(self, velocity_envelope):
        self._velocity_envelope = velocity_envelope
        self._restart()
        duration = 0.
        while not self.reached_destination():
            duration += self.proceed()
        return duration

    def proceed(self, max_time_to_process=None):
        self._time_processed = 0.
        self._max_time_to_process = max_time_to_process
        while (self._max_time_to_process is None or self._max_time_to_process > 0) \
                and not self.reached_destination():
            self._process_within_state()
        return self._time_processed

    def current_position(self):
        return self._position

    def _process_within_state(self):
        if self._reached_path_strip_destination():
            self._remaining_path.pop(0)
            self._activate_next_path_strip()
        else:
            self._move_along_path_strip()

    def reached_destination(self):
        return len(self._remaining_path) <= 1

    def _reached_path_strip_destination(self):
        return self._travel_time_in_strip >= self._current_strip_duration

    def _activate_next_path_strip(self):
        if len(self._remaining_path) >= 2:
            self._current_strip_departure = self._remaining_path[0]
            self._current_strip_destination = self._remaining_path[1]
            self._current_strip_duration = self._current_strip_distance() / \
                self._current_strip_velocity()
            self._travel_time_in_strip = 0.0

    def _current_strip_distance(self):
        return numpy.linalg.norm(self._current_strip_destination - self._current_strip_departure)

    def _current_strip_velocity(self):
        return self._velocity_envelope.envelope((self._relative_cursor())) \
            * self._desired_average_velocity \
            / self._velocity_correction

    def _relative_cursor(self):
        return 1 - len(self._remaining_path) / float(len(self._path))

    def _move_along_path_strip(self):
        remaining_time_in_strip = self._current_strip_duration - self._travel_time_in_strip
        if self._max_time_to_process is None:
            duration_to_move = remaining_time_in_strip
        else:
            duration_to_move = min(self._max_time_to_process, remaining_time_in_strip)
        self._position = self._current_strip_departure + \
            (self._current_strip_destination - self._current_strip_departure) * \
            self._travel_time_in_strip / (self._current_strip_duration)
        self._travel_time_in_strip += duration_to_move
        self._time_processed += duration_to_move
        if self._max_time_to_process is not None:
            self._max_time_to_process -= duration_to_move
