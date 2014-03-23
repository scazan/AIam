from entities.point import *

class Entity(BaseEntity):
    def get_value(self):
        z = math.cos(self._t)
        y = math.sin(self._t)
        x = 0
        return [x, y, z]

    def get_duration(self):
        return 2 * math.pi
