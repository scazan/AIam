# idle: Sway near center

import behaviour
import motion_controller
import random
from states import *

MAGNITUDE = 0.1

class Behaviour(behaviour.Behaviour):
    def on_enabled(self):
        self._initiate_sway_in()

    def process_input(self, input_position, time_increment):
        if self.motion_controller.get_mode() == motion_controller.IDLE:
            self._idle()

    def _idle(self):
        if self.motion_controller.get_cursor().is_in_state() and \
           self.motion_controller.get_cursor().state == self.MC:
            self._initiate_sway_out()
        else:
            self._initiate_sway_in()

    def _initiate_sway_out(self):
        destination_state = random.choice(self.MC.inputs + self.MC.outputs)
        self.motion_controller.initiate_movement_to(
            BetweenStates(
                self.MC, destination_state, MAGNITUDE))

    def _initiate_sway_in(self):
        self.motion_controller.initiate_movement_to(InState(self.MC))
