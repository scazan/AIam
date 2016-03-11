import numpy
import sklearn.neighbors

NUM_NEIGHBORS = 100

class Flaneur:
    def __init__(self, map_points,
                 translational_speed=0.2,
                 directional_speed=0.05,
                 look_ahead_distance=0.1):
        self.map_points = map_points
        self.translational_speed = translational_speed
        self.directional_speed = directional_speed
        self.look_ahead_distance = look_ahead_distance
        self._n_dimensions = len(map_points[0])
        self._nearest_neighbor_classifier = sklearn.neighbors.KNeighborsClassifier(
            n_neighbors=NUM_NEIGHBORS, weights='uniform')
        self._nearest_neighbor_classifier.fit(map_points, range(len(map_points)))
        self.reset()

    def reset(self):
        self._position = numpy.random.random(size=self._n_dimensions)
        self._direction = None
        self._neighbors = []
        self._neighbors_center = None

    def get_position(self):
        return self._position

    def get_neighbors(self):
        return self._neighbors

    def get_neighbors_center(self):
        return self._neighbors_center

    def proceed(self, time_increment):
        self._time_increment = time_increment
        self._process_direction()
        self._move_in_direction()

    def _process_direction(self):
        position_ahead = self._get_position_ahead()
        distances_list, points_indices_list = self._nearest_neighbor_classifier.kneighbors(
            position_ahead)
        distances = distances_list[0]
        points_indices = points_indices_list[0]
        self._neighbors = [self.map_points[index] for index in points_indices]
        self._neighbors_center = numpy.mean(self._neighbors, 0)
        target_direction = self._neighbors_center - self._position
        if self._direction is None:
            self._direction = target_direction
        else:
            self._move_towards_direction(target_direction)

    def _get_position_ahead(self):
        if self._direction is None:
            return self._position
        else:
            norm = numpy.linalg.norm(self._direction)
            if norm > 0:
                return self._position + self._direction / norm * self.look_ahead_distance
            else:
                return self._position

    def _move_towards_direction(self, target_direction):
        difference = target_direction - self._direction
        norm = numpy.linalg.norm(difference)
        if norm > 0:
            self._direction += difference / norm * min(self.directional_speed * self._time_increment, 1)

    def _move_in_direction(self):
        norm = numpy.linalg.norm(self._direction)
        if norm > 0:
            self._position += self._direction / norm * self._time_increment * self.translational_speed
