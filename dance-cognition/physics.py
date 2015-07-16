import numpy
import random
import math

class FrictionConstrainer:
    def __init__(self, balance_detector):
        self._balance_detector = balance_detector
        self._supporting_vertex_locked_position = None
        self._supporting_vertex_index = None

    def constrain(self, vertices):
        if self._supporting_vertex_locked_position is None:
            result = vertices
        else:
            result = self._stabilize_around_supporting_vertex(vertices)
        new_supporting_vertex_index = self._balance_detector.identify_supporting_vertex(vertices)
        if new_supporting_vertex_index != self._supporting_vertex_index:
            self._supporting_vertex_index = new_supporting_vertex_index
            self._supporting_vertex_locked_position = result[self._supporting_vertex_index]
        return result

    def _stabilize_around_supporting_vertex(self, unconstrained_vertices):
        unconstrained_supporting_vertex = unconstrained_vertices[self._supporting_vertex_index]
        translation = self._supporting_vertex_locked_position - unconstrained_supporting_vertex
        return [vertex + translation for vertex in unconstrained_vertices]

class BalanceDetector:
    def identify_supporting_vertex(self, vertices):
        return self._lowest_vertex(vertices)

    def _lowest_vertex(self, vertices):
        return min(
            range(len(vertices)),
            key=lambda index: vertices[index][1])
        
class FloorConstrainer:
    def __init__(self):
        self._floor_y = 0

    def constrain(self, vertices):
        bottom_y = min([vertex[1] for vertex in vertices])
        offset = numpy.zeros(len(vertices[0]))
        offset[1] = self._floor_y - bottom_y
        return [vertex + offset for vertex in vertices]

class RandomSlide:
    def __init__(self, speed):
        angle = random.uniform(0, math.pi*2)
        self._translation_increment = numpy.array(
            [math.cos(angle), 0, math.sin(angle)]) * speed
        self._translation = numpy.zeros(3)

    def constrain(self, vertices):
        self._translation += self._translation_increment
        return [vertex + self._translation for vertex in vertices]
