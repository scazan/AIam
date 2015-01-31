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
parser.add_argument("--type", choices=["gnuplot", "svg"], default="gnuplot")
args = parser.parse_args()
model = load_model(args.model)[0]

def split_observations_into_segments(observations, sensitivity):
    segments = []
    segment = []
    previous_observation = None
    for observation in observations:
        if previous_observation is not None and \
                numpy.linalg.norm(observation - previous_observation) > sensitivity:
            segments.append(segment)
            segment = []
        segment.append(observation)
        previous_observation = observation
    return segments

if args.split_sensitivity:
    segments = split_observations_into_segments(
        model.normalized_observed_reductions, args.split_sensitivity)
else:
    segments = [model.normalized_observed_reductions]

class gnuplotGenerator:
    def generate(self, segments, out):
        for observations in segments:
            for observation in observations:
                print >>out, " ".join([str(value) for value in observation])
            print >>out

        global args
        if args.segments_output:
            n = 0
            for segment in segments:
                out = open(args.segments_output % n, "w")
                for observation in segment:
                    print >>out, " ".join([str(value) for value in observation])
                out.close()
                n += 1

generator = eval("%sGenerator" % args.type)()
out = open(args.output, "w")
generator.generate(segments, out)
out.close()

if args.split_sensitivity:
    print "Plotted %d observations in %d segments" % (
        len(model.normalized_observed_reductions), len(segments))
else:
    print "Plotted %d observations" % len(model.normalized_observed_reductions)
