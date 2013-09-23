import numpy
import random
import math

def radians_to_vector2d(radians):
    return numpy.array([math.cos(radians), math.sin(radians)])

def vector2d_to_radians(v):
    dx, dy = v
    if dx == 0 and dy == 0:
        print "RANDOM!"
        return random.uniform(0, 2*math.pi)
    else:
        return math.atan2(dy, dx)
