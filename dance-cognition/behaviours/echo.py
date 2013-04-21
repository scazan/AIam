from vector import *
from states import state_machine, InterStatePosition
import behaviour

SPATIAL_THRESHOLD = 0.25
TEMPORAL_THRESHOLD = 1.0

class Behaviour(behaviour.Behaviour):
    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self._state_hypothesis = None
        self._observed_state = None
        self._output_queue = []
        self._output_transition = None
        self._time = 0.0

    def process_input(self, input_position, time_increment):
        self._time += time_increment
        self._input_position = input_position
        nearest_state = self._nearest_state()
        if nearest_state and self._distance_to_state(nearest_state) < SPATIAL_THRESHOLD:
            if nearest_state == self._state_hypothesis:
                self._duration_in_state += time_increment
                if self._duration_in_state > TEMPORAL_THRESHOLD:
                    self._state_observed(nearest_state)
            else:
                self._state_hypothesis = nearest_state
                self._duration_in_state = 0

        if self._output_transition:
            self._output_transition_time += time_increment
            if self._output_transition_time > self._output_transition["duration"]:
                self._output_transition = None

        if not self._output_transition and len(self._output_queue) > 0:
            self._output_transition = self._output_queue.pop(0)
            self._output_transition_time = 0.0

    def _nearest_state(self):
        return min(state_machine.states.values(), key=lambda state: self._distance_to_state(state))

    def _distance_to_state(self, state):
        return (state.position - self._input_position).mag()

    def _state_observed(self, new_observed_state):
        if self._observed_state and self._is_valid_transition(self._observed_state, new_observed_state):
            duration = self._time - self._observed_state_at_time
            self._transition_observed(self._observed_state, new_observed_state, duration)
        self._observed_state = new_observed_state
        self._observed_state_at_time = self._time

    def _is_valid_transition(self, source_state, destination_state):
        return destination_state in source_state.inputs + source_state.outputs

    def _transition_observed(self, source_state, destination_state, duration):
        self._output_queue.append({"source_state": source_state,
                                   "destination_state": destination_state,
                                   "duration": duration})

    def output(self):
        if self._output_transition:
            return InterStatePosition(
                self._output_transition["source_state"],
                self._output_transition["destination_state"],
                self._output_transition_time / self._output_transition["duration"])

    def observed_state(self):
        return self._observed_state
