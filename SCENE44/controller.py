#!/usr/bin/env python

import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../dance-cognition")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../dance-cognition/connectivity")
from osc_receiver import OscReceiver

OSC_PORT = 15002

def handle_center(path, values, types, src, user_data):
    user_id, x, y, z = values
    print user_id, x, y, z

osc_receiver = OscReceiver(OSC_PORT)
osc_receiver.add_method("/center", "ifff", handle_center)
osc_receiver.start()

while True:
    time.sleep(1)
