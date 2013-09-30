import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from argparse import ArgumentParser
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import window
import math
from bvh_reader import bvh_reader
from backprop_net import BackpropNet
from teacher import *
from learning_plotter import LearningPlotter

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

    def get_duration(self):
        return bvh_reader.get_duration() / args.bvh_speed

class CircularStimulus(Stimulus):
    def __str__(self):
        return "CircularStimulus"

    def get_value(self):
        z = math.cos(self._t)
        y = math.sin(self._t)
        x = 0
        return [x, y, z]

    def get_duration(self):
        return 2 * math.pi

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
parser.add_argument("-shuffle-input", action="store_true")
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

if args.shuffle_input:
    teacher = ShufflingTeacher(stimulus)
else:
    teacher = LiveTeacher(stimulus)

student = BackpropNet(3, 6, 3)

if args.pretrain > 0:
    pretrain(student, teacher, args.pretrain)

if args.plot:
    LearningPlotter(student, teacher, args.plot_duration).plot(args.plot)
else:
    window.run(ExperimentWindow, args)
