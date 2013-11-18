#!/usr/bin/env python

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from argparse import ArgumentParser
from bvh_reader import bvh_reader as bvh_reader_module
import math

class JointAnglePlotter:
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("bvh")
        parser.add_argument("output")
        parser.add_argument("-radius", type=int, default=100)
        parser.add_argument("-spacing", type=int, default=10)
        parser.add_argument("-dot-size", type=int, default=2)
        parser.add_argument("-joint")

    def __init__(self, args):
        self.args = args
        self.out = open(args.output, "w")
        self.bvh_reader = bvh_reader_module.BvhReader(args.bvh)
        self.bvh_reader.read()

        self.dimension_plots = {}
        n = 0
        for channel in ["Xrotation", "Yrotation", "Zrotation"]:
            self.dimension_plots[channel] = {
                "cx": self.args.spacing * (1+n*2) + self.args.radius * (n*2) + self.args.radius,
                "cy": self.args.spacing + self.args.radius}
            n += 1

    def plot(self):
        self._add_header()
        for n in range(self.bvh_reader.skeleton.num_frames):
            hips = self.bvh_reader.skeleton.get_hips(n)
            self._process_joint_recurse(hips)
        self._add_footer()

    def _add_header(self):
        width = self.args.spacing * 6 + self.args.radius * 6
        height = self.args.spacing * 2 + self.args.radius * 2
        self.out.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1">\n')
        self.out.write('<g>\n')
        self.out.write('<rect width="%d" height="%d" fill="white" />\n' % (
                width, height))
        for dimension_plot in self.dimension_plots.values():
            self.out.write(
                '<circle cx="%d" cy="%d" r="%d" fill="none" stroke="#f0f0f0" stroke-width="1" />\n' % (
                    dimension_plot["cx"], dimension_plot["cy"], self.args.radius))

    def _add_footer(self):
        self.out.write('</g>\n')
        self.out.write('</svg>\n')

    def _process_joint_recurse(self, joint):
        if joint.rotation_definition and joint.name == self.args.joint:
            self._process_rotation_definition(joint.rotation_definition)
        for child in joint.children:
            self._process_joint_recurse(child)

    def _process_rotation_definition(self, rotation_definition):
        for channel, degrees in rotation_definition:
            self._plot_angle(channel, degrees)

    def _plot_angle(self, channel, degrees):
        dimension_plot = self.dimension_plots[channel]
        self.out.write(
            '<circle cx="%d" cy="%d" r="%d" fill="black" fill-opacity="0.1"/>\n' % (
                dimension_plot["cx"] + self.args.radius * math.cos(math.radians(degrees)),
                dimension_plot["cy"] + self.args.radius * math.sin(math.radians(degrees)),
                self.args.dot_size))


parser = ArgumentParser()
JointAnglePlotter.add_parser_arguments(parser)
args = parser.parse_args()
JointAnglePlotter(args).plot()
