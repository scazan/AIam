#!/usr/bin/env python

# gnuplot example for 3 components:
# splot "observations.dat" with points pointsize 0.1

# export to EPS:
# set terminal postscript eps color
# set out "observations.eps"
# replot

from argparse import ArgumentParser
from model import load_model

parser = ArgumentParser()
parser.add_argument("model")
parser.add_argument("--num-components", "-n", type=int, default=3)
args = parser.parse_args()
model = load_model(args.model)

for observation in model.normalized_observed_reductions:
    print " ".join([str(value) for value in observation[:args.num_components]])
