import behaviour
import interpret
import random
from states import *
import motion_controller

PASSIVITY_TIMEOUT = 3.0
SWAY_MAGNITUDE = 0.1

class Behaviour(behaviour.Behaviour):
    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self.interpreter.add_callback(interpret.MOVE, self._move_observed)
        self.interpreter.add_callback(interpret.ACTIVITY, self._observed_active)
        self.interpreter.add_passivity_callback(PASSIVITY_TIMEOUT, self._observed_passive)
        self._last_observed_destination = None
        self._idling = True

    # control logic

    def on_enabled(self):
        self.motion_controller.initiate_movement_to(InState(self.MC))

    def _observed_active(self):
        print "observed active"
        if self._can_echo():
            print "echoing"
            self._echo()
        if self._idling:
            print "stopped idling"
            self._idling = False

    def _observed_passive(self):
        print "observed passive"
        if not self._idling:
            print "idling"
            self._idling = True

    def process_input(self, input_position, time_increment):
        behaviour.Behaviour.process_input(self, input_position, time_increment)
        if self.motion_controller.get_mode() == motion_controller.IDLE:
            if self._idling:
                self._idle()
            elif self._can_echo():
                print "echoing"
                self._echo()
            else:
                print "improvising"
                self._initiate_random_movement()

    # echo

    def _can_echo(self):
        return self._last_observed_destination and \
            self.motion_controller.can_move_to(self._last_observed_destination)

    def _echo(self):
        self.motion_controller.initiate_movement_to(
            self._last_observed_destination,
            self._last_observed_duration)
        self._last_observed_destination = None

    def _move_observed(self, source_state, destination_state, duration):
        self._last_observed_destination = InState(destination_state)
        self._last_observed_duration = duration

    # improvise

    def _initiate_random_movement(self):
        cursor = self.motion_controller.get_cursor()
        if cursor.is_in_state():
            destination_state = random.choice(cursor.state.inputs + cursor.state.outputs)
        elif cursor.is_between_states():
            destination_state = random.choice([cursor.source_state, cursor.destination_state])
        self.motion_controller.initiate_movement_to(InState(destination_state))

    # idle

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
                self.MC, destination_state, SWAY_MAGNITUDE))

    def _initiate_sway_in(self):
        self.motion_controller.initiate_movement_to(InState(self.MC))
