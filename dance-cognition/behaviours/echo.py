# echo: Observe and repeat moves, one by one, like an echo.

import behaviour
import interpret
from states import *

class Behaviour(behaviour.Behaviour):
    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self.interpreter.add_callback(interpret.MOVE, self._move_observed)
        self._last_observed_destination = None

    def on_enabled(self):
        self.motion_controller.initiate_movement_to(InState(self.MC))

    def process_input(self, input_position, time_increment):
        behaviour.Behaviour.process_input(self, input_position, time_increment)
        if self._last_observed_destination and \
           self.motion_controller.can_move_to(self._last_observed_destination):
            self.motion_controller.initiate_movement_to(
                self._last_observed_destination,
                self._last_observed_duration)
            self._last_observed_destination = None

    def _move_observed(self, source_state, destination_state, duration):
        self._last_observed_destination = InState(destination_state)
        self._last_observed_duration = duration
