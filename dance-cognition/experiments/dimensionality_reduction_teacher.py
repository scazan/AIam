import random
import numpy
import cPickle
import os

class Teacher:
    def __init__(self, stimulus, frame_rate):
        self._stimulus = stimulus
        self._frame_rate = frame_rate
        self._training_data = None
        if self._cacheable():
            if self._cache_exists():
                self._load_training_data_from_cache()
            else:
                self._create_training_data(stimulus.get_duration())
                self._save_training_data_to_cache()

    def _create_training_data(self, duration):
        print "creating training data..."
        self._training_data = []
        time_increment = 1.0 / self._frame_rate
        t = 0
        while t < duration:
            self._add_training_datum()
            self.proceed(time_increment)
            t += time_increment
        print "ok"

    def get_training_data(self, duration):
        if self._training_data is None:
            self._create_training_data(duration)
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
        print "loading training data from %s ..." % cache_filename
        f = open(cache_filename)
        self._training_data = cPickle.load(f)
        f.close()
        print "ok"

    def _save_training_data_to_cache(self):
        cache_filename = self._cache_filename()
        print "saving training data to %s ..." % cache_filename
        f = open(cache_filename, "w")
        cPickle.dump(self._training_data, f)
        f.close()
        print "ok"

    def _cache_filename(self):
        return "%s.%sfps.data" % (self._stimulus.filename(), self._frame_rate)

    def _cacheable(self):
        return hasattr(self._stimulus, "filename") and \
            hasattr(self._stimulus, "get_duration")
