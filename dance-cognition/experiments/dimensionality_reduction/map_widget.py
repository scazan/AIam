from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui, QtOpenGL
import numpy

SPLIT_SENSITIVITY = .2

class MapWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent, dimensions):
        self._dimensions = dimensions
        observations = parent.experiment.student.normalized_observed_reductions[
            :,dimensions]
        self._split_into_segments(observations)
        self._reduction = None
        QtOpenGL.QGLWidget.__init__(self, parent)

    def _split_into_segments(self, observations):
        self._segments = []
        segment = []
        previous_observation = None
        for observation in observations:
            if previous_observation is not None and \
                    numpy.linalg.norm(observation - previous_observation) > SPLIT_SENSITIVITY:
                self._segments.append(segment)
                segment = []
            segment.append(observation)
            previous_observation = observation
        if len(segment) > 0:
            self._segments.append(segment)

    def set_reduction(self, reduction):
        self._reduction = reduction[self._dimensions]

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 0.0)
        glClearAccum(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

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
        self._render_segments()
        if self._reduction is not None:
            self._render_reduction()

    def _render_segments(self):
        glColor4f(0, 0, 0, .1)
        glLineWidth(1.0)

        for segment in self._segments:
            glBegin(GL_LINE_STRIP)
            for x,y in segment:
                glVertex2f(*self._vertex(x, y))
            glEnd()

    def _render_reduction(self):
        glColor3f(0, 0, 0)
        glPointSize(4.0)
        glBegin(GL_POINTS)
        glVertex2f(*self._vertex(*self._reduction))
        glEnd()

    def _vertex(self, x, y):
        return x*self._width, y*self._height
