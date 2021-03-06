import numpy
import random
import math
from transformations import quaternion_from_euler, euler_from_quaternion
from expmap import *

def radians_to_vector2d(radians):
    return numpy.array([math.cos(radians), math.sin(radians)])

def vector2d_to_radians(v):
    dx, dy = v
    if dx == 0 and dy == 0:
        return random.uniform(0, 2*math.pi)
    else:
        return math.atan2(dy, dx)

def euler_to_vector6d(r1, r2, r3):
    return numpy.append(
        radians_to_vector2d(r1),
        numpy.append(
            radians_to_vector2d(r2),
            radians_to_vector2d(r3)))

def vector6d_to_euler(vector6d):
    r1 = vector2d_to_radians(vector6d[0:2])
    r2 = vector2d_to_radians(vector6d[2:4])
    r3 = vector2d_to_radians(vector6d[4:6])
    return r1, r2, r3

class EulerTo3Vectors:
    num_parameters = 6

    @staticmethod
    def rotation_to_parameters(euler):
        return euler_to_vector6d(*euler.angles)

    @staticmethod
    def parameters_to_rotation(parameters, axes):
        return vector6d_to_euler(parameters)

class EulerToQuaternion:
    num_parameters = 4

    @staticmethod
    def rotation_to_parameters(euler):
        return quaternion_from_euler(*euler.angles, axes=euler.axes)

    @staticmethod
    def parameters_to_rotation(non_normalized_quaternion, axes):
        normalized_quaternion = non_normalized_quaternion / numpy.linalg.norm(
            non_normalized_quaternion)
        return euler_from_quaternion(normalized_quaternion, axes)

class EulerToExpmap:
    num_parameters = 4

    @staticmethod
    def rotation_to_parameters(euler):
        return expmap_from_euler(*euler.angles, axes=euler.axes)

    @staticmethod
    def parameters_to_rotation(parameters, axes):
        return euler_from_expmap(parameters, axes)
