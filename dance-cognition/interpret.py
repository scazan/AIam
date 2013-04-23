from states import state_machine

SPATIAL_THRESHOLD = 0.25
TEMPORAL_THRESHOLD = 1.0

MOVE, STATE = range(2)

class Interpreter:
    def __init__(self):
        self._state_hypothesis = None
        self._observed_state = None
        self._time = 0.0
        self._callbacks = {
            MOVE: [],
            STATE: []}

    def add_callback(self, event, callback):
        self._callbacks[event].append(callback)

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

    def _nearest_state(self):
        return min(state_machine.states.values(), key=lambda state: self._distance_to_state(state))

    def _distance_to_state(self, state):
        return (state.position - self._input_position).mag()

    def _is_valid_transition(self, source_state, destination_state):
        return destination_state in source_state.inputs + source_state.outputs

    def _state_observed(self, new_observed_state):
        if self._observed_state and self._is_valid_transition(self._observed_state, new_observed_state):
            duration = self._time - self._observed_state_at_time
            self._fire_callbacks(MOVE, self._observed_state, new_observed_state, duration)
        self._observed_state = new_observed_state
        self._observed_state_at_time = self._time
        self._fire_callbacks(STATE, new_observed_state)

    def _fire_callbacks(self, event, *args):
        for callback in self._callbacks[event]:
            callback(*args)
