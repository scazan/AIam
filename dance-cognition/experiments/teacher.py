import random
import numpy

class Teacher:
    def __init__(self, stimulus):
        self._stimulus = stimulus
        self._training_data = []
        self._create_training_data()

    def _create_training_data(self):
        print "creating training data..."
        time_increment = 1.0 / 50
        t = 0
        stimulus_duration = self._stimulus.get_duration()
        while t < stimulus_duration:
            self._add_training_datum()
            self.proceed(time_increment)
            t += time_increment
        print "ok"

    def get_training_data(self):
        return numpy.array(self._training_data)

    def proceed(self, time_increment):
        self._stimulus.proceed(time_increment)

    def _add_training_datum(self):
        datum = list(self._stimulus.get_value())
        self._training_data.append(datum)
