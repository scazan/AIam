import os
import random
from math import atan2, degrees, pi, sqrt
# import numpy as np
import time
import sys
import subprocess

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../dance-cognition")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../dance-cognition/connectivity")
from osc_receiver import OscReceiver

OSC_PORT = 15002


center = [132,4500]
targets = [center,[1500/2,3000],[-1500/2,3000],[-1500/2,6000-1500],[1500/2,6000-1500]]

target = targets[0]
print target
target_reached = False

d = {
	0: 'Windows',
	1: 'Windows Office',
	2: 'Office',
	3: 'Office Bathroom',
	4: 'Bathroom',
	5: 'Bathroom Screen',
	6: 'Screen',
	7: 'Screen Windows',
	8: 'Windows'
}

def distance(p0, p1):
    return sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)

def handle_center(path, values, types, src, user_data):

	global time_of_last_handler
	global target
	# check distance from current target
	user_id, x, y, z = values
	d = distance([x,z], target)
	center_distance = distance([x,z], center)
	print center_distance
	if center_distance < 2000:
		if d<400 :
			# os.system("say Target reached")
			# os.system("say new target")

			target_reached = False
			#generate new target
			target=random.choice(targets)
			# print "target:", target
		elif time_of_last_handler is None or time.time() - time_of_last_handler > 1 :
			# print user_id, x, y, z
			getDir(x,z,target[0],target[1])
			time_of_last_handler = time.time()
			# print "distance:", d
	else:
		subprocess.call("afplay error.wav", shell=True)

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

	directionId = round(degs/45.0)
	# print(degs)

	direction = d[directionId]
	# print(direction)
	os.system("say "+direction)



while True:
    time.sleep(1)

