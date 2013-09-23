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
from bvh_reader import bvh_reader
from bvh_reader.geo import vertex
import numpy

class BvhInput:
    def __init__(self):
        self._t = 0

    def process(self, time_increment):
        self._t += time_increment
        vertices = bvh_reader.get_skeleton_vertices(self._t * args.bvh_speed)
        normalized_vectors = numpy.array(
            [bvh_reader.normalize_vector(bvh_reader.vertex_to_vector(vertex))
             for vertex in vertices])
        return normalized_vectors

class NeuralNet:
    def __init__(self, vector_size):
        self._vector_size = vector_size
        num_hidden_nodes = vector_size * 2
        self._net = buildNetwork(vector_size, num_hidden_nodes, vector_size)
        self._recent_data = collections.deque(maxlen=DATASET_SIZE)
        self._trainer = BackpropTrainer(self._net, learningrate=0.001)

    def process(self, inp):
        return self._net.activate(inp)

    def train(self, inp, output):
        self._recent_data.append((inp, output))
        dataset = SupervisedDataSet(self._vector_size, self._vector_size)
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
        self._input_vectors = None
        self._output_vectors = None
        self.net = NeuralNet(bvh_reader.num_joints * 3)
        self._input_history = collections.deque(maxlen=HISTORY_SIZE)
        self._input_history.extend([
                self._zero_input() for n in range(HISTORY_SIZE)])
        self._training_history = collections.deque(maxlen=HISTORY_SIZE)
        self._y_orientation = 0.0
        self._x_orientation = 0.0
        if self.args.pretrain > 0:
            self._pretrain(self.args.pretrain)

    def _zero_input(self):
        return numpy.zeros(bvh_reader.num_joints * 3)

    def _pretrain(self, duration):
        print "pre-training..."
        t = 0
        time_increment = 1.0 / 50
        while t < duration:
            self._update(time_increment)
            t += time_increment
        print "ok"

    def _update(self, time_increment):
        self._input_vectors = input_generator.process(time_increment)
        self._net_input = self._input_vectors.flatten()
        self._input_history.append(self._net_input)
        past_input = self._input_history[0]
        self._training_history.append((past_input, self._net_input))
        past_training_tuple = self._training_history[0]
        self.net.train(*past_training_tuple)

    def render(self):
        self._update(self.time_increment)
        net_output = self.net.process(self._net_input)
        self._output_vectors = net_output.reshape([bvh_reader.num_joints, 3])

        self.configure_3d_projection(-100, 0)
        glRotatef(self._x_orientation, 1.0, 0.0, 0.0)
        glRotatef(self._y_orientation, 0.0, 1.0, 0.0)
        self._draw_unit_cube()
        self._draw_input()
        self._draw_output()

        # self._print_pose(self._input_vectors)

    def _print_pose(self, normalized_vectors):
        vertices = [bvh_reader.vector_to_vertex(bvh_reader.skeleton_scale_vector(vector))
                    for vector in normalized_vectors]
        bvh_reader.print_pose(vertices)

    def _draw_input(self):
        if self._input_vectors is not None:
            glColor3f(0, 1, 0)
            self._draw_skeleton(self._input_vectors)

    def _draw_output(self):
        if self._output_vectors is not None:
            glColor3f(0.5, 0.5, 1.0)
            self._draw_skeleton(self._output_vectors)

    def _draw_skeleton(self, normalized_vectors):
        glLineWidth(2.0)
        vertices = [bvh_reader.vector_to_vertex(bvh_reader.skeleton_scale_vector(vector))
                    for vector in normalized_vectors]
        edges = bvh_reader.vertices_to_edges(vertices)
        for edge in edges:
            vector1 = bvh_reader.normalize_vector(bvh_reader.vertex_to_vector(edge.v1))
            vector2 = bvh_reader.normalize_vector(bvh_reader.vertex_to_vector(edge.v2))
            self._draw_line(vector1, vector2)

    def _draw_line(self, v1, v2):
        glBegin(GL_LINES)
        glVertex3f(*v1)
        glVertex3f(*v2)
        glEnd()

    def _draw_unit_cube(self):
        glLineWidth(1.0)
        glColor4f(0,0,0,0.2)
        glutWireCube(2.0)


parser = ArgumentParser()
window.Window.add_parser_arguments(parser)
ExperimentWindow.add_parser_arguments(parser)
args = parser.parse_args()

bvh_reader = bvh_reader.BvhReader(args.bvh)
bvh_reader.scale_factor = args.bvh_scale
bvh_reader.read()
input_generator = BvhInput()

window.run(ExperimentWindow, args)
