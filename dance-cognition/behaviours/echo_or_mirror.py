from states import InterStatePosition
import behaviour
import interpret

MIRROR, ECHO, WAIT = range(3)

class Behaviour(behaviour.Behaviour):
    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self._mode = MIRROR

        # from echo
        self.interpreter.add_callback(interpret.MOVE, self._move_observed)
        self.interpreter.add_callback(interpret.STATE, self._state_observed)
        self._next_output_transition = None
        self._output_transition = None

        # from mirror
        self.interpreter.add_callback(interpret.LEAVING_CENTER, self._on_leaving_center)
        self.interpreter.add_callback(interpret.ENTERING_CENTER, self._on_entering_center)
        self._target_state = None
        self._center_output = InterStatePosition(
            self._state_machine.states["MC"],
            self._state_machine.states["MLB"],
            0.0)
        self._output = self._center_output
        self._in_center = False

    def process_input(self, input_position, time_increment):
        if self._mode == MIRROR:
            if self._output_transition:
                self._output_transition_time += time_increment
                if self._output_transition_time > self._output_transition["duration"]:
                    self._output_transition = None

            if not self._output_transition and self._next_output_transition:
                self._output_transition = self._next_output_transition
                self._next_output_transition = None
                self._output_transition_time = 0.0

        elif self._mode == WAIT:

    # from echo
    def _move_observed(self, source_state, destination_state, duration):
        self._next_output_transition = {
            "source_state": source_state,
            "destination_state": destination_state,
            "duration": duration}

    def output(self):
        if self._output_transition:
            return InterStatePosition(
                self._output_transition["source_state"],
                self._output_transition["destination_state"],
                self._output_transition_time / self._output_transition["duration"])

    def _state_observed(self, state):
        if self._mode == MIRROR and state != self.MC:
            self._mode = WAIT

    # from mirror
    def _select_transition(self, input_position):
        assumed_target_state = self.interpreter.guess_target_state(input_position, self.MC)
        self._output = InterStatePosition(self.MC, assumed_target_state, 0.0)
