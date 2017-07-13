import numpy
import random
import math
from transformations import quaternion_from_euler, euler_from_quaternion
from expmap import *

EPSILON = 1E-12

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

class RotationParameterization:
    @staticmethod
    def interpolate(x, y, amount):
        return RotationParameterization.interpolate_linearly(x, y, amount)

    @staticmethod
    def interpolate_linearly(x, y, amount):
        return list(numpy.array(y) * amount + numpy.array(x) * (1-amount))
        
class EulerTo3Vectors(RotationParameterization):
    num_parameters = 6

    @staticmethod
    def rotation_to_parameters(euler):
        return euler_to_vector6d(*euler.angles)

    @staticmethod
    def parameters_to_rotation(parameters, axes):
        return vector6d_to_euler(parameters)

class ZeroNormedQuaternion(Exception):
    pass

class EulerToQuaternion(RotationParameterization):
    num_parameters = 4

    @staticmethod
    def rotation_to_parameters(euler):
        return quaternion_from_euler(*euler.angles, axes=euler.axes)

    @staticmethod
    def parameters_to_rotation(non_normalized_quaternion, axes):
        normalized_quaternion = non_normalized_quaternion / numpy.linalg.norm(
            non_normalized_quaternion)
        return euler_from_quaternion(normalized_quaternion, axes)

    @staticmethod
    def interpolate(q0, q1, amount, shortest_path=True):
        q0_norm = numpy.linalg.norm(q0)
        if q0_norm == 0:
            raise ZeroNormedQuaternion(
                "First quaternion passed to interpolate() is zero and cannot be normalized.")
        q0 /= q0_norm

        q1_norm = numpy.linalg.norm(q1)
        if q1_norm == 0:
            raise ZeroNormedQuaternion(
                "Second quaternion passed to interpolate() is zero and cannot be normalized.")
        q1 /= q1_norm
        
        ca = numpy.dot(q0, q1)
        if shortest_path and ca<0:
            ca = -ca
            neg_q1 = True
        else:
            neg_q1 = False

        if ca>=1.0:
            o = 0.0
        elif ca<=-1.0:
            o = math.pi
        else:
            o = math.acos(ca)
        so = math.sin(o)

        if (abs(so)<EPSILON):
            return RotationParameterization.interpolate_linearly(q0, q1, amount)
        
        a = math.sin(o*(1.0-amount)) / so
        b = math.sin(o*amount) / so
        if neg_q1:
            return q0*a - q1*b
        else:
            return q0*a + q1*b

class EulerToExpmap(RotationParameterization):
    num_parameters = 4

    @staticmethod
    def rotation_to_parameters(euler):
        return expmap_from_euler(*euler.angles, axes=euler.axes)

    @staticmethod
    def parameters_to_rotation(parameters, axes):
        return euler_from_expmap(parameters, axes)
