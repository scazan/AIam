from vector import *
from states import state_machine
import behaviour

SPATIAL_THRESHOLD = 0.25
TEMPORAL_THRESHOLD = 1.0

class Behaviour(behaviour.Behaviour):
    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self._state_hypothesis = None
        self._observed_state = None

    def process_input(self, input_position, time_increment):
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

    def _nearest_state(self):
        return min(state_machine.states.values(), key=lambda state: self._distance_to_state(state))

    def _distance_to_state(self, state):
        return (state.position - self._input_position).mag()

    def _state_observed(self, state):
        self._observed_state = state

    def output(self):
        return None

    def observed_state(self):
        return self._observed_state
