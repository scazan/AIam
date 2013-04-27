# echo: Observe and repeat moves, one by one, like an echo.

import behaviour
import interpret

class Behaviour(behaviour.Behaviour):
    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self.interpreter.add_callback(interpret.MOVE, self._move_observed)
        self._last_observed_move = None

    def process_input(self, input_position, time_increment):
        behaviour.Behaviour.process_input(self, input_position, time_increment)
        if self._last_observed_move and \
           self.can_move_to(self._last_observed_move["destination_state"]):
            self.initiate_movement_to(
                self._last_observed_move["destination_state"],
                self._last_observed_move["duration"])

    def _move_observed(self, source_state, destination_state, duration):
        self._last_observed_move = {
            "destination_state": destination_state,
            "duration": duration}
