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

parser = ArgumentParser()
parser.add_argument("model")
parser.add_argument("--output", "-o", default="observations.dat")
args = parser.parse_args()
model = load_model(args.model)[0]

out = open(args.output, "w")
for observation in model.normalized_observed_reductions:
    print >>out, " ".join([str(value) for value in observation])
out.close()
