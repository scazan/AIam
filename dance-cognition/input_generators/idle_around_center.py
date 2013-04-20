from vector import *
import random
import math
import input_generator

class Generator(input_generator.Generator):
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("-magnitude", type=float, default=0.1)

    def __init__(self, args):
        self._magnitude = args.magnitude
        self._position = Vector3d(0, 0, 0)
        self._t = 0
        self._sway_duration = 1.0
        self._sway_target = None

    def update(self, time_increment):
        self._t += time_increment
        if self._t > self._sway_duration or self._sway_target is None:
            self._sway_target = Vector3d(
                random.uniform(-1, 1),
                random.uniform(-1, 1),
                random.uniform(-1, 1)) * self._magnitude
            self._t = 0

    def position(self):
        return self._sway_target * self._envelope(self._t / self._sway_duration)

    def _envelope(self, x):
        if x < 0.5:
            return self._sigmoid(x*2)
        else:
            return 1 - self._sigmoid(1 - x*2)

    def _sigmoid(self, x):
        return 1 - (math.cos(x * math.pi) + 1) / 2
