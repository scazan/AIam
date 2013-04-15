from vector import Vector2d
import math

response_factor = 1.0
activity_magnitude_threshold = 0.01
passivity_duration_threshold = 5.0

class SensoryAdapter:
    def __init__(self):
        self._background = Vector2d(0.0, 0.0)
        self._previous_stimulus = Vector2d(0.0, 0.0)
        self._passivity_duration = 0.0

    def feed_stimulus(self, stimulus, time_increment):
        if (self._previous_stimulus - stimulus).mag() > activity_magnitude_threshold:
            self._passivity_duration = 0.0
        else:
            self._passivity_duration += time_increment

        if self._passivity_duration > passivity_duration_threshold:
            self._background += (stimulus - self._background) * \
                min(response_factor * time_increment, 1.0)

        self._previous_stimulus.set(stimulus)

    def response(self):
        return self._previous_stimulus - self._background

    def background(self):
        return self._background
