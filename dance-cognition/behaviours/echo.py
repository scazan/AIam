# echo: Observe and repeat moves, one by one, like an echo.

from states import InterStatePosition
import behaviour
import interpret

class Behaviour(behaviour.Behaviour):
    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self.interpreter.add_callback(interpret.MOVE, self._move_observed)
        self._next_output_transition = None
        self._output_transition = None

    def process_input(self, input_position, time_increment):
        if self._output_transition:
            self._output_transition_time += time_increment
            if self._output_transition_time > self._output_transition["duration"]:
                self._output_transition = None

        if not self._output_transition and self._next_output_transition:
            self._output_transition = self._next_output_transition
            self._next_output_transition = None
            self._output_transition_time = 0.0

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
