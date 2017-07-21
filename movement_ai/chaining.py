import collections
import numpy

class Chainer:
    def __init__(self):
        self._input_queue = collections.deque()
        self._previous_translated_value = None

    def switch_source(self):
        self._offset = None

    def put(self, value):
        self._input_queue.append(value)
        
    def get(self):
        untranslated_value = self._input_queue.popleft()
        if self._offset is None:
            if self._previous_translated_value is None:
                self._offset = numpy.zeros(len(untranslated_value))
            else:
                self._offset = untranslated_value - self._previous_translated_value
        translated_value = untranslated_value - self._offset
        self._previous_translated_value = translated_value
        return translated_value
