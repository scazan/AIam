#!/usr/bin/python

from bvh_reader import BvhReader
from argparse import ArgumentParser
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

import window
from vector import Vector3d

class BvhViewer(window.Window):
    def __init__(self, *args):
        global bvh_reader
        window.Window.__init__(self, *args)
        self.reader = bvh_reader
        self._pose = bvh_reader.create_pose()
        self.t = 0.0

    def InitGL(self):
        window.Window.InitGL(self)
        glutMouseFunc(self._mouse_clicked)
        glutMotionFunc(self._mouse_moved)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self._y_orientation = 0.0
        self._x_orientation = 0.0

    def render(self):
        self.configure_3d_projection(-100, 0)
        glRotatef(self._x_orientation, 1.0, 0.0, 0.0)
        glRotatef(self._y_orientation, 0.0, 1.0, 0.0)
        if args.unit_cube:
            self._draw_unit_cube()
        self._draw_skeleton()
        self.t += self.time_increment

    def _draw_skeleton(self):
        t = self.t * args.speed
        if t > self.reader.get_duration() and not args.loop:
            return
        glLineWidth(2.0)
        glColor3f(0,0,0)
        self.reader.set_pose_from_frame(self._pose, t)
        edges = self._pose.get_edges()
        for edge in edges:
            self._draw_line(self._zoom_vertex(edge.v1),
                            self._zoom_vertex(edge.v2))

    def _zoom_vertex(self, vertex):
        return args.zoom * self.reader.normalize_vector(vertex)

    def _draw_line(self, v1, v2):
        glBegin(GL_LINES)
        glVertex3f(*v1)
        glVertex3f(*v2)
        glEnd()
        
    def _draw_unit_cube(self):
        glColor4f(0,0,0,0.2)
        glutWireCube(2.0)

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

    def keyPressed(self, key, x, y):
        if key == 'r':
            self._rewind()
        else:
            window.Window.keyPressed(self, key, x, y)

    def _rewind(self):
        self.t = 0

parser = ArgumentParser()
window.Window.add_parser_arguments(parser)
parser.add_argument("-bvh")
parser.add_argument("-speed", type=float, default=1.0)
parser.add_argument("-zoom", type=float, default=1.0)
parser.add_argument("-unit-cube", action="store_true")
parser.add_argument("-loop", action="store_true")
args = parser.parse_args()

bvh_reader = BvhReader(args.bvh)
bvh_reader.read()

window.run(BvhViewer, args)
