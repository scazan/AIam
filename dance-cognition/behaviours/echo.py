# echo: Observe and repeat moves, one by one, like an echo.

import behaviour
import interpret
from states import *

class Behaviour(behaviour.Behaviour):
    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self.interpreter.add_callback(interpret.MOVE, self._move_observed)
        self._last_observed_move = None

    def on_enabled(self):
        self.motion_controller.initiate_movement_to(InState(self.MC))

    def process_input(self, input_position, time_increment):
        behaviour.Behaviour.process_input(self, input_position, time_increment)
        if self._last_observed_move:
            destination_cursor = InState(self._last_observed_move["destination_state"])
            if self.motion_controller.can_move_to(destination_cursor):
                self.motion_controller.initiate_movement_to(
                    destination_cursor,
                    self._last_observed_move["duration"])
                self._last_observed_move = None

    def _move_observed(self, source_state, destination_state, duration):
        self._last_observed_move = {
            "destination_state": destination_state,
            "duration": duration}
