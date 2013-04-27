# sync: Mirrors the dynamics of the input. Works best when input is near center.

from states import MC
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

    def process_input(self, input_position, time_increment):
        behaviour.Behaviour.process_input(self, input_position, time_increment)
        if self.get_mode() == behaviour.FREE:
            amplitude = max((input_position - self.interpreter.sensed_center()).mag() -
                            interpret.CENTER_SPATIAL_THRESHOLD, 0.0) / self.max_amplitude
            self.set_cursor(self.MC, self._target_state, amplitude)

    def _on_leaving_center(self, input_position):
        print "LEAVING_CENTER"
        self._select_target_state(input_position)
        self.initiate_free_movement()

    def _on_entering_center(self, input_position):
        print "ENTERING_CENTER"
        self.initiate_idle()

    def _select_target_state(self, input_position):
        mc = self._state_machine.states[MC]
        self._target_state = random.choice(mc.inputs + mc.outputs)
