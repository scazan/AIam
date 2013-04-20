from simple_osc_receiver import OscReceiver
from simple_osc_sender import OscSender
import time
from argparse import ArgumentParser
import imp
from vector import *
from states import state_machine

def receive_torso_position(path, args, types, src, user_data):
    global input_position
    position_tuple = args
    position_relative_to_camera = Vector3d(*position_tuple)
    input_position = position_in_unit_cube(position_relative_to_camera)

def position_in_unit_cube(position_relative_to_camera):
    global config
    p = position_relative_to_camera - config.center
    p.x /= config.size.x
    p.y /= config.size.y
    p.z /= config.size.z
    return p

def refresh():
    global last_refresh_time
    now = time.time()
    if last_refresh_time is None:
        time_increment = 0.0
    else:
        time_increment = now - last_refresh_time
    behaviour.process_input(input_position, time_increment)
    output_inter_state_position = behaviour.output()
    osc_sender.send("/input_position", *input_position)
    osc_sender.send("/position",
                    output_inter_state_position.source_state.name,
                    output_inter_state_position.destination_state.name,
                    output_inter_state_position.relative_position)
    last_refresh_time = now

parser = ArgumentParser()
parser.add_argument("-behaviour", type=str, default="follower")
parser.add_argument("-config", type=str, default="default")
parser.add_argument("-refresh-rate", type=float, default=60.0)
args = parser.parse_args()

config = imp.load_source("config", "input_data/%s/config.py" % args.config)
config.center = Vector3d(*config.center)
config.size = Vector3d(*config.size)

behaviour_module = imp.load_source(args.behaviour, "behaviours/%s.py" % args.behaviour)
behaviour = behaviour_module.Behaviour(state_machine)

osc_sender = OscSender(7892)
input_position = Vector3d(0.0, 0.0, 0.0)
last_refresh_time = None
osc_receiver = OscReceiver(7891, listen="localhost")
osc_receiver.add_method("/joint/torso", "fff", receive_torso_position)
osc_receiver.start(auto_serve=True)

refresh_interval = 1.0 / args.refresh_rate
while True:
    refresh()
    time.sleep(refresh_interval)
