#!/usr/bin/env python

# gnuplot example for 3 components:
# set palette gray
# splot "observations.dat" with points pointsize 0.4 pointtype 7 palette

# export to EPS:
# set terminal postscript eps color
# set out "observations.eps"
# replot

from argparse import ArgumentParser
from storage import load_model
import numpy

parser = ArgumentParser()
parser.add_argument("model")
parser.add_argument("--output", "-o", default="observations.dat")
parser.add_argument("--split-sensitivity", type=float)
args = parser.parse_args()
model = load_model(args.model)[0]

num_segments = 1
out = open(args.output, "w")
previous_observation = None
for observation in model.normalized_observed_reductions:
    if previous_observation is not None and args.split_sensitivity and \
            numpy.linalg.norm(observation - previous_observation) > args.split_sensitivity:
        print >>out
        num_segments += 1
    print >>out, " ".join([str(value) for value in observation])
    previous_observation = observation
out.close()

if args.split_sensitivity:
    print "Plotted %d observations in %d segments" % (
        len(model.normalized_observed_reductions), num_segments)
else:
    print "Plotted %d observations" % len(model.normalized_observed_reductions)
