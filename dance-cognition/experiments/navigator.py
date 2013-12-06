import sklearn.neighbors
import numpy

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

