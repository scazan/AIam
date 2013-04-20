from vector import *
from states import InterStatePosition
import random

SPATIAL_THRESHOLD = 0.04
TEMPORAL_THRESHOLD = 0.2

class Behaviour:
    def __init__(self, state_machine):
        self._state_machine = state_machine
        self._target_state = None
        self._center_output = InterStatePosition(
            state_machine.states["MC"],
            state_machine.states["MLB"],
            0.0)
        self._sensed_center = Vector3d(0.0, 0.0, 0.0)
        self._in_center = True
        self._duration_in_center = 0

    def process_input(self, input_position, time_increment):
        self._sensed_center += (input_position - self._sensed_center) * \
                               0.2 * min(time_increment, 1.0)
        sensed_input_position = input_position - self._sensed_center
        amplitude = max(sensed_input_position.mag() - SPATIAL_THRESHOLD, 0.0)
        self._sensed_center = max(self._sensed_center, amplitude)

        input_in_center = sensed_input_position.mag() < SPATIAL_THRESHOLD
        if self._in_center:
            if input_in_center:
                self._duration_in_center += time_increment
            else:
                if self._duration_in_center >= TEMPORAL_THRESHOLD:
                    self._select_transition()
                self._in_center = False
        else:
            if input_in_center:
                self._in_center = True
                self._duration_in_center = 0

        if self._in_center:
            self._output = self._center_output
        else:
            self._output.relative_position = amplitude

    def output(self):
        return self._output

    def _select_transition(self):
        mc = self._state_machine.states["MC"]
        target_state = random.choice(mc.inputs + mc.outputs)
        self._output = InterStatePosition(mc, target_state, 0.0)
