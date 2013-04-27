# sync: Mirrors the dynamics of the input. Works best when input is near center.

from states import InterStatePosition, MC, MLB
import random
import behaviour
import math
import interpret

class Behaviour(behaviour.Behaviour):
    max_amplitude = math.sqrt(2)

    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self.interpreter.add_callback(interpret.LEAVING_CENTER, self._on_leaving_center)
        self.interpreter.add_callback(interpret.ENTERING_CENTER, self._on_entering_center)
        self._target_state = None
        self._center_output = InterStatePosition(
            self._state_machine.states[MC],
            self._state_machine.states[MLB],
            0.0)
        self._output = self._center_output
        self._in_center = False

    def process_input(self, input_position, time_increment):
        if self._in_center:
            self._output = self._center_output
        else:
            amplitude = max((input_position - self.interpreter.sensed_center()).mag() -
                            interpret.CENTER_SPATIAL_THRESHOLD, 0.0) / self.max_amplitude
            self._output.relative_position = amplitude

    def output(self):
        return self._output

    def _on_leaving_center(self, input_position):
        self._select_transition(input_position)
        self._in_center = False

    def _on_entering_center(self, input_position):
        self._in_center = True

    def _select_transition(self, input_position):
        mc = self._state_machine.states[MC]
        target_state = random.choice(mc.inputs + mc.outputs)
        self._output = InterStatePosition(mc, target_state, 0.0)
