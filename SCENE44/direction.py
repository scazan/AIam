import os
import random
from math import atan2, degrees, pi
import numpy as np

d = {
	0: 'East',
	1: 'Northeast',
	2: 'North',
	3: 'Northwest',
	4: 'West',
	5: 'Southwest ',
	6: 'South',
	7: 'Southeast',
	8: 'East'
}

# osc receive from c++
location = np.array([random.random(),random.random()])
target =  np.array([random.random(),random.random()])

x1 = location[0]
y1 = location[1]
x2 = target[0]
y2 = target[1]

dx = x2 - x1
dy = y2 - y1
rads = atan2(dy,dx)
rads %= 2*pi
degs = degrees(rads)

directionId = round(350/45.0)
print(degs)

direction = d[directionId]
print(direction)
os.system("say "+direction)

