import window
from vector import Vector3d, DirectionalVector
import random
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from states import state_machine

MOUSE_REACTIVITY = 5.0

class FollowerDemo(window.Window):
    def __init__(self, *args):
        window.Window.__init__(self, *args)
        self.input = Vector3d(0, 0, 0)

    def InitGL(self):
        window.Window.InitGL(self)
        glutMouseFunc(self._mouse_clicked)
        glutMotionFunc(self._mouse_moved)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def _mouse_clicked(self, button, state, x, y):
        if state == GLUT_DOWN:
            self._drag_x_previous = x
            self._drag_y_previous = y

    def _mouse_moved(self, x, y):
        movement = Vector2d(float(x - self._drag_x_previous),
                            float(y - self._drag_y_previous)) / self.min_dimension
        self.input += movement * MOUSE_REACTIVITY
        self.input.x = self._clamp(self.input.x)
        self.input.y = self._clamp(self.input.y)
        self._drag_x_previous = x
        self._drag_y_previous = y

    def _clamp(self, value):
        return max(min(value, 1.0), -1.0)

    def render(self):
        self.input += self._input_noise()
        self._draw_input()
        self._draw_output()

    def _input_noise(self):
        mag = random.normalvariate(0.0, 0.5) * 0.001
        return Vector3d(
            random.uniform(-1,1),
            random.uniform(-1,1),
            random.uniform(-1,1)) * mag

    def _draw_output(self):
        glPushMatrix()
        self.configure_3d_projection(100, 0)

        self._draw_unit_cube()

        glColor3f(0,0,0)
        glPointSize(5.0)
        glBegin(GL_POINTS)
        for state in state_machine.states.values():
            glVertex3f(*state.position)
        glEnd()

        glPopMatrix()

    def _draw_input(self):
        glPushMatrix()
        self.configure_3d_projection(-400, 0)

        self._draw_unit_cube()

        glColor3f(0,0,0)
        glPointSize(5.0)
        glBegin(GL_POINTS)
        glVertex3f(*self.input)
        glEnd()

        glPopMatrix()

    def _draw_unit_cube(self):
        glColor4f(0,0,0,0.2)
        glutWireCube(2.0)

window.run(FollowerDemo)
