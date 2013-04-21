# sync: Mirrors the dynamics of the input. Works best when input is near center.

from vector import *
from states import InterStatePosition
import random
import behaviour
import math
from sensory_adaptation import SensoryAdapter

SPATIAL_THRESHOLD = 0.04
TEMPORAL_THRESHOLD = 0.2

class Behaviour(behaviour.Behaviour):
    max_amplitude = math.sqrt(2)

    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self._sensory_adapter = SensoryAdapter(0.1)
        self._target_state = None
        self._center_output = InterStatePosition(
            self._state_machine.states["MC"],
            self._state_machine.states["MLB"],
            0.0)
        self._in_center = True
        self._duration_in_center = 0
        self._output = self._center_output

    def process_raw_input(self, raw_input_position, time_increment):
        return self._sensory_adapter.process(raw_input_position, time_increment)

    def process_input(self, input_position, time_increment):
        input_in_center = input_position.mag() < SPATIAL_THRESHOLD
        if self._in_center:
            if input_in_center:
                self._duration_in_center += time_increment
            else:
                if self._duration_in_center >= TEMPORAL_THRESHOLD:
                    self._select_transition(input_position)
                self._in_center = False
        else:
            if input_in_center:
                self._in_center = True
                self._duration_in_center = 0

        if self._in_center:
            self._output = self._center_output
        else:
            amplitude = max(input_position.mag() - SPATIAL_THRESHOLD, 0.0) / self.max_amplitude
            self._output.relative_position = amplitude

    def output(self):
        return self._output

    def _select_transition(self, input_position):
        mc = self._state_machine.states["MC"]
        target_state = random.choice(mc.inputs + mc.outputs)
        self._output = InterStatePosition(mc, target_state, 0.0)
