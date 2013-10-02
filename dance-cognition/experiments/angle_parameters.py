import numpy
import random
import math

def radians_to_vector2d(radians):
    return numpy.array([math.cos(radians), math.sin(radians)])

def vector2d_to_radians(v):
    dx, dy = v
    if dx == 0 and dy == 0:
        return random.uniform(0, 2*math.pi)
    else:
        return math.atan2(dy, dx)

def radians3d_to_vector6d(r1, r2, r3):
    return numpy.append(
        radians_to_vector2d(r1),
        numpy.append(
            radians_to_vector2d(r2),
            radians_to_vector2d(r3)))

def vector6d_to_radians3d(vector6d):
    r1 = vector2d_to_radians(vector6d[0:2])
    r2 = vector2d_to_radians(vector6d[2:4])
    r3 = vector2d_to_radians(vector6d[4:6])
    return r1, r2, r3
