#!/usr/bin/env python

import argparse
import threading
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

from receiver import PnReceiver, SERVER_PORT_BVH

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../../dance-cognition")

import window
from bvh.bvh_reader import BvhReader

parser = argparse.ArgumentParser()
window.Window.add_parser_arguments(parser)
parser.add_argument("bvh")
parser.add_argument("--host", default="localhost")
parser.add_argument("--port", type=int, default=SERVER_PORT_BVH)
parser.add_argument("-speed", type=float, default=1.0)
parser.add_argument("-zoom", type=float, default=1.0)
parser.add_argument("-unit-cube", action="store_true")
parser.add_argument("-loop", action="store_true")
parser.add_argument("-vertex-size", type=float, default=0)
parser.add_argument("--z-up", action="store_true")
args = parser.parse_args()

class BvhViewer(window.Window):
    def __init__(self, *args):        
        global bvh_reader
        window.Window.__init__(self, *args)
        self.reader = bvh_reader

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

    def _draw_skeleton(self):
        global frame
        if frame is None:
            return
        bvh_reader.set_pose_from_frame(pose, frame)
        vertices = pose.get_vertices()
        edges = self.reader.vertices_to_edges(vertices)
        if args.vertex_size > 0:
            self._draw_vertices(vertices)
        self._draw_edges(edges)

    def _draw_vertices(self, vertices):
        glPointSize(args.vertex_size)
        glColor3f(0,0,0)
        glBegin(GL_POINTS)
        for vertex in vertices:
            self._bvh_vertex(self._zoom_vertex(vertex))
        glEnd()

    def _draw_edges(self, edges):
        glLineWidth(2.0)
        glColor3f(0,0,0)
        for edge in edges:
            self._draw_line(self._zoom_vertex(edge.v1),
                            self._zoom_vertex(edge.v2))

    def _zoom_vertex(self, vertex):
        return args.zoom * self.reader.normalize_vector(vertex)

    def _draw_line(self, v1, v2):
        glBegin(GL_LINES)
        self._bvh_vertex(v1)
        self._bvh_vertex(v2)
        glEnd()

    def _bvh_vertex(self, v):
        glVertex3f(
            v[bvh_coordinate_left],
            v[bvh_coordinate_up],
            v[bvh_coordinate_far])

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

def receive():
    global frame
    for frame in pn_receiver.get_frames():
        pass

if args.z_up:
    bvh_coordinate_left = 0
    bvh_coordinate_up = 2
    bvh_coordinate_far = 1
else:
    bvh_coordinate_left = 0
    bvh_coordinate_up = 1
    bvh_coordinate_far = 2

bvh_reader = BvhReader(args.bvh)
bvh_reader.read(read_frames=False)
pose = bvh_reader.get_hierarchy().create_pose()
frame = None

pn_receiver = PnReceiver()
print "connecting..."
pn_receiver.connect(args.host, args.port)
print "ok"

receiver_thread = threading.Thread(target=receive)
receiver_thread.daemon = True
receiver_thread.start()

window.run(BvhViewer, args)
