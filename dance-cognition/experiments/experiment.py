import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from argparse import ArgumentParser
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import window
import math
from backprop_net import BackpropNet
from teacher import *
from learning_plotter import LearningPlotter
from bvh_reader import bvh_reader as bvh_reader_module

class Stimulus:
    def __init__(self):
        self._t = 0

    def proceed(self, time_increment):
        self._t += time_increment

class ExperimentWindow(window.Window):
    def __init__(self, experiment, args):
        self.bvh_reader = experiment.bvh_reader
        window.Window.__init__(self, args)

    def render(self):
        if teacher.collected_enough_training_data():
            inp = teacher.get_input()
            expected_output = teacher.get_output()
            student.train(inp, expected_output)
        teacher.proceed(self.time_increment)

        self.configure_3d_projection(-100, 0)
        self._draw_unit_cube()

        inp = stimulus.get_value()
        output = student.process(inp)
        self.draw_input(inp)
        self.draw_output(output)

    def _draw_unit_cube(self):
        glLineWidth(1.0)
        glColor4f(0,0,0,0.2)
        glutWireCube(2.0)

def add_parser_arguments(parser):
    window.Window.add_parser_arguments(parser)
    parser.add_argument("-pretrain", type=float)
    parser.add_argument("-bvh")
    parser.add_argument("-bvh-speed", type=float, default=1.0)
    parser.add_argument("-bvh-scale", type=float, default=40)
    parser.add_argument("-plot", type=str)
    parser.add_argument("-plot-duration", type=float, default=10)
    parser.add_argument("-shuffle-input", action="store_true")


class Experiment:
    def __init__(self, window_class, args):
        self.args = args
        self.window_class = window_class
        if args.bvh:
            self.bvh_reader = bvh_reader_module.BvhReader(args.bvh)
            self.bvh_reader.scale_factor = args.bvh_scale
            self.bvh_reader.read()
        else:
            self.bvh_reader = None

    def run(self, _student, _stimulus):
        global student, teacher, stimulus
        stimulus = _stimulus
        student = _student

        if self.args.shuffle_input:
            teacher = ShufflingTeacher(stimulus)
        else:
            teacher = LiveTeacher(stimulus)

        if self.args.pretrain > 0:
            pretrain(student, teacher, self.args.pretrain)

        if self.args.plot:
            LearningPlotter(student, teacher, self.args.plot_duration).plot(self.args.plot)
        else:
            self.window_class(self, self.args).run()
