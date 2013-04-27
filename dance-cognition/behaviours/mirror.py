# mirror: Mirrors the dynamics of the input, like sync, but also tries to mirror the move itself.
# Works best when input is near center.

from behaviours import sync

class Behaviour(sync.Behaviour):
    def _select_target_state(self, input_position):
        assumed_target_state = self.interpreter.guess_target_state(
            input_position, self.motion_controller.MC)
        self._target_state = assumed_target_state

