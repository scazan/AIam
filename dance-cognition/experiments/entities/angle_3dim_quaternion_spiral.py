from entities.angle_3dim_quaternion import *
import math

class Entity(QuaternionEntity):
    def get_value(self):
        x = (self._t / 1) % (2*math.pi)
        y = (self._t / 2) % (2*math.pi)
        z = (self._t / 4) % (2*math.pi)
        return quaternion_from_euler(x, y, z)

    def get_duration(self):
        return 2 * math.pi * 4
