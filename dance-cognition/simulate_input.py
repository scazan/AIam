from argparse import ArgumentParser
from simple_osc_sender import OscSender
import time
import random
from vector import Vector3d
import imp

def noise():
    return Vector3d(
        random.uniform(-1.0, 1.0),
        random.uniform(-1.0, 1.0),
        random.uniform(-1.0, 1.0)) * args.noise

parser = ArgumentParser()
parser.add_argument("-generator", type=str, default="dataset_transitions")
parser.add_argument("-refresh-rate", type=float, default=60.0)
parser.add_argument("-noise", type=float, default=0.01)
args, unknown_args = parser.parse_known_args()

generator_module = imp.load_source("generator", "input_generators/%s.py" % args.generator)
generator_module.Generator.add_parser_arguments(parser)
args = parser.parse_args()
generator = generator_module.Generator(args)

osc_sender = OscSender(7891)
refresh_interval = 1.0 / args.refresh_rate
while True:
    generator.update(refresh_interval)
    input_position = generator.position() + noise()
    osc_sender.send("/joint/torso", *input_position)
    time.sleep(refresh_interval)
