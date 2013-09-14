#!/usr/bin/perl

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from cgkit.asfamc import AMCReader
import window
from argparse import ArgumentParser
import threading
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

class AmcViewer(window.Window):
    def __init__(self, *args):
        global amc_data_reader
        window.Window.__init__(self, *args)
        self.data_reader = amc_data_reader

    def render(self):
        self.configure_3d_projection(100, 0)
        if self.data_reader.data:
            self._draw_points()

    def _draw_points(self):
        glPointSize(2.0)
        glBegin(GL_POINTS)
        for joint, point in self.data_reader.data:
            if len(point) == 3:
                glVertex3f(*point)
        glEnd()

class AmcDataReader(AMCReader):
    def __init__(self, *args):
        AMCReader.__init__(self, *args)
        self.data = None

    def onFrame(self, framenr, data):
        self.data = data

parser = ArgumentParser()
window.Window.add_parser_arguments(parser)
parser.add_argument("-amc")
args = parser.parse_args()

amc_data_reader = AmcDataReader(args.amc)
amc_data_reader_thread = threading.Thread(target=amc_data_reader.read)
amc_data_reader_thread.daemon = True
amc_data_reader_thread.start()
window.run(AmcViewer, args)
