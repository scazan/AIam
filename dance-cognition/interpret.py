from states import state_machine
from sensory_adaptation import SensoryAdapter

SPATIAL_THRESHOLD = 0.25
TEMPORAL_THRESHOLD = 1.0

CENTER_SPATIAL_THRESHOLD = 0.04
CENTER_TEMPORAL_THRESHOLD = 0.2

MOVE, STATE, LEAVING_CENTER, ENTERING_CENTER = range(4)

class Interpreter:
    def __init__(self):
        self._state_hypothesis = None
        self._observed_state = None
        self._sensory_adapter = SensoryAdapter(0.1)
        self._in_center = True
        self._duration_in_center = 0
        self._time = 0.0
        self._callbacks = {
            MOVE: [],
            STATE: [],
            LEAVING_CENTER: [],
            ENTERING_CENTER: []
        }

    def add_callback(self, event, callback):
        self._callbacks[event].append(callback)

    def process_input(self, input_position, time_increment):
        self._time += time_increment
        self._detect_whether_leaving_or_entering_center(input_position, time_increment)
        self._detect_whether_state_changed(input_position, time_increment)

    def sensed_center(self):
        return self._sensory_adapter.sensed_center()

    def _detect_whether_leaving_or_entering_center(self, input_position, time_increment):
        sensed_input_position = self._sensory_adapter.process(input_position, time_increment)
        input_in_center = sensed_input_position.mag() < CENTER_SPATIAL_THRESHOLD
        if self._in_center:
            if input_in_center:
                self._duration_in_center += time_increment
            else:
                if self._duration_in_center >= CENTER_TEMPORAL_THRESHOLD:
                    self._fire_callbacks(LEAVING_CENTER, input_position)
                    self._in_center = False
        else:
            if input_in_center:
                self._in_center = True
                self._duration_in_center = 0
                self._fire_callbacks(ENTERING_CENTER, input_position)

    def _detect_whether_state_changed(self, input_position, time_increment):
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
