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
import math
import collections
from pybrain.tools.shortcuts import buildNetwork
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.datasets import SupervisedDataSet
import numpy
from angle_parameters import radians_to_vector2d, vector2d_to_radians

class CircularInput:
    def __init__(self):
        self._t = 0

    def __str__(self):
        return "CircularInput"

    def process(self, time_increment):
        self._t += time_increment
        r = self._t % (2*math.pi)
        return numpy.array([r])

class NeuralNet:
    def __init__(self):
        self._net = buildNetwork(2, 4, 2)
        self._recent_data = collections.deque(maxlen=DATASET_SIZE)
        self._trainer = BackpropTrainer(self._net, learningrate=0.001)

    def process(self, inp):
        return self._net.activate(inp)

    def train(self, inp, output):
        self._recent_data.append((inp, output))
        dataset = SupervisedDataSet(2, 2)
        for recent_in, recent_out in self._recent_data:
            dataset.addSample(recent_in, recent_out)

        self._trainer.trainOnDataset(dataset)

class ExperimentWindow(window.Window):
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("-pretrain", type=float)

    def __init__(self, *args):
        window.Window.__init__(self, *args)
        self.input = None
        self.output = None
        self.net = NeuralNet()
        self._input_history = collections.deque(maxlen=HISTORY_SIZE)
        self._input_history.extend([
                self._zero_input() for n in range(HISTORY_SIZE)])
        self._training_history = collections.deque(maxlen=HISTORY_SIZE)
        self._y_orientation = 0.0
        self._x_orientation = 0.0
        if self.args.pretrain > 0:
            self._pretrain(self.args.pretrain)

    def _zero_input(self):
        return numpy.zeros(2)

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
        correct_output = radians_to_vector2d(self.input[0])
        self._training_history.append((past_input, correct_output))
        past_training_tuple = self._training_history[0]
        self.net.train(*past_training_tuple)

    def render(self):
        self._update(self.time_increment)
        self.output = self.net.process(radians_to_vector2d(self.input[0]))

        self.configure_3d_projection(-100, 0)
        glRotatef(self._x_orientation, 1.0, 0.0, 0.0)
        glRotatef(self._y_orientation, 0.0, 1.0, 0.0)
        self._draw_unit_cube()
        self._draw_input()
        self._draw_output()

    def _draw_input(self):
        if self.input is not None:
            glColor3f(0, 1, 0)
            self._draw_angle(self.input[0])

    def _draw_output(self):
        if self.output is not None:
            glColor3f(0.5, 0.5, 1.0)
            self._draw_angle(vector2d_to_radians(self.output))

    def _draw_angle(self, r):
        z = math.cos(r)
        y = math.sin(r)
        x = 0
        glPointSize(3)
        glBegin(GL_POINTS)
        glVertex3f(x, y, z)
        glEnd()

    def _draw_unit_cube(self):
        glColor4f(0,0,0,0.2)
        glutWireCube(2.0)


parser = ArgumentParser()
window.Window.add_parser_arguments(parser)
ExperimentWindow.add_parser_arguments(parser)
args = parser.parse_args()

input_generator = CircularInput()

window.run(ExperimentWindow, args)
