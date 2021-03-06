from numpy import array, dot
from math import radians, cos, sin

class edge:
    def __init__(self, v1, v2):
      self.v1 = v1
      self.v2 = v2

class Euler:
    def __init__(self, angles, axes='sxyz'):
        self.angles = angles
        self.axes = axes

def make_translation_matrix(xpos, ypos, zpos):
    return array([
            [1.,    0.,    0.,    xpos],
            [0.,    1.,    0.,    ypos],
            [0.,    0.,    1.,    zpos],
            [0.,    0.,    0.,    1.] ])

def make_z_rotation_matrix(degrees):
    theta = radians(degrees)
    mycos = cos(theta)
    mysin = sin(theta)
    return array([
        [mycos,  -mysin, 0.,   0.],
        [mysin,  mycos,  0.,   0.],
        [0.,     0.,     1.,   0.],
        [0.,     0.,     0.,   1.] ])

def make_y_rotation_matrix(degrees):
    theta = radians(degrees)
    mycos = cos(theta)
    mysin = sin(theta)
    return array([
        [mycos,  0.,    mysin, 0.],
        [0.,     1.,    0.,    0.],
        [-mysin, 0.,    mycos, 0.],
        [0.,     0.,    0.,    1.] ])

def make_x_rotation_matrix(degrees):
    theta = radians(degrees)
    mycos = cos(theta)
    mysin = sin(theta)
    return array([
        [1.,     0.,     0.,     0.],
        [0.,     mycos,  -mysin, 0.],
        [0.,     mysin,  mycos,  0.],
        [0.,     0.,     0.,     1.] ])
