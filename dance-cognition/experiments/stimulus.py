class Stimulus:
    def __init__(self):
        self._t = 0

    def proceed(self, time_increment):
        self._t += time_increment
