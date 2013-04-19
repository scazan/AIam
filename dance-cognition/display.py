import window
from vector import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from states import state_machine, InterStatePosition
from simple_osc_receiver import OscReceiver
from argparse import ArgumentParser

MOUSE_REACTIVITY = 5.0

class Display(window.Window):
    def InitGL(self):
        window.Window.InitGL(self)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def render(self):
        osc_receiver.serve()
        self._draw_input()
        self._draw_output()

    def _draw_output(self):
        glPushMatrix()
        self.configure_3d_projection(100, 0)
        self._draw_unit_cube()
        self._draw_states_as_points()
        self._draw_transitions_as_lines()
        self._draw_output_position()
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

    def _draw_output_position(self):
        if output_inter_state_position:
            glColor3f(1,0,0)
            glPointSize(5.0)
            glBegin(GL_POINTS)
            glVertex3f(*state_machine.inter_state_to_euclidian_position(output_inter_state_position))
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

def receive_input_position(path, args, types, src, user_data):
    global input_position
    position_tuple = args
    input_position = Vector3d(*position_tuple)

def receive_output_position(path, args, types, src, user_data):
    global output_inter_state_position
    source_state_name, output_state_name, relative_position = args
    source_state = state_machine.states[source_state_name]
    output_state = state_machine.states[output_state_name]
    output_inter_state_position = InterStatePosition(
        source_state, output_state, relative_position)

input_position = Vector3d(0, 0, 0)
osc_receiver = OscReceiver(7892, listen="localhost")
osc_receiver.add_method("/input_position", "fff", receive_input_position)
osc_receiver.add_method("/position", "ssf", receive_output_position)
osc_receiver.start()

output_inter_state_position = None

parser = ArgumentParser()
window.Window.add_parser_arguments(parser)
args = parser.parse_args()
window.run(Display, args)
