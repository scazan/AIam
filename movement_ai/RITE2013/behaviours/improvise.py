import behaviour
import motion_controller
import random
from states import *

class Behaviour(behaviour.Behaviour):
    def on_enabled(self):
        self._initiate_random_movement()

    def process_input(self, input_position, time_increment):
        if self.motion_controller.get_mode() == motion_controller.IDLE:
            self._initiate_random_movement()

    def _initiate_random_movement(self):
        cursor = self.motion_controller.get_cursor()
        if cursor.is_in_state():
            destination_state = random.choice(cursor.state.inputs + cursor.state.outputs)
        elif cursor.is_between_states():
            destination_state = random.choice([cursor.source_state, cursor.destination_state])
        self.motion_controller.initiate_movement_to(InState(destination_state))
