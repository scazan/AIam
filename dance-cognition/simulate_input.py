from argparse import ArgumentParser
from simple_osc_sender import OscSender
import time
import random
from vector import Vector3d
from input_generators.dataset_transitions import Generator

def noise():
    return Vector3d(
        random.uniform(-1.0, 1.0),
        random.uniform(-1.0, 1.0),
        random.uniform(-1.0, 1.0)) * 0.01

parser = ArgumentParser()
parser.add_argument("-refresh-rate", type=float, default=60.0)
args = parser.parse_args()

osc_sender = OscSender(7891)

refresh_interval = 1.0 / args.refresh_rate
generator = Generator()
while True:
    generator.update(refresh_interval)
    input_position = generator.position() + noise()
    osc_sender.send("/joint/torso", *input_position)
    time.sleep(refresh_interval)
