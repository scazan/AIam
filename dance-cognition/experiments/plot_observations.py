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
parser.add_argument("--segments-output")
args = parser.parse_args()
model = load_model(args.model)[0]

segments = []
segment = []
previous_observation = None
out = open(args.output, "w")
for observation in model.normalized_observed_reductions:
    if previous_observation is not None and args.split_sensitivity and \
            numpy.linalg.norm(observation - previous_observation) > args.split_sensitivity:
        segments.append(segment)
        segment = []
        print >>out
    segment.append(observation)
    previous_observation = observation
    print >>out, " ".join([str(value) for value in observation])
out.close()

if args.segments_output:
    n = 0
    for segment in segments:
        out = open(args.segments_output % n, "w")
        for observation in segment:
            print >>out, " ".join([str(value) for value in observation])
        out.close()
        n += 1

if args.split_sensitivity:
    print "Plotted %d observations in %d segments" % (
        len(model.normalized_observed_reductions), len(segments))
else:
    print "Plotted %d observations" % len(model.normalized_observed_reductions)
