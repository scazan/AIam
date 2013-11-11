HISTORY_SIZE = 100

import collections
import random
import numpy

class Teacher:
    def __init__(self, stimulus, max_history_size):
        self._stimulus = stimulus
        self._input_history = collections.deque(maxlen=HISTORY_SIZE)
        self._training_history = collections.deque(maxlen=max_history_size)

    def proceed(self, time_increment):
        self._stimulus.proceed(time_increment)
        self._add_training_tuple_to_history()

    def _add_training_tuple_to_history(self):
        recent_input = self._stimulus.get_value()
        self._input_history.append(recent_input)
        if self.collected_enough_training_data():
            past_input = self._input_history[0]
            self._training_history.append((past_input, recent_input))

    def collected_enough_training_data(self):
        return len(self._input_history) == HISTORY_SIZE

    def judge_error(self, expected_output, output):
        return numpy.linalg.norm(expected_output - output)

class ShufflingTeacher(Teacher):
    def __init__(self, stimulus):
        Teacher.__init__(self, stimulus, max_history_size=None)
        self._create_training_data()

    def _create_training_data(self):
        time_increment = 1.0 / 50
        while not self.collected_enough_training_data():
            self._add_training_tuple_to_history()
            self.proceed(time_increment)

        t = 0
        stimulus_duration = self._stimulus.get_duration()
        while t < stimulus_duration:
            self._add_training_tuple_to_history()
            self.proceed(time_increment)
            t += time_increment

        self._pick_next_training_datum_to_return()

    def proceed(self, time_increment):
        Teacher.proceed(self, time_increment)
        if self.collected_enough_training_data():
            self._pick_next_training_datum_to_return()

    def _pick_next_training_datum_to_return(self):
        random_index = random.randint(0, len(self._training_history)-1)
        self._input_to_return, self._output_to_return = \
            self._training_history[random_index]

    def get_input(self):
        return self._input_to_return

    def get_output(self):
        return self._output_to_return

class LiveTeacher(Teacher):
    def __init__(self, stimulus):
        Teacher.__init__(self, stimulus, max_history_size=HISTORY_SIZE)
        self._add_training_tuple_to_history()

    def get_input(self):
        past_input, past_output = self._training_history[0]
        return past_input

    def get_output(self):
        past_input, past_output = self._training_history[0]
        return past_output
