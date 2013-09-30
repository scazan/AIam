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
from bvh_reader import bvh_reader

class Stimulus:
    def __init__(self):
        self._t = 0

    def proceed(self, time_increment):
        self._t += time_increment

class ExperimentWindow(window.Window):
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

def run_experiment(_student, _stimulus, window_class, args):
    global bvh_reader, teacher, student, stimulus
    student = _student
    stimulus = _stimulus

    if args.bvh:
        bvh_reader = bvh_reader.BvhReader(args.bvh)
        bvh_reader.scale_factor = args.bvh_scale
        bvh_reader.read()

    if args.shuffle_input:
        teacher = ShufflingTeacher(stimulus)
    else:
        teacher = LiveTeacher(stimulus)

    if args.pretrain > 0:
        pretrain(student, teacher, args.pretrain)

    if args.plot:
        LearningPlotter(student, teacher, args.plot_duration).plot(args.plot)
    else:
        window.run(window_class, args)
