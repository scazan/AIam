import math
import copy
from argparse import ArgumentParser
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui, QtOpenGL

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")
from bvh.bvh_reader import bvh_reader as bvh_reader_module
from connectivity.simple_osc_receiver import OscReceiver

FRAME_RATE = 50

class MainWindow(QtOpenGL.QGLWidget):
    def __init__(self, bvh_reader, args):
        self.bvh_reader = bvh_reader
        self._hierarchy = bvh_reader.get_hierarchy()
        self._pose = bvh_reader.create_pose()
        self.args = args
        self.margin = 0
        self._set_camera_from_arg(args.camera)
        self._next_world_positions = {}
        self._world_positions = None
        self._frame_count = None
        QtOpenGL.QGLWidget.__init__(self)

        self._osc_receiver = OscReceiver(args.port)
        self._osc_receiver.add_method("/world", "iifff", self._received_worldpos)
        self._osc_receiver.start(auto_serve=True)

        timer = QtCore.QTimer(self)
        timer.setInterval(1000. / FRAME_RATE)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), self.updateGL)
        timer.start()

    def _received_worldpos(self, path, args, types, src, user_data):
        frame_count, joint_index, x, y, z = args
        if joint_index == 0:
            if self._frame_count is None:
                self._frame_count = frame_count
            elif frame_count > self._frame_count:
                self._world_positions = copy.copy(self._next_world_positions)
                self._next_world_positions = {}
                self._frame_count = frame_count

        self._next_world_positions[joint_index] = (x, y, z)

    def _set_camera_from_arg(self, arg):
        pos_x, pos_y, pos_z, orient_y, orient_z = map(float, arg.split(","))
        self._set_camera_position([pos_x, pos_y, pos_z])
        self._set_camera_orientation(orient_y, orient_z)

    def _set_camera_position(self, position):
        self._camera_position = position

    def _set_camera_orientation(self, y_orientation, x_orientation):
        self._camera_y_orientation = y_orientation
        self._camera_x_orientation = x_orientation

    def sizeHint(self):
        return QtCore.QSize(800, 600)

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 0.0)
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
        if self._world_positions is not None:
            self._hierarchy.set_pose_vertices(self._pose, self._world_positions)
            self._render_pose()
        
    def _render_pose(self):
        glColor3f(0, 0, 0)
        glLineWidth(2.0)
        self._render_joint(self._pose.get_root_joint())

    def _render_joint(self, joint):
        for child in joint.children:
            self._render_edge(joint, child)
            self._render_joint(child)

    def _render_edge(self, joint1, joint2):
        glBegin(GL_LINES)
        self._vertex(joint1.worldpos)
        self._vertex(joint2.worldpos)
        glEnd()

    def _vertex(self, worldpos):
        glVertex3f(*worldpos)

parser = ArgumentParser()
parser.add_argument("bvh", type=str)
parser.add_argument("--camera", help="posX,posY,posZ,orientY,orientX",
                    default="-3.767,-1.400,-3.485,-55.500,18.500")
parser.add_argument("--port", type=int, default=10000)
args = parser.parse_args()

bvh_reader = bvh_reader_module.BvhReader(args.bvh)
bvh_reader.read()

app = QtGui.QApplication(sys.argv)
window = MainWindow(bvh_reader, args)
window.show()
app.exec_()
