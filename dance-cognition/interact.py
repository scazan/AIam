from simple_osc_receiver import OscReceiver
from simple_osc_sender import OscSender
import time
from argparse import ArgumentParser
import imp
from vector import *
from states import state_machine
import interpret
from config_loader import load_config

def receive_torso_position(path, args, types, src, user_data):
    global normalized_torso_position
    position_tuple = args
    position_relative_to_camera = Vector3d(*position_tuple)
    normalized_torso_position = position_in_unit_cube(position_relative_to_camera)
    if verbose:
        print "torso", position_tuple
        print " =>", normalized_torso_position

def receive_center_of_mass_position(path, args, types, src, user_data):
    global normalized_center_of_mass_position
    position_tuple = args
    position_relative_to_camera = Vector3d(*position_tuple)
    normalized_center_of_mass_position = position_in_unit_cube(position_relative_to_camera)
    if verbose:
        print "center_of_mass", position_tuple
        print " =>", normalized_center_of_mass_position

def position_in_unit_cube(position_relative_to_camera):
    global config
    p = position_relative_to_camera - config.center
    p.x /= config.size.x
    p.y /= config.size.y
    p.z /= config.size.z
    return p

def refresh():
    if normalized_torso_position is None:
        return

    global last_refresh_time
    now = time.time()
    if last_refresh_time is None:
        time_increment = 0.0
    else:
        time_increment = now - last_refresh_time
    last_refresh_time = now

    input_position = normalized_torso_position
    interpreter.process_input(input_position, time_increment)
    behaviour.process_input(input_position, time_increment)

    osc_sender.send("/input_position", *input_position)
    osc_sender.send("/normalized_torso_position", *normalized_torso_position)
    if normalized_center_of_mass_position:
        osc_sender.send("/normalized_center_of_mass_position", *normalized_center_of_mass_position)

    output_inter_state_position = behaviour.output()
    if output_inter_state_position:
        if output_inter_state_position.relative_position < 0 or \
           output_inter_state_position.relative_position > 1:
            print "WARNING: illegal relative_position in output: %r" % \
                output_inter_state_position.relative_position
        osc_sender.send("/position",
                        output_inter_state_position.source_state.name,
                        output_inter_state_position.destination_state.name,
                        output_inter_state_position.relative_position)

def observed_state(state):
    osc_sender.send("/observed_state", state.name)

parser = ArgumentParser()
parser.add_argument("-behaviour", type=str, default="follower")
parser.add_argument("-config", type=str)
parser.add_argument("-refresh-rate", type=float, default=60.0)
parser.add_argument("-verbose", action="store_true")
args = parser.parse_args()
verbose = args.verbose

config = load_config(args.config)

interpreter = interpret.Interpreter()
interpreter.add_callback(interpret.STATE, observed_state)

behaviour_module = imp.load_source(args.behaviour, "behaviours/%s.py" % args.behaviour)
behaviour = behaviour_module.Behaviour(state_machine, interpreter)

osc_sender = OscSender(7892)
normalized_torso_position = None
normalized_center_of_mass_position = None
last_refresh_time = None
osc_receiver = OscReceiver(7891, listen="localhost")
osc_receiver.add_method("/joint/torso", "fff", receive_torso_position)
osc_receiver.add_method("/com", "fff", receive_center_of_mass_position)
osc_receiver.start(auto_serve=True)

refresh_interval = 1.0 / args.refresh_rate
while True:
    refresh()
    time.sleep(refresh_interval)
