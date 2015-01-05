from angle_parameters import *
import unittest
import math
from transformations import euler_matrix, is_same_transform

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")
from bvh_reader.geo import Euler

class AngleParametersTest(unittest.TestCase):
    def test_radians_vector2d_inversion(self):
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

    def test_euler_to_3vectors_inversion(self):
        self._test_angle_3dof_inversion(EulerTo3Vectors)

    def test_euler_to_quaternion_inversion(self):
        self._test_angle_3dof_inversion(EulerToQuaternion)

    def _test_angle_3dof_inversion(self, parameterization):
        eulers = [
            (0.1, 0.3, 1.8),
            (4.1, 2.3, 3.8),
            (5.1, 0.1, 2.8),
            ]
        for angles in eulers:
            euler = Euler(angles)
            parameters = parameterization.rotation_to_parameters(euler)
            self._assert_euler_equals(
                euler.angles,
                parameterization.parameters_to_rotation(parameters, euler.axes))

    def _assert_euler_equals(self, angles1, angles2):
        matrix1 = euler_matrix(*angles1)
        matrix2 = euler_matrix(*angles2)
        self.assertTrue(is_same_transform(matrix1, matrix2))
