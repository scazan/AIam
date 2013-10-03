from angle_parameters import *
import unittest
import math

class AngleParametersTest(unittest.TestCase):
    def test_radians_to_vector2d_and_back(self):
        for n in range(100):
            r = float(n) / 100 * (math.pi*2)
            self._assert_radians_equal(r, vector2d_to_radians(radians_to_vector2d(r)))

    def _assert_radians_equal(self, x, y):
        self.assertAlmostEquals(
            self._clamp_radians(x),
            self._clamp_radians(y))

    def _clamp_radians(self, r):
        while r < 0:
            r += math.pi*2
        while r > math.pi*2:
            r -= math.pi*2
        return r

    def test_radians3d_to_vector6d_and_back(self):
        radians3ds = [
            (0.1, 0.3, 1.8),
            (4.1, 2.3, 3.8),
            (5.1, 0.1, 2.8),
            ]
        for radians3d in radians3ds:
            self._assert_radians3d_almost_equals(
                radians3d, 
                vector6d_to_radians3d(radians3d_to_vector6d(*radians3d)))

    def _assert_radians3d_almost_equals(self, x, y):
        self._assert_radians_equal(x[0], y[0])
        self._assert_radians_equal(x[1], y[1])
        self._assert_radians_equal(x[2], y[2])

