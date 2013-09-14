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
from vector import Vector2d
import math
import collections
from pybrain.tools.shortcuts import buildNetwork
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.datasets import SupervisedDataSet

class InputGenerator:
    def __init__(self):
        self._t = 0

    def process(self, time_increment):
        self._t += time_increment
        x = math.cos(self._t)
        y = math.sin(self._t)
        return Vector2d(x, y)

class NeuralNet:
    def __init__(self):
        self._net = buildNetwork(2, 3, 2)
        self._recent_data = collections.deque(maxlen=DATASET_SIZE)
        self._trainer = BackpropTrainer(self._net, learningrate=0.001)

    def process(self, inp):
        net_in = inp.v
        net_out = self._net.activate(net_in)
        return Vector2d(*net_out)

    def train(self, inp, output):
        self._recent_data.append((inp.v, output.v))
        dataset = SupervisedDataSet(2, 2)
        for recent_in, recent_out in self._recent_data:
            dataset.addSample(recent_in, recent_out)

        self._trainer.trainOnDataset(dataset)

class Frame(window.Frame):
    def draw_point(self, p):
        glPointSize(3)
        glBegin(GL_POINTS)
        glVertex2f((p.x/2 + 0.5) * self.width,
                   (p.y/2 + 0.5) * self.height)
        glEnd()

class InputOutputFrame(Frame):
    def render(self):
        if self.window.input:
            glColor3f(0, 1, 0)
            self.draw_point(self.window.input)
        if self.window.output:
            glColor3f(0.5, 0.5, 1.0)
            self.draw_point(self.window.output)

class ExperimentWindow(window.Window):
    def __init__(self, *args):
        window.Window.__init__(self, *args)
        self.input_generator = InputGenerator()
        self.input = None
        self.output = None
        self.net = NeuralNet()
        self._input_history = collections.deque(maxlen=HISTORY_SIZE)
        self._input_history.extend([
                Vector2d(0,0) for n in range(HISTORY_SIZE)])
        self._training_history = collections.deque(maxlen=HISTORY_SIZE)
        self.input_and_output_frame = InputOutputFrame(
            self, left=100, top=100, width=200, height=200)

    def render(self):
        self.input = self.input_generator.process(self.time_increment)
        self._input_history.append(self.input)
        self.past_input = self._input_history[0]
        self.output = self.net.process(self.input)
        self._training_history.append((self.past_input, self.input))
        self.net.train(*self._training_history[0])

parser = ArgumentParser()
window.Window.add_parser_arguments(parser)
args = parser.parse_args()
window.run(ExperimentWindow, args)
