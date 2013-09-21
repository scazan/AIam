HISTORY_SIZE = 100
DATASET_SIZE = 10

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from argparse import ArgumentParser
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import window
from vector import Vector3d
import math
import collections
from pybrain.tools.shortcuts import buildNetwork
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.datasets import SupervisedDataSet
from bvh_reader import bvh_reader

class BvhInput:
    def __init__(self, filename):
        self._filename = filename
        self._reader = bvh_reader.BvhReader(filename)
        self._reader.read()
        self._t = 0

    def __str__(self):
        return "BvhInput(%r)" % self._filename

    def process(self, time_increment):
        self._t += time_increment
        vertices = self._reader.get_skeleton_vertices(self._t * args.bvh_speed)
        hips = self._normalize(self._vertex_to_vector3d(vertices[0]))
        return hips

    def _vertex_to_vector3d(self, v):
        return Vector3d(v[0], v[1], v[2])

    def _normalize(self, v):
        return Vector3d(
            (v.x - self._reader.skeleton.minx) / args.bvh_scale,
            (v.y - self._reader.skeleton.miny) / args.bvh_scale,
            (v.z - self._reader.skeleton.minz) / args.bvh_scale)

class CircularInput:
    def __init__(self):
        self._t = 0

    def __str__(self):
        return "CircularInput"

    def process(self, time_increment):
        self._t += time_increment
        z = math.cos(self._t)
        y = math.sin(self._t)
        x = 0
        return Vector3d(x, y, z)

class NeuralNet:
    def __init__(self):
        self._net = buildNetwork(3, 6, 3)
        self._recent_data = collections.deque(maxlen=DATASET_SIZE)
        self._trainer = BackpropTrainer(self._net, learningrate=0.001)

    def process(self, inp):
        net_in = inp.v
        net_out = self._net.activate(net_in)
        return Vector3d(*net_out)

    def train(self, inp, output):
        self._recent_data.append((inp.v, output.v))
        dataset = SupervisedDataSet(3, 3)
        for recent_in, recent_out in self._recent_data:
            dataset.addSample(recent_in, recent_out)

        self._trainer.trainOnDataset(dataset)

class ExperimentWindow(window.Window):
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("-pretrain", type=float)
        parser.add_argument("-bvh")
        parser.add_argument("-bvh-speed", type=float, default=1.0)
        parser.add_argument("-bvh-scale", type=float, default=40)

    def __init__(self, *args):
        window.Window.__init__(self, *args)
        self.input = None
        self.output = None
        self.net = NeuralNet()
        self._input_history = collections.deque(maxlen=HISTORY_SIZE)
        self._input_history.extend([
                Vector3d(0,0,0) for n in range(HISTORY_SIZE)])
        self._training_history = collections.deque(maxlen=HISTORY_SIZE)
        self._y_orientation = 0.0
        self._x_orientation = 0.0
        if self.args.pretrain > 0:
            self._pretrain(self.args.pretrain)

    def _pretrain(self, duration):
        print "pre-training..."
        t = 0
        time_increment = 1.0 / 50
        while t < duration:
            self._update(time_increment)
            t += time_increment
        print "ok"

    def _update(self, time_increment):
        self.input = input_generator.process(time_increment)
        self._input_history.append(self.input)
        past_input = self._input_history[0]
        self._training_history.append((past_input, self.input))
        past_training_tuple = self._training_history[0]
        self.net.train(*past_training_tuple)

    def render(self):
        self._update(self.time_increment)
        self.output = self.net.process(self.input)

        self.configure_3d_projection(-100, 0)
        glRotatef(self._x_orientation, 1.0, 0.0, 0.0)
        glRotatef(self._y_orientation, 0.0, 1.0, 0.0)
        self._draw_unit_cube()
        self._draw_input()
        self._draw_output()

    def _draw_input(self):
        if self.input:
            glColor3f(0, 1, 0)
            self._draw_point(self.input)

    def _draw_output(self):
        if self.output:
            glColor3f(0.5, 0.5, 1.0)
            self._draw_point(self.output)

    def _draw_point(self, p):
        glPointSize(3)
        glBegin(GL_POINTS)
        glVertex3f(p.x, p.y, p.z)
        glEnd()

    def _draw_unit_cube(self):
        glColor4f(0,0,0,0.2)
        glutWireCube(2.0)


parser = ArgumentParser()
window.Window.add_parser_arguments(parser)
ExperimentWindow.add_parser_arguments(parser)
args = parser.parse_args()

if args.bvh:
    input_generator = BvhInput(args.bvh)
else:
    input_generator = CircularInput()

print "input: %s" % input_generator

window.run(ExperimentWindow, args)
