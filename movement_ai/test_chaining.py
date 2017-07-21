import unittest

from chaining import Chainer

class Sequence:
    def __init__(self, vectors):
        self._vectors = vectors
        self._index = 0

    def get(self):
        result = self._vectors[self._index % len(self._vectors)]
        self._index += 1
        return result

class ChainingTestCase(unittest.TestCase):
    def test_1_sequence_1_iteration(self):
        self.given_sequence([ [0], [1] ])
        self.given_switched_source()
        self.when_getting_items(2)
        self.then_result_is([ [0], [1] ])

    def test_1_sequence_2_iterations(self):
        self.given_sequence([ [0], [1] ])
        self.given_switched_source()
        self.given_got_items(2)
        self.given_switched_source()
        self.when_getting_items(2)
        self.then_result_is([ [1], [2] ])

    def test_1_sequence_3_iterations(self):
        self.given_sequence([ [0], [1] ])
        self.given_switched_source()
        self.given_got_items(2)
        self.given_switched_source()
        self.given_got_items(2)
        self.given_switched_source()
        self.when_getting_items(2)
        self.then_result_is([ [2], [3] ])

    def setUp(self):
        self._chainer = Chainer()
        
    def given_sequence(self, vectors):
        self._sequence = Sequence(vectors)

    def given_switched_source(self):
        self._chainer.switch_source()
            
    def when_getting_items(self, num_items):
        for n in range(num_items):
            self._chainer.put(self._sequence.get())
        self._actual_result = [self._chainer.get() for n in range(num_items)]

    def given_got_items(self, num_items):
        for n in range(num_items):
            self._chainer.put(self._sequence.get())
            self._chainer.get()
            
    def then_result_is(self, expected_result):
        self.assertEquals(
            self._sequence_as_list(expected_result),
            self._sequence_as_list(self._actual_result))

    def _sequence_as_list(self, sequence):
        return [list(x) for x in sequence]
