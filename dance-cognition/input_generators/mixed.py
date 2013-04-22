from vector import *
from states import state_machine
import random
import input_generator
from utils import random_unit_sphere_position
import math

PAUSE, MOVE, SWAY_IN, SWAY_OUT = range(4)

class Generator(input_generator.Generator):
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("-sway-magnitude", type=float, default=0.2)
        parser.add_argument("-sway-duration", type=float, default=1.0)
        parser.add_argument("-pause-duration", type=float, default=0.5)
        parser.add_argument("-move-fluctuation", type=float, default=0.2)
        parser.add_argument("-idle-fluctuation", type=float, default=0.1)
        parser.add_argument("-speed", type=float, default=1.0)

    def __init__(self, args):
        self._sway_magnitude = args.sway_magnitude
        self._sway_duration = args.sway_duration
        self._pause_duration = args.pause_duration
        self._move_fluctuation_magnitude = args.move_fluctuation
        self._idle_fluctuation_magnitude = args.idle_fluctuation
        self._speed = args.speed
        self._destination_state = state_machine.states["MC"]
        self._destination_position = self._destination_state.position
        self._enter_sway_in_state()
        self._enter_pause_state()

    def update(self, time_increment):
        self._t += time_increment

        if self._state == PAUSE and self._t > self._pause_duration:
            if self._source_state.name == "MC" and random.random() < 0.8:
                print "sway"
                self._enter_sway_out_state()
            else:
                self._enter_move_state()
        elif self._state == MOVE and self._t > self._move_duration:
            self._enter_pause_state()
        elif self._state == SWAY_OUT and self._t > self._sway_duration:
            self._enter_sway_in_state()
        elif self._state == SWAY_IN and self._t > self._sway_duration:
            self._enter_pause_state()

    def _enter_pause_state(self):
        self._source_state = self._destination_state
        if self._state == MOVE:
            self._source_position = self._destination_position
        self._t = 0.0
        self._state = PAUSE

    def _enter_sway_out_state(self):
        self._state = SWAY_OUT
        self._t = 0
        self._sway_target = Vector3d(
            random.uniform(-1, 1),
            random.uniform(-1, 1),
            random.uniform(-1, 1)) * self._sway_magnitude

    def _enter_sway_in_state(self):
        self._state = SWAY_IN
        self._t = 0
        self._source_position = state_machine.states["MC"].position + self._idle_fluctuation()

    def _enter_move_state(self):
        self._state = MOVE
        self._destination_state = random.choice(self._source_state.outputs + self._source_state.inputs)
        if self._destination_state.name == "MC":
            self._destination_position = state_machine.states["MC"].position + self._idle_fluctuation()
        else:
            self._destination_position = self._destination_state.position + self._move_fluctuation()
        print "%s -> %s" % (self._source_state.name, self._destination_state.name)
        distance = (self._destination_position - self._source_state.position).mag()
        self._move_duration = distance / self._speed
        self._t = 0.0

    def position(self):
        if self._state == PAUSE:
            return self._source_position
        elif self._state == MOVE:
            return self._source_position + (self._destination_position - self._source_position) * \
                self._sigmoid(self._t / self._move_duration)
        elif self._state == SWAY_OUT:
            return self._source_position + (self._sway_target - self._source_position) * \
                self._sigmoid(self._t / self._sway_duration)
        elif self._state == SWAY_IN:
            return self._source_position + (self._sway_target - self._source_position) * \
                self._sigmoid((self._sway_duration - self._t) / self._sway_duration)

    def _sigmoid(self, x):
        return 1 - (math.cos(x * math.pi) + 1) / 2

    def _idle_fluctuation(self):
        return random_unit_sphere_position() * self._idle_fluctuation_magnitude

    def _move_fluctuation(self):
        return random_unit_sphere_position() * self._move_fluctuation_magnitude
