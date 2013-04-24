# TODO:
# add "free" state, used by sync/mirror
# add method initiate_free_movement (around resting state), used by sync/mirror
# add method for setting cursor within free movement, used by sync/mirror
# add method leave_free_movement. this will be used by echo_or_mirror when detecting that partner is away from center.
# add callback for entering resting state (from free movement). this will be used by echo_or_mirror to potentially start new move.

from states import InterStatePosition

class Behaviour:
    def __init__(self, state_machine, interpreter):
        self._state_machine = state_machine
        self.interpreter = interpreter
        self.MC = state_machine.states["MC"]
        self._resting_state = self.MC
        self._performing_move = False

    def process_input(self, input_position, time_increment):
        if self._performing_move:
            self._move_time += time_increment
            if self._move_time > self._move_duration:
                self._performing_move = False
                self._resting_state = self._destination_state

    def start_move_to(self, destination_state, duration):
        assert self.can_move_to(destination_state)
        self._destination_state = destination_state
        self._move_time = 0.0
        self._move_duration = duration
        self._performing_move = True

    def can_move_to(self, destination_state):
        return not self._performing_move and \
            destination_state in self._resting_state.outputs + self._resting_state.inputs

    def output(self):
        if self._performing_move:
            return InterStatePosition(
                self._resting_state,
                self._destination_state,
                self._move_time / self._move_duration)
        else:
            # TODO: optimize (?)
            return InterStatePosition(
                self._resting_state,
                (self._resting_state.outputs + self._resting_state.inputs)[0],
                0.0)
