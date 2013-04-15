import window
from vector import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from states import state_machine
from osc_receiver import OscReceiver

MOUSE_REACTIVITY = 5.0

class FollowerDemo(window.Window):
    def __init__(self, *args):
        window.Window.__init__(self, *args)

    def InitGL(self):
        window.Window.InitGL(self)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def _clamp(self, value):
        return max(min(value, 1.0), -1.0)

    def render(self):
        self._draw_input()
        self._draw_output()

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
        glVertex3f(*input_position)
        glEnd()

        glPopMatrix()

    def _draw_unit_cube(self):
        glColor4f(0,0,0,0.2)
        glutWireCube(2.0)


def receive_input(path, args, types, src, user_data):
    global input_position
    position_tuple = args
    input_position = Vector3d(*position_tuple)

input_position = Vector3d(0, 0, 0)
osc_receiver = OscReceiver(50001)
osc_receiver.add_method("/input_position", "fff", receive_input)
osc_receiver.start()
window.run(FollowerDemo)
