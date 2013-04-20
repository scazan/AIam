from vector import *
from states import InterStatePosition
import random

SPATIAL_THRESHOLD = 0.04
TEMPORAL_THRESHOLD = 0.2

class Behaviour:
    def __init__(self, state_machine):
        self._state_machine = state_machine
        self._target_state = None
        self._center_output = InterStatePosition(
            state_machine.states["MC"],
            state_machine.states["MLB"],
            0.0)
        self._sensed_center = Vector3d(0.0, 0.0, 0.0)
        self._in_center = True
        self._duration_in_center = 0

    def process_input(self, input_position, time_increment):
        self._sensed_center += (input_position - self._sensed_center) * \
                               0.2 * min(time_increment, 1.0)
        sensed_input_position = input_position - self._sensed_center
        amplitude = max(sensed_input_position.mag() - SPATIAL_THRESHOLD, 0.0)
        self._sensed_center = max(self._sensed_center, amplitude)

        input_in_center = sensed_input_position.mag() < SPATIAL_THRESHOLD
        if self._in_center:
            if input_in_center:
                self._duration_in_center += time_increment
            else:
                if self._duration_in_center >= TEMPORAL_THRESHOLD:
                    self._select_transition(sensed_input_position)
                self._in_center = False
        else:
            if input_in_center:
                self._in_center = True
                self._duration_in_center = 0

        if self._in_center:
            self._output = self._center_output
        else:
            self._output.relative_position = amplitude

    def output(self):
        return self._output

    def _select_transition(self, input_position):
        mc = self._state_machine.states["MC"]

        min_distance = None
        for output_state in mc.inputs + mc.outputs:
            inter_state_position = self._perpendicular_inter_state_position(input_position, mc, output_state)
            distance = (input_position - self._state_machine.inter_state_to_euclidian_position(inter_state_position)).mag()
            if min_distance is None or distance < min_distance:
                nearest_output_state = output_state
                min_distance = distance

        self._output = InterStatePosition(mc, nearest_output_state, 0.0)

    def _perpendicular_inter_state_position(self, v, input_state, output_state):
        pos1 = input_state.position
        pos2 = output_state.position
        intersection = self._perpendicular(pos1, pos2, v)
        relative_position = (intersection - pos1).mag() / (pos2 - pos1).mag()
        relative_position = self._clamp(relative_position, 0, 1)
        return InterStatePosition(input_state, output_state, relative_position)

    def _perpendicular(self, p1, p2, q):
        u = p2 - p1
        pq = q - p1
        w2 = pq - u * (dot_product(pq, u) / pow(u.mag(), 2))
        return q - w2

    def _clamp(self, v, v_min, v_max):
        return max(min(v, v_max), v_min)