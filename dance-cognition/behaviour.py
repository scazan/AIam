# TODO:
# add method leave_free_movement. this will be used by echo_or_mirror when detecting that partner is away from center.
# add callback for entering resting state (from free movement). this will be used by echo_or_mirror to potentially start new move.

from states import state_machine, MC

class Behaviour:
    def __init__(self, interpreter, motion_controller):
        self.interpreter = interpreter
        self.motion_controller = motion_controller
        self.MC = state_machine.states[MC]
        self.enabled = True

    def process_input(self, input_position, time_increment):
        self._time_increment = time_increment
