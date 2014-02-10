import math

class Envelope:
    _min_relative_velocity = .1

    def envelope(self, x):
        return self._clamp(self.unclamped_envelope(x))

    def _clamp(self, x):
        return self._min_relative_velocity + (1 - self._min_relative_velocity) * x

class SymmetricalEnvelope(Envelope):
    def unclamped_envelope(self, x):
        if x < .5:
            return self._clamp(self.rising_envelope(x*2))
        else:
            return self._clamp(self.rising_envelope((1-x) * 2))

class constant_envelope:
    def envelope(self, x):
        return 1.

class exponential_envelope(SymmetricalEnvelope):
    _slope = 3.

    def rising_envelope(self, x):
        return pow(x, self._slope)

class sine_envelope(Envelope):
    def unclamped_envelope(self, x):
        return (math.sin((x + .75) * math.pi*2) + 1) / 2
