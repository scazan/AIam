import sys
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui, QtOpenGL
import numpy
import random
from navigator import Navigator

class MapView(QtOpenGL.QGLWidget):
    def __init__(self, parent):
        QtOpenGL.QGLWidget.__init__(self, parent)

    def render(self):
        self.render_map()
        self.render_path()

    def render_map(self):
        glColor3f(0, 1, 0)
        glPointSize(3.0)
        glBegin(GL_POINTS)
        for x,y in self.parent().knowns:
            glVertex2f(x*self.width, y*self.height)
        glEnd()

    def render_path(self):
        glColor3f(0.5, 0.5, 1.0)

        departure_x, departure_y = self.parent().path[0]
        destination_x, destination_y = self.parent().path[-1]
        glLineWidth(1.0)
        glRectf(departure_x*self.width-3,
                departure_y*self.height-3,
                departure_x*self.width+3,
                departure_y*self.height+3)

        glPointSize(6.0)
        glBegin(GL_POINTS)
        glVertex2f(destination_x*self.width, destination_y*self.height)
        glEnd()

        glPointSize(3.0)
        glBegin(GL_POINTS)
        for x,y in self.parent().path[1:-1]:
            glVertex2f(x*self.width, y*self.height)
        glEnd()

        glBegin(GL_LINE_STRIP)
        for x,y in self.parent().path:
            glVertex2f(x*self.width, y*self.height)
        glEnd()

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
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, self.window_width, self.window_height, 0.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(self.margin, self.margin, 0)
        self.render()

class MainWindow(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        layout = QtGui.QHBoxLayout()
        size_policy = QtGui.QSizePolicy(
            QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(1)

        self.map_view = MapView(self)
        layout.addWidget(self.map_view)

        self.setLayout(layout)

        self.generate_random_map()
        self.create_navigator()
        self.generate_path()

    def generate_random_map(self):
        self.knowns = [self.random_map_position() for n in range(100)]

    def random_map_position(self):
        return numpy.array([random.uniform(0., 1.),
                            random.uniform(0., 1.)])

    def create_navigator(self):
        self.navigator = Navigator(knowns=self.knowns)

    def generate_path(self):
        departure = random.choice(self.knowns)
        destination = self.random_map_position()
        self.path = self.navigator.generate_path(
            departure=departure, destination=destination, resolution=10)

    def sizeHint(self):
        return QtCore.QSize(500, 500)

app = QtGui.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
