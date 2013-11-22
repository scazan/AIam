from numpy import array, dot
from math import radians, cos, sin

class vertex:
    def __init__(self, x=0, y=0, z=0):
      self.tr = [x,y,z,1]

class edge:
    def __init__(self, v1, v2):
      self.v1 = v1
      self.v2 = v2

def make_transposition_matrix(xpos, ypos, zpos):
    return array([
            [1.,    0.,    0.,    xpos],
            [0.,    1.,    0.,    ypos],
            [0.,    0.,    1.,    zpos],
            [0.,    0.,    0.,    1.] ])

def make_rotation_matrix(definition):
    rotation_matrix = array([
            [1.,0.,0.,0.],
            [0.,1.,0.,0.],
            [0.,0.,1.,0.],
            [0.,0.,0.,1.] ])
    for channel, degrees in definition:
        if channel == "Xrotation":
            rotation_matrix = dot(
                rotation_matrix,
                make_x_rotation_matrix(degrees))
        elif channel == "Yrotation":
            rotation_matrix = dot(
                rotation_matrix,
                make_y_rotation_matrix(degrees))
        elif channel == "Zrotation":
            rotation_matrix = dot(
                rotation_matrix,
                make_z_rotation_matrix(degrees))
        else:
            raise Exception("unknown channel %r" % channel)
    return rotation_matrix

def rotation_definition_to_euler_angles(definition):
    euler_angles = [None, None, None]
    for channel, degrees in definition:
        if channel == "Xrotation":
            euler_angles[0] = radians(degrees)
        elif channel == "Yrotation":
            euler_angles[1] = radians(degrees)
        elif channel == "Zrotation":
            euler_angles[2] = radians(degrees)
    return euler_angles

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
