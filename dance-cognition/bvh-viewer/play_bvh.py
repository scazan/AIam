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

class BvhViewer(window.Window):
    def __init__(self, *args):
        global bvh_reader
        window.Window.__init__(self, *args)
        self.reader = bvh_reader
        self.skelscreenedges = self.reader.skeleton.make_skelscreenedges(
            DEBUG=0, arrow='none', circle=1)
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
        self._draw_unit_cube()
        self._draw_skeleton()
        self.t += self.time_increment

    def _draw_skeleton(self):
        glLineWidth(2.0)
        glColor3f(0,0,0)
        frame_index = 1 + int(self.t * args.speed / self.reader.skeleton.dt) % self.reader.skeleton.frames
        self.reader.skeleton.populate_skelscreenedges(self.skelscreenedges, frame_index)
        for screenedge in self.skelscreenedges:
            self._draw_line(self._normalize(self._screenvert_to_vector3d(screenedge.sv1)),
                            self._normalize(self._screenvert_to_vector3d(screenedge.sv2)))

    def _draw_line(self, v1, v2):
        glBegin(GL_LINES)
        glVertex3f(*v1)
        glVertex3f(*v2)
        glEnd()

    def _screenvert_to_vector3d(self, sv):
        return Vector3d(sv.tr[0], sv.tr[1], sv.tr[2])

    def _normalize(self, v):
        return Vector3d(
            (v.x - self.reader.skeleton.minx) / args.scale,
            (v.y - self.reader.skeleton.miny) / args.scale,
            (v.z - self.reader.skeleton.minz) / args.scale)
        
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

parser = ArgumentParser()
window.Window.add_parser_arguments(parser)
parser.add_argument("-bvh")
parser.add_argument("-speed", type=float, default=1.0)
parser.add_argument("-scale", type=float, default=40)
args = parser.parse_args()

bvh_reader = BvhReader(args.bvh)
bvh_reader.read()

window.run(BvhViewer, args)
