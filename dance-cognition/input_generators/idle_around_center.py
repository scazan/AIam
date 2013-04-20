from vector import *
import random
import math
import input_generator

class Generator(input_generator.Generator):
    center = Vector3d(0.0, 0.0, 0.0)

    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("-magnitude", type=float, default=0.1)
        parser.add_argument("-pause-duration", type=float, default=0.2)
        parser.add_argument("-sway-duration", type=float, default=1.0)

    def __init__(self, args):
        self._magnitude = args.magnitude
        self._position = Vector3d(0, 0, 0)
        self._t = 0
        self._sway_duration = args.sway_duration
        self._pause_duration = args.pause_duration
        self._sway_target = None
        self._pausing = True

    def update(self, time_increment):
        self._t += time_increment

        if self._pausing:
            if self._t > self._pause_duration:
                self._pausing = False
                self._t = 0
                self._sway_target = Vector3d(
                    random.uniform(-1, 1),
                    random.uniform(-1, 1),
                    random.uniform(-1, 1)) * self._magnitude
        else:
            if self._t > self._sway_duration:
                self._pausing = True
                self._t = 0

    def position(self):
        if self._pausing:
            return self.center
        else:
            return self._sway_target * self._envelope(self._t / self._sway_duration)

    def _envelope(self, x):
        if x < 0.5:
            return self._sigmoid(x*2)
        else:
            return 1 - self._sigmoid(1 - x*2)

    def _sigmoid(self, x):
        return 1 - (math.cos(x * math.pi) + 1) / 2
