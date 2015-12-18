import unittest
from bvh.bvh_reader.bvh_collection import BvhCollection

class MockScaleInfo:
    min_x = 0
    min_y = 0
    min_z = 0
    max_x = 0
    max_y = 0
    max_z = 0

class MockBvhReader:
    def __init__(self, duration, num_frames=1):
        self._duration = duration
        self._num_frames = num_frames
        self._scale_info = MockScaleInfo()

    def read(self):
        pass

    def get_duration(self):
        return self._duration

    def get_num_frames(self):
        return self._num_frames

class TestedBvhCollection(BvhCollection):
    def __init__(self, bvh_readers):
        self._init_readers(bvh_readers)

class BvhCollectionTestCase(unittest.TestCase):
    def test_duration(self):
        self._given_bvh_reader(duration=10)
        self._given_bvh_reader(duration=5)
        self._when_creating_bvh_collection()
        self._then_duration_is(15)

    def setUp(self):
        self._bvh_readers = []

    def _given_bvh_reader(self, **kwargs):
        self._bvh_readers.append(MockBvhReader(**kwargs))

    def _when_creating_bvh_collection(self):
        self._bvh_collection = TestedBvhCollection(self._bvh_readers)
        self._bvh_collection.read()

    def _then_duration_is(self, expected_duration):
        self.assertEquals(expected_duration, self._bvh_collection.get_duration())
