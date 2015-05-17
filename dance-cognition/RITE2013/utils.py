import random
from vector import *

def random_unit_sphere_position():
    p = Vector3d(
        random.uniform(-1, 1),
        random.uniform(-1, 1),
        random.uniform(-1, 1))
    p.normalize()
    return p
