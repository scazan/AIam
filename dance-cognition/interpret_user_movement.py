import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/connectivity")
from osc_receiver import OscReceiver
import time

OSC_PORT = 15002

def handle_joint_data(path, args, types, src, user_data):
    joint_name, x, y, z = args
    print "%s: %s %s %s" % (joint_name, x, y, z)

osc_receiver = OscReceiver(OSC_PORT)
osc_receiver.add_method("/joint", "sfff", handle_joint_data)
osc_receiver.start()

while True:
    time.sleep(1)
