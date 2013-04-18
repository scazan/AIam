import numpy
from vector import Vector
from states import InterStatePosition

class Follower:
    def __init__(self, state_machine):
        self.state_machine = state_machine
        self.inter_state_position = None

    def follow(self, v):
        self.inter_state_position = self._nearest_inter_state_position(v)

    def _nearest_inter_state_position(self, v):
        min_distance = None
        for transition in self.state_machine.transitions:
            inter_state_position = self._perpendicular_inter_state_position(v, transition)
            distance = (v - self.state_machine.inter_state_to_euclidian_position(inter_state_position)).mag()
            if min_distance is None or distance < min_distance:
                nearest_inter_state_position = inter_state_position
                min_distance = distance
        return nearest_inter_state_position

    def _perpendicular_inter_state_position(self, v, transition):
        input_state, output_state = transition
        pos1 = input_state.position
        pos2 = output_state.position
        intersection = self._perpendicular(pos1, pos2, v)
        relative_position = (intersection - pos1).mag() / (pos2 - pos1).mag()
        relative_position = self._clamp(relative_position, 0, 1)
        return InterStatePosition(input_state, output_state, relative_position)

    def _perpendicular(self, p1, p2, q):
        u = p2 - p1
        pq = q - p1
        w2 = pq - u * (self._dot_product(pq, u) / pow(u.mag(), 2))
        return q - w2

    def _dot_product(self, a, b):
        return numpy.dot(a.v, b.v)

    def _clamp(self, v, v_min, v_max):
        return max(min(v, v_max), v_min)
