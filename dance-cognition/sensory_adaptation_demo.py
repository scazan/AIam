from sensory_adaptation import SensoryAdapter
import window
from vector import Vector2d
from input_noise import input_noise
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

MOUSE_REACTIVITY = 5.0

class Frame(window.Frame):
    def draw_point(self, p):
        glPointSize(3)
        glBegin(GL_POINTS)
        glVertex2f((p.x/2 + 0.5) * self.width,
                   (p.y/2 + 0.5) * self.height)
        glEnd()

class InputFrame(Frame):
    def render(self):
        glColor3f(0, 0, 0)
        self.draw_point(self.window.input)

        glColor3f(0.5, 0.5, 1.0)
        self.draw_point(self.window.sensory_adapter.background())

class OutputFrame(Frame):
    def render(self):
        glColor3f(0, 0, 0)
        self.draw_point(self.window.output)

class SensoryAdaptationDemo(window.Window):
    def __init__(self, *args):
        window.Window.__init__(self, *args)
        self.input_frame = InputFrame(
            self, left=100, top=100, width=200, height=200)
        self.output_frame = OutputFrame(
            self, left=400, top=100, width=200, height=200)
        self.input = Vector2d(0, 0)
        self.output = Vector2d(0, 0)
        self.sensory_adapter = SensoryAdapter()

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
        self.sensory_adapter.feed_stimulus(self.input, self.time_increment)
        self.output = self.sensory_adapter.response()
        self.input += input_noise()

window.run(SensoryAdaptationDemo)
