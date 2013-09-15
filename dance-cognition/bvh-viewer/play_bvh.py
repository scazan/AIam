#!/usr/bin/perl

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from bvh_reader import BvhReader
import window
from argparse import ArgumentParser
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from vector import Vector3d
from camera import Camera

class BvhViewer(window.Window):
    def __init__(self, *args):
        global bvh_reader
        window.Window.__init__(self, *args)
        self.reader = bvh_reader
        self.skelscreenedges = self.reader.skeleton.make_skelscreenedges(
            DEBUG=0, arrow='none', circle=1)
        self.camera = Camera(x=0, y=15, z=35, cfx=20, parallel=0,   \
                                 ppdist=30, DEBUG=0)

    def InitGL(self):
        window.Window.InitGL(self)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def resized_window(self):
        self.camera.t[0] = int((self.reader.skeleton.minx + self.reader.skeleton.maxx)/2)
        self.camera.t[1] = int((self.reader.skeleton.miny + self.reader.skeleton.maxy)/2)
        if (self.camera.t[1] < 10): self.camera.t[1] = 10
        self.camera.t[2] = self.reader.skeleton.maxz + 100
        self.camera.yrot = 0
        self.camera.Recompute()

    def render(self):
        self._draw_skeleton()

    def _draw_skeleton(self):
        glLineWidth(2.0)
        glColor3f(0,0,0)
        self.reader.skeleton.populate_skelscreenedges(self.skelscreenedges, 100)
        for screenedge in self.skelscreenedges:
            screenedge.worldtocam(self.camera)            
            screenedge.camtoscreen(self.camera, self.width, self.height)
            self._draw_line(
                screenedge.sv1.screenx,
                screenedge.sv1.screeny,
                screenedge.sv2.screenx,
                screenedge.sv2.screeny)

    def _draw_line(self, x1, y1, x2, y2):
        glBegin(GL_LINES)
        glVertex2f(x1, y1)
        glVertex2f(x2, y2)
        glEnd()

    def _mouse_clicked(self, button, state, x, y):
        if button == GLUT_LEFT_BUTTON:
            self._dragging_orientation = (state == GLUT_DOWN)
        if state == GLUT_DOWN:
            self._drag_x_previous = x
            self._drag_y_previous = y

    def _mouse_moved(self, x, y):
        if self._dragging_orientation:
            self._y_orientation += x - self._drag_x_previous
            self._x_orientation -= y - self._drag_y_previous

parser = ArgumentParser()
window.Window.add_parser_arguments(parser)
parser.add_argument("-bvh")
args = parser.parse_args()

bvh_reader = BvhReader(args.bvh)
bvh_reader.read()

window.run(BvhViewer, args)
