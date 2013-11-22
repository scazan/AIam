#!/usr/bin/env python

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from argparse import ArgumentParser
from bvh_reader import bvh_reader as bvh_reader_module
import math
from PIL import Image
import numpy

class JointAnglePlotter:
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("bvh")
        parser.add_argument("output")
        parser.add_argument("-radius", type=int, default=100)
        parser.add_argument("-spacing", type=int, default=10)

    def __init__(self, args):
        self.args = args
        self.bvh_reader = bvh_reader_module.BvhReader(args.bvh)
        self.bvh_reader.read()

        self.width = self.args.spacing * 6 + self.args.radius * 6
        self.height = self.args.spacing * 2 + self.args.radius * 2
        self._create_outputs()

        self.dimension_plots = {}
        n = 0
        for channel in ["Xrotation", "Yrotation", "Zrotation"]:
            self.dimension_plots[channel] = {
                "cx": self.args.spacing * (1+n*2) + self.args.radius * (n*2) + self.args.radius,
                "cy": self.args.spacing + self.args.radius}
            n += 1

    def _create_outputs(self):
        hips = self.bvh_reader.skeleton.get_hips(0)
        self.outputs = []
        self._identify_joints_with_rotation(hips)

        for output in self.outputs:
            image_buffer = numpy.empty(self.width * self.height * 3)
            image_buffer.fill(255)
            output["image_buffer"] = image_buffer

    def _identify_joints_with_rotation(self, joint):
        if joint.rotation_definition:
            joint.index_with_rotation = len(self.outputs)
            self.outputs.append({"joint": joint})
        for child in joint.children:
            self._identify_joints_with_rotation(child)

    def plot(self):
        for n in range(self.bvh_reader.skeleton.num_frames):
            hips = self.bvh_reader.skeleton.get_hips(n)
            self._process_joint_recurse(hips)
        self._save_images()

    def _save_images(self):
        n = 0
        for output in self.outputs:
            output_path = "%s%03d_%s.png" % (
                args.output, n, output["joint"].name)
            image = Image.fromstring("RGB", (self.width, self.height),
                                     data=self._array_to_string(output["image_buffer"]))
            image.save(output_path)
            n += 1

    def _array_to_string(self, xs):
        return "".join([chr(int(x)) for x in xs])

    def _process_joint_recurse(self, joint):
        if joint.rotation_definition:
            self._process_rotation_definition(joint)
        for child in joint.children:
            self._process_joint_recurse(child)

    def _process_rotation_definition(self, joint):
        image_buffer = self.outputs[joint.index_with_rotation]["image_buffer"]
        for channel, degrees in joint.rotation_definition:
            self._plot_angle(image_buffer, channel, degrees)

    def _plot_angle(self, image_buffer, channel, degrees):
        dimension_plot = self.dimension_plots[channel]
        x = int(dimension_plot["cx"] + self.args.radius * math.cos(math.radians(degrees)))
        y = int(dimension_plot["cy"] + self.args.radius * math.sin(math.radians(degrees)))
        p = (y * self.width + x) * 3
        image_buffer[p] = 0
        image_buffer[p+1] = 0
        image_buffer[p+2] = 0

parser = ArgumentParser()
JointAnglePlotter.add_parser_arguments(parser)
args = parser.parse_args()
JointAnglePlotter(args).plot()
