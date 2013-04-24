# mirror: Mirrors the dynamics of the input, like sync, but also tries to mirror the move itself.
# Works best when input is near center.

from states import InterStatePosition
from behaviours import sync

class Behaviour(sync.Behaviour):
    def _select_transition(self, input_position):
        assumed_target_state = self.interpreter.guess_target_state(input_position, self.MC)
        self._output = InterStatePosition(self.MC, assumed_target_state, 0.0)
