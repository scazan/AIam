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
from connectivity.osc_receiver import OscReceiver
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
NUM_TRACKED_JOINTS = 15
JOINTS_DETERMNING_INTENSITY = ["left_hand", "right_hand"]

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

        ai_osc_receiver = OscReceiver(args.port)
        ai_osc_receiver.add_method("/avatar_begin", "i", self._handle_avatar_begin)
        ai_osc_receiver.add_method("/avatar_end", "", self._handle_avatar_end)
        ai_osc_receiver.add_method("/world", "iifff", self._received_worldpos)
        ai_osc_receiver.start()

        self._frame = None
        self._users = {}
        skeleton_osc_receiver = OscReceiver(args.skeleton_osc_port)
        skeleton_osc_receiver.add_method("/begin_frame", "f", self._handle_begin_frame)
        skeleton_osc_receiver.add_method("/joint", "isfffffffff", self._handle_joint_data)
        skeleton_osc_receiver.add_method("/state", "is", self._handle_user_state)
        skeleton_osc_receiver.start()

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

    def _handle_begin_frame(self, path, values, types, src, user_data):
        (timestamp,) = values
        if self._frame is not None:
            self._process_frame()
        self._frame = {"timestamp": timestamp,
                       "user_states": [],
                       "joint_data": []}

    def _handle_joint_data(self, path, values, types, src, user_data):
        if self._frame is not None:
            self._frame["joint_data"].append(values)

    def _handle_user_state(self, path, values, types, src, user_data):
        user_id, state = values
        if self._frame is not None:
            self._frame["user_states"].append((user_id, state))

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
        
        self._eye = (self.width / 2, self.height/2, 5000)

    def render(self):
        self.configure_3d_projection(-100, 0)
        camera_x = self._camera_position[0]
        camera_z = self._camera_position[2]
        # self._floor.render(0, 0, camera_x, camera_z)
        for avatar in self._avatars.values():
            if avatar.is_renderable:
                self._render_avatar(avatar)

        self.configure_2d_projection(0, self.width, 0, self.height)
        glColor3f(1,0,1)
        for avatar in self._avatars.values():
            if avatar.is_renderable:
                self._render_avatar_2d(avatar)
                
    def _render_avatar_2d(self, avatar):
        screen_vertices = [
            self._world_to_screen(world_vertex)
            for world_vertex in avatar.vertices]
        screen_vertices = self._adjust_screen_vertices(
            screen_vertices,
            x_offset=0.5,
            y_offset=0.2,
            scale=0.5)
        screen_edges = self.bvh_reader.vertices_to_edges(screen_vertices)
        for edge in screen_edges:
            self._render_edge_2d(edge.v1, edge.v2)

    def _world_to_screen(self, world):
        x = (self._eye[2] * (world[0]-self._eye[0])) / (self._eye[2] + world[2]) + self._eye[0];
        y = (self._eye[2] * (world[1]-self._eye[1])) / (self._eye[2] + world[2]) + self._eye[1];
        screen = (x, y)
        return screen

    def _adjust_screen_vertices(self, vertices, x_offset, y_offset, scale):
        hip_x = vertices[0][0]
        return [
            ((vertex[0] - hip_x) * scale + x_offset, (vertex[1] + y_offset) * scale)
            for vertex in vertices]

    def _render_edge_2d(self, v1, v2):
        glBegin(GL_LINES)
        glVertex2f(v1[0] * self.width, v1[1] * self.height)
        glVertex2f(v2[0] * self.width, v2[1] * self.height)
        glEnd()
    
    def configure_2d_projection(self, left, right, bottom, top):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(left, right, bottom, top, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
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

    def _process_frame(self):
        for values in self._frame["user_states"]:
            self._process_user_state(*values)

    def _process_user_state(self, user_id, state):
        if user_id not in self._users:
            self._users[user_id] = User(user_id)
        user = self._users[user_id]
        if state == "lost":
            try:
                del self._users[user_id]
            except KeyError:
                pass
        
class User:
    def __init__(self, user_id):
        self._user_id = user_id
        self._joints = {}
        self._num_updated_joints = 0
        self._intensity = 0

    def handle_joint_data(self, joint_name, *args):
        self._process_joint_data(joint_name, *args)

    def _process_joint_data(self, joint_name,
                            position_x, position_y, position_z,
                            position_confidence,
                            orientation_w, orientation_x, orientation_y, orientation_z,
                            orientation_confidence):
        self._ensure_joint_exists(joint_name)
        joint = self._joints[joint_name]
        joint.set_position(position_x, position_y, position_z)
        joint.set_position_confidence(position_confidence)
        joint.set_orientation(orientation_w, orientation_x, orientation_y, orientation_z)
        joint.set_orientation_confidence(orientation_confidence)
        self._last_updated_joint = joint_name
        self._num_updated_joints += 1
        if self._num_updated_joints >= NUM_TRACKED_JOINTS:
            self._process_frame()

    def _ensure_joint_exists(self, joint_name):
        if joint_name not in self._joints:
            self._joints[joint_name] = Joint()

    def _process_frame(self):
        self._intensity = self._measure_intensity()
        self._num_updated_joints = 0

    def _measure_intensity(self):
        return sum([
            self.get_joint(joint_name).get_intensity()
            for joint_name in JOINTS_DETERMNING_INTENSITY]) / \
                len(JOINTS_DETERMNING_INTENSITY)

    def get_intensity(self):
        return self._intensity
    
    def get_id(self):
        return self._user_id

    def get_joint(self, name):
        return self._joints[name]

    def has_complete_joint_data(self):
        return len(self._joints) >= NUM_TRACKED_JOINTS
    
parser = ArgumentParser()
parser.add_argument("bvh", type=str)
parser.add_argument("--camera", help="posX,posY,posZ,orientY,orientX",
                    default="-3.767,-1.400,-3.485,-55.500,18.500")
parser.add_argument("--port", type=int, default=10000)
parser.add_argument("--z-up", action="store_true")
parser.add_argument("--type", choices=["world"], default="world")
parser.add_argument("--skeleton-osc-port", type=int, default=15002)
args = parser.parse_args()

bvh_reader = bvh_reader_module.BvhReader(args.bvh)
bvh_reader.read()

app = QtGui.QApplication(sys.argv)
window = MainWindow(bvh_reader, args)
window.show()
app.exec_()
