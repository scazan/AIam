import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/connectivity")
from osc_receiver import OscReceiver

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui, QtOpenGL
import collections
import math

OSC_PORT = 15002
FRAME_RATE = 30

class Scene(QtOpenGL.QGLWidget):
    def __init__(self, parent):
        QtOpenGL.QGLWidget.__init__(self)
        self._users_joints = collections.defaultdict(dict)

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 0.0)
        glClearAccum(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glEnable(GL_POINT_SMOOTH)
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
        self.configure_3d_projection()

    def configure_3d_projection(self, pixdx=0, pixdy=0):
        self.fovy = 40.0
        self.near = 300.0
        self.far = 20000.0

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

#-3.767,-1.400,-3.485,-55.500,18.500
        self._camera_x_orientation = 55
        self._camera_y_orientation = 0
        self._camera_position = [0, 0, -2000]

        glRotatef(self._camera_x_orientation, 1.0, 0.0, 0.0)
        glRotatef(self._camera_y_orientation, 0.0, 1.0, 0.0)
        glTranslatef(*self._camera_position)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(self.margin, self.margin, 0)

        for user_id, joints in self._users_joints.iteritems():
            self._draw_user(user_id, joints)

    def _draw_user(self, user_id, joints):
        self._draw_limb(joints, "head", "neck")

        self._draw_limb(joints, "left_shoulder", "left_elbow")
        self._draw_limb(joints, "left_elbow", "left_hand")

        self._draw_limb(joints, "right_shoulder", "right_elbow")
        self._draw_limb(joints, "right_elbow", "right_hand")

        self._draw_limb(joints, "left_shoulder", "right_shoulder")

        self._draw_limb(joints, "left_shoulder", "torso")
        self._draw_limb(joints, "right_shoulder", "torso")

        self._draw_limb(joints, "left_hip", "torso")
        self._draw_limb(joints, "right_hip", "torso")
        self._draw_limb(joints, "left_hip", "right_hip")

        self._draw_limb(joints, "left_hip", "left_knee")
        self._draw_limb(joints, "left_knee", "left_foot")

        self._draw_limb(joints, "right_hip", "right_knee")
        self._draw_limb(joints, "right_knee", "right_foot")

    def _draw_limb(self, joints, name1, name2):
        joint1 = joints[name1]
        joint2 = joints[name2]
        glColor3f(0, 0, 0)
        glBegin(GL_LINES)
        glVertex3f(*joint1)
        glVertex3f(*joint2)
        glEnd()

    def sizeHint(self):
        return QtCore.QSize(500, 500)

    def handle_joint_data(self, path, args, types, src, user_data):
        user_id, joint_name, x, y, z = args
        self._users_joints[user_id][joint_name] = [x, y, z]

class MainWindow(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self._layout = QtGui.QVBoxLayout()
        self.setLayout(self._layout)
        self._scene = Scene(self)
        self._layout.addWidget(self._scene)

        osc_receiver = OscReceiver(OSC_PORT)
        osc_receiver.add_method("/joint", "isfff", self._scene.handle_joint_data)
        osc_receiver.start()

        timer = QtCore.QTimer(self)
        timer.setInterval(1000. / FRAME_RATE)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), self._scene.updateGL)
        timer.start()

app = QtGui.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
