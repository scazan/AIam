import math
import copy
from argparse import ArgumentParser
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui, QtOpenGL
from collections import defaultdict

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")
from bvh import bvh_reader as bvh_reader_module
from connectivity.simple_osc_receiver import OscReceiver
from floor_checkerboard import FloorCheckerboard

FLOOR_ARGS = {"num_cells": 26, "size": 26,
              "board_color1": (.2, .2, .2, 1),
              "board_color2": (.3, .3, .3, 1),
              "floor_color": None,
              "background_color": (0.0, 0.0, 0.0, 0.0)}
CAMERA_Y_SPEED = .01
CAMERA_KEY_SPEED = .1
CAMERA_DRAG_SPEED = .1
FRAME_RATE = 50

class Avatar:
    def __init__(self):
        self.pose = bvh_reader.create_pose()
        self.frame = None
        self.is_renderable = False
        
class MainWindow(QtOpenGL.QGLWidget):
    def __init__(self, bvh_reader, args):
        self.bvh_reader = bvh_reader
        self._hierarchy = bvh_reader.get_hierarchy()
        self._avatars = {}
        self.args = args
        self.margin = 0
        self._set_camera_from_arg(args.camera)
        self._current_avatar = None
        self._dragging_orientation = False
        self._dragging_y_position = False
        QtOpenGL.QGLWidget.__init__(self)
        self.setMouseTracking(True)
        self._floor = FloorCheckerboard(**FLOOR_ARGS)
        self._in_fullscreen = False

        self._osc_receiver = OscReceiver(args.port)
        self._osc_receiver.add_method("/avatar_begin", "i", self._handle_avatar_begin)
        self._osc_receiver.add_method("/avatar_end", "", self._handle_avatar_end)
        self._osc_receiver.add_method("/world", "iifff", self._received_worldpos)
        self._osc_receiver.start(auto_serve=True)

        timer = QtCore.QTimer(self)
        timer.setInterval(1000. / FRAME_RATE)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), self.updateGL)
        timer.start()

    def _new_frame(self):
        return [None] * self._hierarchy.get_num_joints()

    def _handle_avatar_begin(self, path, args, types, src, user_data):
        index = args[0]
        if index not in self._avatars:
            self._avatars[index] = Avatar()
        self._current_avatar = self._avatars[index]
        self._current_avatar.frame = self._new_frame()

    def _handle_avatar_end(self, path, args, types, src, user_data):
        if self._current_avatar is None:
            return
        self._current_avatar.vertices = copy.copy(self._current_avatar.frame)
        self._current_avatar.is_renderable = True
        self._current_avatar.frame = None
        self._current_avatar = None
        
    def _received_worldpos(self, path, args, types, src, user_data):
        if self._current_avatar is None:
            return
        frame_count, joint_index, x, y, z = args
        self._current_avatar.frame[joint_index] = (x, y, z)

    def _received_translation(self, path, args, types, src, user_data):
        if self._current_avatar is None:
            return
        frame_count, joint_index, x, y, z = args
        self._current_avatar.frame[joint_index].update(
            {"Xposition": x,
             "Yposition": y,
             "Zposition": z})

    def _received_orientation(self, path, args, types, src, user_data):
        if self._current_avatar is None:
            return
        frame_count, joint_index, x, y, z = args
        self._current_avatar.frame[joint_index].update(
            {"Xrotation": math.degrees(x),
             "Yrotation": math.degrees(y),
             "Zrotation": math.degrees(z)})

    def _set_camera_from_arg(self, arg):
        pos_x, pos_y, pos_z, orient_y, orient_z = map(float, arg.split(","))
        self._set_camera_position([pos_x, pos_y, pos_z])
        self._set_camera_orientation(orient_y, orient_z)

    def _set_camera_position(self, position):
        self._camera_position = position

    def _set_camera_orientation(self, y_orientation, x_orientation):
        self._camera_y_orientation = y_orientation
        self._camera_x_orientation = x_orientation

    def keyPressEvent(self, event):
        r = math.radians(self._camera_y_orientation)
        new_position = self._camera_position
        key = event.key()
        if key == QtCore.Qt.Key_A:
            new_position[0] += CAMERA_KEY_SPEED * math.cos(r)
            new_position[2] += CAMERA_KEY_SPEED * math.sin(r)
            self._set_camera_position(new_position)
            return
        elif key == QtCore.Qt.Key_D:
            new_position[0] -= CAMERA_KEY_SPEED * math.cos(r)
            new_position[2] -= CAMERA_KEY_SPEED * math.sin(r)
            self._set_camera_position(new_position)
            return
        elif key == QtCore.Qt.Key_W:
            new_position[0] += CAMERA_KEY_SPEED * math.cos(r + math.pi/2)
            new_position[2] += CAMERA_KEY_SPEED * math.sin(r + math.pi/2)
            self._set_camera_position(new_position)
            return
        elif key == QtCore.Qt.Key_S:
            new_position[0] -= CAMERA_KEY_SPEED * math.cos(r + math.pi/2)
            new_position[2] -= CAMERA_KEY_SPEED * math.sin(r + math.pi/2)
            self._set_camera_position(new_position)
            return
        elif key == QtCore.Qt.Key_F:
            self._toggle_fullscreen()
            return
        QtGui.QWidget.keyPressEvent(self, event)

    def sizeHint(self):
        return QtCore.QSize(800, 600)

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClearAccum(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glutInit(sys.argv)

    def resizeGL(self, window_width, window_height):
        self.window_width = window_width
        self.window_height = window_height
        if window_height == 0:
            window_height = 1
        glViewport(0, 0, window_width, window_height)
        self.margin = 0
        self.width = window_width - 2*self.margin
        self.height = window_height - 2*self.margin
        self._aspect_ratio = float(window_width) / window_height
        self.min_dimension = min(self.width, self.height)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(self.margin, self.margin, 0)
        self.render()

    def configure_3d_projection(self, pixdx=0, pixdy=0):
        self.fovy = 45
        self.near = 0.1
        self.far = 100.0

        fov2 = ((self.fovy*math.pi) / 180.0) / 2.0
        top = self.near * math.tan(fov2)
        bottom = -top
        right = top * self._aspect_ratio
        left = -right
        xwsize = right - left
        ywsize = top - bottom
        dx = -(pixdx*xwsize/self.width)
        dy = -(pixdy*ywsize/self.height)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glFrustum (left + dx, right + dx, bottom + dy, top + dy, self.near, self.far)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glRotatef(self._camera_x_orientation, 1.0, 0.0, 0.0)
        glRotatef(self._camera_y_orientation, 0.0, 1.0, 0.0)
        glTranslatef(*self._camera_position)

    def render(self):
        self.configure_3d_projection(-100, 0)
        camera_x = self._camera_position[0]
        camera_z = self._camera_position[2]
        self._floor.render(0, 0, camera_x, camera_z)
        for avatar in self._avatars.values():
            if avatar.is_renderable:
                self._render_avatar(avatar)
        
    def _render_avatar(self, avatar):
        glColor3f(1, 1, 1)
        glLineWidth(5.0)
        edges = self.bvh_reader.vertices_to_edges(avatar.vertices) # TODO: what if type==bvh?
        for edge in edges:
            self._render_edge(edge.v1, edge.v2)

    def _render_edge(self, v1, v2):
        glBegin(GL_LINES)
        self._vertex(v1)
        self._vertex(v2)
        glEnd()

    def _vertex(self, worldpos):
        if self.args.z_up:
            glVertex3f(worldpos[0], worldpos[2], worldpos[1])
        else:
            glVertex3f(worldpos[0], worldpos[1], worldpos[2])

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._dragging_orientation = True
        elif event.button() == QtCore.Qt.RightButton:
            self._dragging_y_position = True

    def mouseReleaseEvent(self, event):
        self._dragging_orientation = False
        self._dragging_y_position = False
        self._drag_x_previous = event.x()
        self._drag_y_previous = event.y()

    def mouseMoveEvent(self, event):
        x = event.x()
        y = event.y()
        if self._dragging_orientation:
            self._set_camera_orientation(
                self._camera_y_orientation + CAMERA_DRAG_SPEED * (x - self._drag_x_previous),
                self._camera_x_orientation + CAMERA_DRAG_SPEED * (y - self._drag_y_previous))
        elif self._dragging_y_position:
            self._camera_position[1] += CAMERA_Y_SPEED * (y - self._drag_y_previous)
        self._drag_x_previous = x
        self._drag_y_previous = y

    def _toggle_fullscreen(self):
        if self._in_fullscreen:
            self._leave_fullscreen()
        else:
            self._enter_fullscreen()
        
    def _enter_fullscreen(self):
        self.setCursor(QtCore.Qt.BlankCursor)
        self.showFullScreen()
        self._in_fullscreen = True

    def _leave_fullscreen(self):
        self.setCursor(QtCore.Qt.ArrowCursor)
        self.showNormal()
        self._in_fullscreen = False
        
parser = ArgumentParser()
parser.add_argument("bvh", type=str)
parser.add_argument("--camera", help="posX,posY,posZ,orientY,orientX",
                    default="-3.767,-1.400,-3.485,-55.500,18.500")
parser.add_argument("--port", type=int, default=10000)
parser.add_argument("--z-up", action="store_true")
parser.add_argument("--type", choices=["world"], default="world")
args = parser.parse_args()

bvh_reader = bvh_reader_module.BvhReader(args.bvh)
bvh_reader.read()

app = QtGui.QApplication(sys.argv)
window = MainWindow(bvh_reader, args)
window.show()
app.exec_()
