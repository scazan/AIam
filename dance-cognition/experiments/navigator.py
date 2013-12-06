import sklearn.neighbors
import numpy
import copy

class Navigator:
    def __init__(self, map_points):
        self.map_points = map_points
        self._nearest_neighbor_classifier = sklearn.neighbors.KNeighborsClassifier(
            n_neighbors=1, weights='uniform')
        self._nearest_neighbor_classifier.fit(map_points, map_points)

    def generate_path(self, departure, destination, resolution):
        self._departure = departure
        self._destination = destination
        self._resolution = resolution
        self._path = [departure]
        for n in range(resolution-1):
            self._add_path_segment(n)
        return self._path

    def _add_path_segment(self, n):
        previous_point = self._path[-1]
        next_point_straightly = previous_point + (self._destination - previous_point) \
            / (self._resolution - n - 1)
        next_point_in_map = self._nearest_neighbor_classifier.predict(
            next_point_straightly)[0]
        if not numpy.array_equal(next_point_in_map, previous_point):
            self._path.append(next_point_in_map)

class PathFollower:
    def __init__(self, path, duration):
        self._duration = duration
        self._value = path[0]
        self._path_strip_duration = duration / len(path)
        self._remaining_path = copy.copy(path)
        self._activate_next_path_strip()

    def proceed(self, time_increment):
        self._time_to_process = time_increment
        while self._time_to_process > 0 and not self.reached_destination():
            self._process_within_state()

    def get_value(self):
        return self._value

    def _process_within_state(self):
        if self._reached_path_strip_destination():
            self._remaining_path.pop(0)
            self._activate_next_path_strip()
        else:
            self._move_along_path_strip()

    def reached_destination(self):
        return len(self._remaining_path) <= 1

    def _reached_path_strip_destination(self):
        return self._travel_time_in_strip >= self._path_strip_duration

    def _activate_next_path_strip(self):
        if len(self._remaining_path) >= 2:
            self._current_strip_departure = self._remaining_path[0]
            self._current_strip_destination = self._remaining_path[1]
            self._travel_time_in_strip = 0.0
            
    def _move_along_path_strip(self):
        remaining_time_in_strip = self._path_strip_duration - self._travel_time_in_strip
        duration_to_move = min(self._time_to_process, remaining_time_in_strip)
        self._value = self._current_strip_departure + \
            (self._current_strip_destination - self._current_strip_departure) * \
            self._travel_time_in_strip / (self._path_strip_duration)
        self._travel_time_in_strip += duration_to_move
        self._time_to_process -= duration_to_move
