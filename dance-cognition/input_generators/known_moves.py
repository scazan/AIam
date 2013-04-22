from states import state_machine
import random
import input_generator
from utils import random_unit_sphere_position
import math

PAUSE, MOVE = range(2)

class Generator(input_generator.Generator):
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("-pause-duration", type=float, default=0.5)
        parser.add_argument("-fluctuation", type=float, default=0.2)
        parser.add_argument("-move-duration", type=float, default=3.0)

    def __init__(self, args):
        self._pause_duration = args.pause_duration
        self._fluctuation_magnitude = args.fluctuation
        self._move_duration = args.move_duration
        self._destination_state = state_machine.states["MC"]
        self._destination_position = self._destination_state.position
        self._enter_pause_state()

    def update(self, time_increment):
        self._t += time_increment

        if self._state == PAUSE and self._t > self._pause_duration:
            self._enter_move_state()
        elif self._state == MOVE and self._t > self._move_duration:
            self._enter_pause_state()

    def _enter_pause_state(self):
        self._state = PAUSE
        self._source_state = self._destination_state
        self._source_position = self._destination_position
        self._t = 0.0

    def _enter_move_state(self):
        self._state = MOVE
        self._destination_state = random.choice(self._source_state.outputs + self._source_state.inputs)
        self._destination_position = self._destination_state.position + self._fluctuation()
        print "%s -> %s" % (self._source_state.name, self._destination_state.name)
        distance = (self._destination_position - self._source_state.position).mag()
        self._t = 0.0

    def position(self):
        if self._state == PAUSE:
            return self._source_position
        elif self._state == MOVE:
            return self._source_position + (self._destination_position - self._source_position) * \
                self._sigmoid(self._t / self._move_duration)

    def _sigmoid(self, x):
        return 1 - (math.cos(x * math.pi) + 1) / 2

    def _fluctuation(self):
        return random_unit_sphere_position() * self._fluctuation_magnitude
