import random
from vector import DirectionalVector
import math

def input_noise():
    angle = random.uniform(0, math.pi*2)
    mag = random.normalvariate(0.0, 0.5) * 0.001
    return DirectionalVector(angle, mag)
