import random
import numpy
import pickle
import os

class Teacher:
    def __init__(self, stimulus):
        self._stimulus = stimulus
        if self._cacheable():
            if self._cache_exists():
                self._load_training_data_from_cache()
            else:
                self._create_training_data()
                self._save_training_data_to_cache()
        else:
            self._create_training_data()

    def _create_training_data(self):
        print "creating training data..."
        self._training_data = []
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

    def _cache_exists(self):
        return os.path.exists(self._cache_filename())

    def _load_training_data_from_cache(self):
        cache_filename = self._cache_filename()
        print "loading training data from %s..." % cache_filename
        f = open(cache_filename)
        self._training_data = pickle.load(f)
        f.close()
        print "ok"

    def _save_training_data_to_cache(self):
        cache_filename = self._cache_filename()
        print "saving training data to %s..." % cache_filename
        f = open(cache_filename, "w")
        pickle.dump(self._training_data, f)
        f.close()
        print "ok"

    def _cache_filename(self):
        return self._stimulus.filename() + ".data"

    def _cacheable(self):
        return hasattr(self._stimulus, "filename")
