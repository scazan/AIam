from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui, QtOpenGL

class MapWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent):
        self._map_points = parent.experiment.student.normalized_observed_reductions[:,[0,2]]
        QtOpenGL.QGLWidget.__init__(self, parent)

    def set_reduction(self, reduction):
        self._reduction = reduction

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 0.0)
        glClearAccum(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_LINE_SMOOTH)

    def resizeGL(self, window_width, window_height):
        self.window_width = window_width
        self.window_height = window_height
        if window_height == 0:
            window_height = 1
        self._margin = 5
        self._width = window_width - 2*self._margin
        self._height = window_height - 2*self._margin
        glViewport(0, 0, window_width, window_height)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glOrtho(0.0, self.window_width, self.window_height, 0.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glTranslatef(self._margin, self._margin, 0)
        self._render_map()

    def _render_map(self):
        glColor3f(0, 0, 0)
        glPointSize(1.0)
        glBegin(GL_POINTS)
        for x,y in self._map_points:
            glVertex2f(*self._vertex(x, y))
        glEnd()

    def _vertex(self, x, y):
        return x*self._width, y*self._height
