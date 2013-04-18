import window
from vector import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from states import state_machine
from osc_receiver import OscReceiver
from follower import Follower
import time

MOUSE_REACTIVITY = 5.0

class FollowerDemo(window.Window):
    def InitGL(self):
        window.Window.InitGL(self)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def render(self):
        self._draw_input()
        self._draw_output()

    def _draw_output(self):
        glPushMatrix()
        self.configure_3d_projection(100, 0)
        self._draw_unit_cube()
        self._draw_states_as_points()
        self._draw_transitions_as_lines()
        self._draw_follower()
        glPopMatrix()

    def _draw_states_as_points(self):
        glColor3f(0,0,0)
        glPointSize(5.0)
        glBegin(GL_POINTS)
        for state in state_machine.states.values():
            glVertex3f(*state.position)
        glEnd()

    def _draw_transitions_as_lines(self):
        glColor4f(0,0,0,0.2)
        glBegin(GL_LINES)
        for input_state, output_state in state_machine.transitions:
            glVertex3f(*input_state.position)
            glVertex3f(*output_state.position)
        glEnd()

    def _draw_follower(self):
        if follower.inter_state_position:
            glColor3f(1,0,0)
            glPointSize(5.0)
            glBegin(GL_POINTS)
            glVertex3f(*state_machine.inter_state_to_euclidian_position(follower.inter_state_position))
            glEnd()

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
    global input_position, last_input_time
    now = time.time()
    if last_input_time is None:
        time_increment = 0.0
    else:
        time_increment = now - last_input_time
    position_tuple = args
    input_position = Vector3d(*position_tuple)
    follower.follow(input_position, time_increment)
    last_input_time = now

input_position = Vector3d(0, 0, 0)
follower = Follower(state_machine)
last_input_time = None
osc_receiver = OscReceiver(50001)
osc_receiver.add_method("/input_position", "fff", receive_input)
osc_receiver.start()
window.run(FollowerDemo)
