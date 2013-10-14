#!/usr/bin/env python

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from bvh_reader import bvh_reader as bvh_reader_module
from bvh_stimulus import BvhStimulus
from argparse import ArgumentParser
import numpy
import cPickle

parser = ArgumentParser()
parser.add_argument("bvh")
parser.add_argument("data")
parser.add_argument("-frame-rate", type=int, default=50)
parser.add_argument("-speed", type=float, default=1.0)
args = parser.parse_args()

def create_training_data(stimulus):
    print "creating training data..."
    training_data = []
    time_increment = 1.0 / args.frame_rate
    t = 0
    duration = stimulus.get_duration()
    while t < duration:
        datum = list(stimulus.get_value())
        training_data.append(datum)
        stimulus.proceed(time_increment)
        t += time_increment
    print "ok"
    return numpy.array(training_data)

def save_training_data(data, filename):
    print "saving training data to %s ..." % filename
    f = open(filename, "w")
    cPickle.dump(data, f)
    f.close()
    print "ok"

bvh_reader = bvh_reader_module.BvhReader(args.bvh)
bvh_reader.read()
stimulus = BvhStimulus(bvh_reader, args.speed)
data = create_training_data(stimulus)
save_training_data(data, args.data)
