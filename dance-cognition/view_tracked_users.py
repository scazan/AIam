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
from argparse import ArgumentParser
from vector import Vector3d
text_renderer_module = __import__("text_renderer")

OSC_PORT = 15002
FRAME_RATE = 30
CAMERA_Y_SPEED = 1
CAMERA_KEY_SPEED = 10
CAMERA_DRAG_SPEED = .1

class Scene(QtOpenGL.QGLWidget):
    def __init__(self, parent):
        QtOpenGL.QGLWidget.__init__(self)
        self._users_joints = collections.defaultdict(dict)
        self._text_renderer_class = getattr(text_renderer_module, "GlutTextRenderer")
        self._set_camera_from_arg(parent.args.camera)
        self._dragging_orientation = False
        self._dragging_y_position = False
        self.setMouseTracking(True)

    def _set_camera_from_arg(self, arg):
        pos_x, pos_y, pos_z, orient_y, orient_z = map(float, arg.split(","))
        self._set_camera_position([pos_x, pos_y, pos_z])
        self._set_camera_orientation(orient_y, orient_z)

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 0.0)
        glClearAccum(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glEnable(GL_POINT_SMOOTH)

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

        glRotatef(self._camera_x_orientation, 1.0, 0.0, 0.0)
        glRotatef(self._camera_y_orientation, 0.0, 1.0, 0.0)
        glTranslatef(*self._camera_position)

    def _draw_floor(self):
        GRID_NUM_CELLS = 30
        GRID_SIZE = self.far - self.near
        y = 0
        z1 = -GRID_SIZE/2
        z2 = GRID_SIZE/2
        x1 = -GRID_SIZE/2
        x2 = GRID_SIZE/2
        self._camera_x = self._camera_position[0]
        self._camera_z = self._camera_position[2]
        color_r = 0
        color_g = 0
        color_b = 0
        color_a = 0.2

        glLineWidth(1.4)

        for n in range(GRID_NUM_CELLS):
            glBegin(GL_LINES)
            x = x1 + float(n) / GRID_NUM_CELLS * GRID_SIZE
            color_a1 = color_a * (1 - abs(x - self._camera_x) / GRID_SIZE)

            glColor4f(color_r, color_g, color_b, 0)
            glVertex3f(x, y, z1)
            glColor4f(color_r, color_g, color_b, color_a1)
            glVertex3f(x, y, self._camera_z)

            glColor4f(color_r, color_g, color_b, color_a1)
            glVertex3f(x, y, self._camera_z)
            glColor4f(color_r, color_g, color_b, 0)
            glVertex3f(x, y, z2)
            glEnd()

        for n in range(GRID_NUM_CELLS):
            glBegin(GL_LINES)
            z = z1 + float(n) / GRID_NUM_CELLS * GRID_SIZE
            color_a1 = color_a * (1 - abs(z - self._camera_z) / GRID_SIZE)

            glColor4f(color_r, color_g, color_b, 0)
            glVertex3f(x1, y, z)
            glColor4f(color_r, color_g, color_b, color_a1)
            glVertex3f(self._camera_x, y, z)

            glColor4f(color_r, color_g, color_b, color_a1)
            glVertex3f(self._camera_x, y, z)
            glColor4f(color_r, color_g, color_b, 0)
            glVertex3f(x2, y, z)
            glEnd()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(self.margin, self.margin, 0)
        self.configure_3d_projection(-100, 0)

        self._draw_floor()

        for user_id, joints in self._users_joints.iteritems():
            self._draw_user(user_id, joints)

    def _draw_user(self, user_id, joints):
        self._draw_label(user_id, joints)

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

    def _draw_label(self, user_id, joints):
        glColor3f(0, 0, 0)
        position = Vector3d(*joints["head"]) + Vector3d(0, 100, 0)
        self._draw_text(str(user_id), 100, *position)

    def _draw_limb(self, joints, name1, name2):
        joint1 = joints[name1]
        joint2 = joints[name2]
        glColor3f(0, 0, 0)
        glBegin(GL_LINES)
        glVertex3f(*joint1)
        glVertex3f(*joint2)
        glEnd()

    def sizeHint(self):
        return QtCore.QSize(640, 480)

    def handle_joint_data(self, path, args, types, src, user_data):
        user_id, joint_name, x, y, z = args
        self._users_joints[user_id][joint_name] = [x, y, z]

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

    def print_camera_settings(self):
        print "%.3f,%.3f,%.3f,%.3f,%.3f" % (
            self._camera_position[0],
            self._camera_position[1],
            self._camera_position[2],
            self._camera_y_orientation, self._camera_x_orientation)

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
        elif key == QtCore.Qt.Key_D:
            new_position[0] -= CAMERA_KEY_SPEED * math.cos(r)
            new_position[2] -= CAMERA_KEY_SPEED * math.sin(r)
            self._set_camera_position(new_position)
        elif key == QtCore.Qt.Key_W:
            new_position[0] += CAMERA_KEY_SPEED * math.cos(r + math.pi/2)
            new_position[2] += CAMERA_KEY_SPEED * math.sin(r + math.pi/2)
            self._set_camera_position(new_position)
        elif key == QtCore.Qt.Key_S:
            new_position[0] -= CAMERA_KEY_SPEED * math.cos(r + math.pi/2)
            new_position[2] -= CAMERA_KEY_SPEED * math.sin(r + math.pi/2)
            self._set_camera_position(new_position)

    def _draw_text(self, text, size, x, y, z, font=GLUT_STROKE_ROMAN, spacing=None,
                  v_align="left", h_align="top"):
        self._text_renderer(text, size, font).render(x, y, z, v_align, h_align)

    def _text_renderer(self, text, size, font):
        return self._text_renderer_class(self, text, size, font)

class MainWindow(QtGui.QWidget):
    def __init__(self, args):
        QtGui.QWidget.__init__(self)
        self.args = args
        self._layout = QtGui.QVBoxLayout()
        self.setLayout(self._layout)
        self._scene = Scene(self)
        self._layout.addWidget(self._scene)
        self._create_menu()

        osc_receiver = OscReceiver(OSC_PORT)
        osc_receiver.add_method("/joint", "isfff", self._scene.handle_joint_data)
        osc_receiver.start()

        timer = QtCore.QTimer(self)
        timer.setInterval(1000. / FRAME_RATE)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), self._scene.updateGL)
        timer.start()

    def _create_menu(self):
        self._menu_bar = QtGui.QMenuBar()
        self._layout.setMenuBar(self._menu_bar)
        self._create_main_menu()

    def _create_main_menu(self):
        self._main_menu = self._menu_bar.addMenu("Main")
        self._add_show_camera_settings_action()

    def _add_show_camera_settings_action(self):
        action = QtGui.QAction('Show camera settings', self)
        action.triggered.connect(self._scene.print_camera_settings)
        self._main_menu.addAction(action)

    def keyPressEvent(self, event):
        self._scene.keyPressEvent(event)
        QtGui.QWidget.keyPressEvent(self, event)


parser = ArgumentParser()
parser.add_argument("--camera", help="posX,posY,posZ,orientY,orientX",
                    default="-70.364,-47.000,-5189.173,-8.800,10.400")
args = parser.parse_args()

app = QtGui.QApplication(sys.argv)
window = MainWindow(args)
window.show()
app.exec_()
