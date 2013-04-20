from vector import *
from states import InterStatePosition
from behaviours import sync

class Behaviour(sync.Behaviour):
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
