from vector import *
from states import InterStatePosition

SPEED = 1.0
THRESHOLD = 0.01

class Behaviour:
    def __init__(self, state_machine):
        self._state_machine = state_machine
        self._inter_state_position = None

    def process_input(self, input_position, time_increment):
        self._time_increment = time_increment
        desired_inter_state_position = self._nearest_inter_state_position(input_position)
        if self._inter_state_position is None:
            self._inter_state_position = desired_inter_state_position
        elif self._inter_state_position.source_state == desired_inter_state_position.source_state and \
                self._inter_state_position.destination_state == desired_inter_state_position.destination_state:
            self._move_along_transition_towards_relative_position(
                desired_inter_state_position.relative_position)
        else:
            nearest_state = self._nearest_transition_state(desired_inter_state_position)
            self._move_along_transition_towards_state(nearest_state)

            euclidian = self._state_machine.inter_state_to_euclidian_position(self._inter_state_position)
            if (euclidian - nearest_state.position).mag() < THRESHOLD:
                self._select_best_transition(input_position, nearest_state)

    def output(self):
        return self._inter_state_position

    def _move_along_transition_towards_relative_position(self, desired_relative_position):
        allowed_relative_distance = self._time_increment * SPEED / self._inter_state_position.transition_length
        actual_relative_distance = abs(
            desired_relative_position - self._inter_state_position.relative_position)
        if allowed_relative_distance >= actual_relative_distance:
            new_relative_position = desired_relative_position
        else:
            if desired_relative_position > self._inter_state_position.relative_position:
                sign = 1
            else:
                sign = -1
            new_relative_position = self._inter_state_position.relative_position + sign * \
                allowed_relative_distance
        new_relative_position = self._clamp(new_relative_position, 0, 1)
        self._inter_state_position.relative_position = new_relative_position

    def _move_along_transition_towards_state(self, target_state):
        if target_state == self._inter_state_position.source_state:
            desired_relative_position = 0.0
        elif target_state == self._inter_state_position.destination_state:
            desired_relative_position = 1.0
        else:
            raise Exception("unexpected target_state")
        self._move_along_transition_towards_relative_position(desired_relative_position)

    def _nearest_transition_state(self, target_inter_state_position):
        target_euclidian = self._state_machine.inter_state_to_euclidian_position(target_inter_state_position)
        distance_from_source = (
            target_euclidian - self._inter_state_position.source_state.position).mag()
        distance_from_destination = (
            target_euclidian - self._inter_state_position.destination_state.position).mag()
        if distance_from_source < distance_from_destination:
            return self._inter_state_position.source_state
        else:
            return self._inter_state_position.destination_state

    def _select_best_transition(self, v, input_state):
        min_distance = None
        for output_state in input_state.inputs + input_state.outputs:
            inter_state_position = self._perpendicular_inter_state_position(v, input_state, output_state)
            distance = (v - self._state_machine.inter_state_to_euclidian_position(inter_state_position)).mag()
            if min_distance is None or distance < min_distance:
                nearest_output_state = output_state
                min_distance = distance
        self._inter_state_position = InterStatePosition(input_state, nearest_output_state, 0.0)

    def _nearest_inter_state_position(self, v):
        min_distance = None
        for input_state, output_state in self._state_machine.transitions:
            inter_state_position = self._perpendicular_inter_state_position(v, input_state, output_state)
            distance = (v - self._state_machine.inter_state_to_euclidian_position(inter_state_position)).mag()
            if min_distance is None or distance < min_distance:
                nearest_inter_state_position = inter_state_position
                min_distance = distance
        return nearest_inter_state_position

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
