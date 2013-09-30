HISTORY_SIZE = 100

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
from bvh_reader import bvh_reader
import numpy

class Stimulus:
    def __init__(self):
        self._t = 0

    def proceed(self, time_increment):
        self._t += time_increment

class BvhStimulus(Stimulus):
    def __str__(self):
        return "BvhStimulus"

    def get_value(self):
        vertices = bvh_reader.get_skeleton_vertices(self._t * args.bvh_speed)
        hips = bvh_reader.normalize_vector(bvh_reader.vertex_to_vector(vertices[0]))
        return hips

class CircularStimulus(Stimulus):
    def __str__(self):
        return "CircularStimulus"

    def get_value(self):
        z = math.cos(self._t)
        y = math.sin(self._t)
        x = 0
        return numpy.array([x, y, z])

class NeuralNet:
    def __init__(self):
        self._net = buildNetwork(3, 6, 3)
        self._trainer = BackpropTrainer(self._net, learningrate=0.001)

    def process(self, inp):
        return self._net.activate(inp)

    def train(self, inp, output):
        dataset = SupervisedDataSet(3, 3)
        dataset.addSample(inp, output)
        self._trainer.trainOnDataset(dataset)

class Teacher:
    def __init__(self, stimulus):
        self._stimulus = stimulus
        self._input_history = collections.deque(maxlen=HISTORY_SIZE)
        self._training_history = collections.deque(maxlen=HISTORY_SIZE)
        self._add_training_tuple_to_history()

    def _add_training_tuple_to_history(self):
        recent_input = self._stimulus.get_value()
        self._input_history.append(recent_input)
        if self.collected_enough_training_data():
            past_input = self._input_history[0]
            self._training_history.append((past_input, recent_input))

    def proceed(self, time_increment):
        self._stimulus.proceed(time_increment)
        self._add_training_tuple_to_history()

    def get_input(self):
        past_input, past_output = self._training_history[0]
        return past_input

    def get_output(self):
        past_input, past_output = self._training_history[0]
        return past_output

    def collected_enough_training_data(self):
        return len(self._input_history) == HISTORY_SIZE

    def judge_error(self, expected_output, output):
        return numpy.linalg.norm(expected_output - output)

class LearningPlotter:
    def __init__(self, student, teacher, duration):
        self._student = student
        self._teacher = teacher
        self._duration = duration

    def plot(self, filename):
        f = open(filename, "w")
        t = 0
        time_increment = 1.0 / 50
        while t < self._duration:
            if self._teacher.collected_enough_training_data():
                inp = self._teacher.get_input()
                expected_output = self._teacher.get_output()
                self._student.train(inp, expected_output)
                output = self._student.process(inp)
                error = self._teacher.judge_error(expected_output, output)
                print >>f, t, error
            self._teacher.proceed(time_increment)
            t += time_increment
        f.close()

class ExperimentWindow(window.Window):
    def __init__(self, *args):
        window.Window.__init__(self, *args)
        self._y_orientation = 0.0
        self._x_orientation = 0.0

    def render(self):
        if teacher.collected_enough_training_data():
            inp = teacher.get_input()
            expected_output = teacher.get_output()
            student.train(inp, expected_output)
        teacher.proceed(self.time_increment)

        self.configure_3d_projection(-100, 0)
        glRotatef(self._x_orientation, 1.0, 0.0, 0.0)
        glRotatef(self._y_orientation, 0.0, 1.0, 0.0)
        self._draw_unit_cube()

        inp = stimulus.get_value()
        output = student.process(inp)
        self._draw_input(inp)
        self._draw_output(output)

    def _draw_input(self, inp):
        glColor3f(0, 1, 0)
        self._draw_point(inp)

    def _draw_output(self, output):
        glColor3f(0.5, 0.5, 1.0)
        self._draw_point(output)

    def _draw_point(self, p):
        glPointSize(3)
        glBegin(GL_POINTS)
        glVertex3f(p[0], p[1], p[2])
        glEnd()

    def _draw_unit_cube(self):
        glColor4f(0,0,0,0.2)
        glutWireCube(2.0)

def pretrain(student, teacher, duration):
    print "pre-training..."
    t = 0
    time_increment = 1.0 / 50
    while t < duration:
        if teacher.collected_enough_training_data():
            inp = teacher.get_input()
            output = teacher.get_output()
            student.train(inp, output)
        teacher.proceed(time_increment)
        t += time_increment
    print "ok"


parser = ArgumentParser()
parser.add_argument("-pretrain", type=float)
parser.add_argument("-bvh")
parser.add_argument("-bvh-speed", type=float, default=1.0)
parser.add_argument("-bvh-scale", type=float, default=40)
parser.add_argument("-plot", type=str)
parser.add_argument("-plot-duration", type=float, default=10)
window.Window.add_parser_arguments(parser)
args = parser.parse_args()

if args.bvh:
    bvh_reader = bvh_reader.BvhReader(args.bvh)
    bvh_reader.scale_factor = args.bvh_scale
    bvh_reader.read()
    stimulus = BvhStimulus()
else:
    stimulus = CircularStimulus()

print "stimulus: %s" % stimulus

teacher = Teacher(stimulus)
student = NeuralNet()

if args.pretrain > 0:
    pretrain(student, teacher, args.pretrain)

if args.plot:
    LearningPlotter(student, teacher, args.plot_duration).plot(args.plot)
else:
    window.run(ExperimentWindow, args)
