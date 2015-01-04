from experiment import *
import math
import transformations
import so3
import vectorops

class Entity(BaseEntity):
    def get_value(self):
        x = (self._t / 1) % (2*math.pi)
        y = (self._t / 2) % (2*math.pi)
        z = (self._t / 4) % (2*math.pi)
        return expmap_from_euler(x, y, z)

    def get_duration(self):
        return 2 * math.pi * 4

def expmap_from_euler(x, y, z):
    matrix = transformations.euler_matrix(x, y, z)
    R = so3.from_matrix(matrix)
    moment = so3.moment(R)
    axis_angle_parameters = vectorops.unit(moment) + [vectorops.norm(moment)]
    return axis_angle_parameters
