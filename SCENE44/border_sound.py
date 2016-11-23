from audio import *
import time
from math import sqrt

s = create_audio_server().boot()
s.amp = 0.1
sine_left = Sine()
sine_right = Sine()
left = sine_left.out()
right = sine_right.out(1)

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../dance-cognition")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../dance-cognition/connectivity")
from osc_receiver import OscReceiver

OSC_PORT = 15002

min_freq = 50
max_freq = 500
center = [132,4500]
area_radius = 1000 
max_distance_to_border = 1000

def update_sound(relative_distance_to_border):
        freq = min_freq + (max_freq - min_freq) * relative_distance_to_border
        sine_left.setFreq(freq)
        sine_right.setFreq(freq)

update_sound(1)

def distance(p0, p1):
    return sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)

def handle_center(path, values, types, src, user_data):
	global area_radius
        global s
	user_id, x, y, z = values
	center_distance = distance([x,z], center)
        distance_to_border = abs(center_distance - area_radius)
        relative_distance_to_border = min(distance_to_border / max_distance_to_border, 1)
        print relative_distance_to_border
        update_sound(relative_distance_to_border)

osc_receiver = OscReceiver(OSC_PORT)
osc_receiver.add_method("/center", "ifff", handle_center)
osc_receiver.start()

s.start()

while True:
    time.sleep(1)
