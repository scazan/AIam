# echo: Observe and repeat moves, one by one, like an echo.

from states import InterStatePosition
import behaviour
import interpret

class Behaviour(behaviour.Behaviour):
    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self.interpreter.add_callback(interpret.MOVE, self._move_observed)
        self._last_observed_move = None
        self._current_output_move = None

    def process_input(self, input_position, time_increment):
        if self._current_output_move:
            self._current_output_move_time += time_increment

        if (not self._current_output_move and self._last_observed_move) or \
           (self._current_output_move and
            self._last_observed_move and
            self._current_output_move["destination_state"] == self._last_observed_move["source_state"]):
            self._current_output_move = self._last_observed_move
            self._current_output_move_time = 0.0

    def _move_observed(self, source_state, destination_state, duration):
        self._last_observed_move = {
            "source_state": source_state,
            "destination_state": destination_state,
            "duration": duration}

    def output(self):
        if self._current_output_move:
            return InterStatePosition(
                self._current_output_move["source_state"],
                self._current_output_move["destination_state"],
                min(1.0, self._current_output_move_time / self._current_output_move["duration"]))
