import behaviour
import interpret
import random
from states import *
import motion_controller

class Behaviour(behaviour.Behaviour):
    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self.interpreter.add_callback(interpret.MOVE, self._move_observed)
        self._last_observed_destination = None

    def on_enabled(self):
        self.motion_controller.initiate_movement_to(InState(self.MC))

    def process_input(self, input_position, time_increment):
        behaviour.Behaviour.process_input(self, input_position, time_increment)
        if self.motion_controller.get_mode() == motion_controller.IDLE:
            if self._last_observed_destination and \
               self.motion_controller.can_move_to(self._last_observed_destination):
                print "echoing"
                self.motion_controller.initiate_movement_to(
                    self._last_observed_destination,
                    self._last_observed_duration)
                self._last_observed_destination = None
            else:
                print "improvising"
                self._initiate_random_movement()

    def _move_observed(self, source_state, destination_state, duration):
        self._last_observed_destination = InState(destination_state)
        self._last_observed_duration = duration

    def _initiate_random_movement(self):
        cursor = self.motion_controller.get_cursor()
        if cursor.is_in_state():
            destination_state = random.choice(cursor.state.inputs + cursor.state.outputs)
        elif cursor.is_between_states():
            destination_state = random.choice([cursor.source_state, cursor.destination_state])
        self.motion_controller.initiate_movement_to(InState(destination_state))
