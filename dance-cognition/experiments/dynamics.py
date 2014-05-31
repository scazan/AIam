import math

class Dynamics:
    def __init__(self, min_relative_velocity=.1):
        self._min_relative_velocity = min_relative_velocity

    def velocity(self, relative_cursor):
        return self._clamp(self.unclamped_velocity(relative_cursor))

    def _clamp(self, relative_cursor):
        return self._min_relative_velocity + (1 - self._min_relative_velocity) * relative_cursor

class SymmetricalDynamics(Dynamics):
    def unclamped_velocity(self, relative_cursor):
        if relative_cursor < .5:
            return self._clamp(self.rising_velocity(relative_cursor*2))
        else:
            return self._clamp(self.rising_velocity((1-relative_cursor) * 2))

class constant_dynamics(Dynamics):
    def velocity(self, relative_cursor):
        return 1.

class exponential_dynamics(SymmetricalDynamics):
    _slope = 3.

    def rising_velocity(self, relative_cursor):
        return pow(relative_cursor, self._slope)

class sine_dynamics(Dynamics):
    def unclamped_velocity(self, relative_cursor):
        return (math.sin((relative_cursor + .75) * math.pi*2) + 1) / 2
