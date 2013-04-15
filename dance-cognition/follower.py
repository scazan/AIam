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
        intersection = self._cross_product(v - pos1, pos2 - pos1) + pos1
        relative_position = (intersection - pos1).mag() / (pos2 - pos1).mag()
        relative_position = self._clamp(relative_position, 0, 1)
        return InterStatePosition(input_state, output_state, relative_position)

    def _cross_product(self, v1, v2):
        c = numpy.cross(v1.v, v2.v)
        return Vector(3, c)

    def _clamp(self, v, v_min, v_max):
        return max(min(v, v_max), v_min)
