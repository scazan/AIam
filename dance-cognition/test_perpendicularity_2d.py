import window
from vector import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy

line_pos1 = Vector2d(0.1, 0.2)
line_pos2 = Vector2d(0.5, 0.1)
p = Vector2d(0.3, 0.3)

class Test(window.Window):
    def InitGL(self):
        window.Window.InitGL(self)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def render(self):
        glColor3f(0,0,0)
        glBegin(GL_LINES)
        glVertex2f(*self._scale(line_pos1))
        glVertex2f(*self._scale(line_pos2))
        glEnd()

        glPointSize(5.0)
        glBegin(GL_POINTS)
        glVertex2f(*self._scale(p))
        glEnd()

        q = self._perpendicular(line_pos1, line_pos2, p)
        glColor3f(1,0,0)
        glBegin(GL_POINTS)
        glVertex2f(*self._scale(q))
        glEnd()

    def _perpendicular(self, p1, p2, q):
        u = p2 - p1
        pq = q - p1
        w2 = pq - u * (self._dot_product(pq, u) / pow(u.mag(), 2))
        return q - w2

    def _dot_product(self, a, b):
        return numpy.dot(a.v, b.v)

    def _scale(self, v):
        return v * self.min_dimension

window.run(Test)
