import os
import random
from math import atan2, degrees, pi
# import numpy as np
import time
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../dance-cognition")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../dance-cognition/connectivity")
from osc_receiver import OscReceiver

OSC_PORT = 15002


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


def handle_center(path, values, types, src, user_data):

	global time_of_last_handler
	if time_of_last_handler is None or time.time() - time_of_last_handler > 4:
		user_id, x, y, z = values
		print user_id, x, y, z
		getDir(x,y,0,0)
		time_of_last_handler = time.time()


time_of_last_handler = None
osc_receiver = OscReceiver(OSC_PORT)
osc_receiver.add_method("/center", "ifff", handle_center)
osc_receiver.start()



def getDir(x1,y1,x2,y2):
# osc receive from c++
	# location = np.array([random.random(),random.random()])
	# target =  np.array([random.random(),random.random()])

	# x1 = location[0]
	# y1 = location[1]
	# x2 = target[0]
	# y2 = target[1]

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



while True:
    time.sleep(1)

