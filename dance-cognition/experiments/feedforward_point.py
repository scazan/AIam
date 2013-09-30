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

class BvhInput(Teacher):
    def __str__(self):
        return "BvhInput"

    def get_input(self):
        vertices = bvh_reader.get_skeleton_vertices(self._t * args.bvh_speed)
        hips = bvh_reader.normalize_vector(bvh_reader.vertex_to_vector(vertices[0]))
        return hips

class CircularInput(Teacher):
    def __str__(self):
        return "CircularInput"

    def get_input(self):
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
    def __init__(self):
        self._t = 0

    def proceed(self, time_increment):
        self._t += time_increment

    def get_output(self):
        return self.get_input()

    def judge_error(self, expected_output, output):
        return numpy.linalg.norm(expected_output - output)

class Student:
    def __init__(self, teacher, pretrain_duration):
        self._teacher = teacher
        self._net = NeuralNet()
        self._input_history = collections.deque(maxlen=HISTORY_SIZE)
        self._training_history = collections.deque(maxlen=HISTORY_SIZE)
        if pretrain_duration > 0:
            self._pretrain(pretrain_duration)

    def _pretrain(self, duration):
        print "pre-training..."
        t = 0
        time_increment = 1.0 / 50
        while t < duration:
            inp = self._teacher.get_input()
            output = self._teacher.get_output()
            self._teacher.proceed(time_increment)
            self.train(inp, output)
            t += time_increment
        print "ok"

    def train(self, inp, output):
        self._input_history.append(inp)

        if self.received_enough_input():
            past_input = self._input_history[0]
            self._training_history.append((past_input, output))
            past_training_tuple = self._training_history[0]
            self._net.train(*past_training_tuple)

    def received_enough_input(self):
        return len(self._input_history) == HISTORY_SIZE

    def process(self, inp):
        return self._net.process(inp)

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
            inp = self._teacher.get_input()
            expected_output = self._teacher.get_output()
            self._teacher.proceed(time_increment)
            self._student.train(inp, expected_output)
            if self._student.received_enough_input():
                output = self._student.process(inp)
                error = self._teacher.judge_error(expected_output, output)
                print >>f, t, error
            t += time_increment
        f.close()

class ExperimentWindow(window.Window):
    def __init__(self, *args):
        window.Window.__init__(self, *args)
        self._y_orientation = 0.0
        self._x_orientation = 0.0

    def render(self):
        inp = teacher.get_input()
        expected_output = teacher.get_output()
        teacher.proceed(self.time_increment)
        student.train(inp, expected_output)

        self.configure_3d_projection(-100, 0)
        glRotatef(self._x_orientation, 1.0, 0.0, 0.0)
        glRotatef(self._y_orientation, 0.0, 1.0, 0.0)
        self._draw_unit_cube()
        self._draw_input(inp)

        if student.received_enough_input():
            output = student.process(inp)
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
    teacher = BvhInput()
else:
    teacher = CircularInput()

print "teacher: %s" % teacher

student = Student(teacher, args.pretrain)

if args.plot:
    LearningPlotter(student, teacher, args.plot_duration).plot(args.plot)
else:
    window.run(ExperimentWindow, args)
