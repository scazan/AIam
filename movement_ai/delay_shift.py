import collections

class DelayShift:
    def __init__(self, period_duration, peak_duration, magnitude):
        self._t = 0
        self._period_duration = period_duration
        self._peak_duration = peak_duration
        self._flat_duration = period_duration - peak_duration
        self._magnitude = magnitude

    def proceed(self, time_increment):
        self._t += time_increment

    def get_value(self):
        time_within_period = self._t % self._period_duration
        if time_within_period < self._flat_duration:
            return 0
        else:
            time_within_peak = (time_within_period - self._flat_duration)
            relative_time_within_peak = time_within_peak / self._peak_duration
            if relative_time_within_peak < 0.5:
                return relative_time_within_peak * 2 * self._magnitude
            else:
                return (1 - relative_time_within_peak) * 2 * self._magnitude
            
class SmoothedDelayShift:
    def __init__(self, period_duration, peak_duration, magnitude, smoothing):
        self._delay_shift = DelayShift(period_duration, peak_duration, magnitude)
        self._buffer = collections.deque([0] * smoothing, maxlen=smoothing)

    def proceed(self, time_increment):
        self._delay_shift.proceed(time_increment)
        self._buffer.append(self._delay_shift.get_value())

    def get_value(self):
        return sum(self._buffer) / len(self._buffer)
    
