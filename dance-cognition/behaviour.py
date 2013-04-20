from vector import *

class Behaviour:
    def __init__(self, state_machine):
        self._state_machine = state_machine
        self._sensed_center = Vector3d(0.0, 0.0, 0.0)

    def process_raw_input(self, input_position, time_increment):
        self._sensed_center += (input_position - self._sensed_center) * \
                               0.2 * min(time_increment, 1.0)
        sensed_input_position = input_position - self._sensed_center
        self.process_input(sensed_input_position)
