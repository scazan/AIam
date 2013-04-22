import window
from vector import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from states import state_machine, InterStatePosition
from simple_osc_receiver import OscReceiver
from argparse import ArgumentParser

MOUSE_REACTIVITY = 5.0
INPUT_COLOR = (0,0,1)
OUTPUT_COLOR = (1,0,0)
OBSERVED_STATE_COLOR = (0,1,0)
TEXT_SIZE = 0.15

class Display(window.Window):
    def InitGL(self):
        window.Window.InitGL(self)
        glutMouseFunc(self._mouse_clicked)
        glutMotionFunc(self._mouse_moved)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self._y_orientation = 0.0
        self._x_orientation = 0.0

    def render(self):
        osc_receiver.serve()
        self._draw_input()
        self._draw_output()

    def _draw_output(self):
        glPushMatrix()
        self.configure_3d_projection(100, 0)
        glRotatef(self._x_orientation, 1.0, 0.0, 0.0)
        glRotatef(self._y_orientation, 0.0, 1.0, 0.0)
        self._draw_unit_cube()
        self._draw_transitions_as_lines()
        self._draw_states_as_points()
        self._draw_state_name()
        self._draw_sensed_input_position()
        self._draw_output_position()
        glPopMatrix()

    def _draw_states_as_points(self):
        glPointSize(5.0)
        for state in state_machine.states.values():
            glBegin(GL_POINTS)
            if state == observed_state:
                glColor3f(*OBSERVED_STATE_COLOR)
            else:
                glColor3f(0,0,0)
            glVertex3f(*state.position)
            glEnd()

    def _draw_state_name(self):
        glColor3f(0,0,0)
        for state in state_machine.states.values():
            self.draw_text(state.name, TEXT_SIZE, *state.position)

    def _draw_transitions_as_lines(self):
        glColor4f(0,0,0,0.2)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        for input_state, output_state in state_machine.transitions:
            glVertex3f(*input_state.position)
            glVertex3f(*output_state.position)
        glEnd()

    def _draw_output_position(self):
        if output_inter_state_position:
            output_position = state_machine.inter_state_to_euclidian_position(output_inter_state_position)
            self._draw_position(output_position, OUTPUT_COLOR)

    def _draw_input(self):
        glPushMatrix()
        self.configure_3d_projection(-300, 0)
        self._draw_unit_cube()
        self._draw_raw_input_position()
        glPopMatrix()

    def _draw_raw_input_position(self):
        self._draw_position(raw_input_position, INPUT_COLOR)

    def _draw_sensed_input_position(self):
        self._draw_position(sensed_input_position, INPUT_COLOR)

    def _draw_position(self, position, color):
        if position is None:
            return
        glColor3f(*color)
        glPointSize(5.0)
        glBegin(GL_POINTS)
        glVertex3f(*position)
        glEnd()

    def _draw_unit_cube(self):
        glColor4f(0,0,0,0.2)
        glutWireCube(2.0)

    def _mouse_clicked(self, button, state, x, y):
        if button == GLUT_LEFT_BUTTON:
            self._dragging_orientation = (state == GLUT_DOWN)
        if state == GLUT_DOWN:
            self._drag_x_previous = x
            self._drag_y_previous = y

    def _mouse_moved(self, x, y):
        if self._dragging_orientation:
            self._y_orientation += x - self._drag_x_previous
            self._x_orientation -= y - self._drag_y_previous

def receive_raw_input_position(path, args, types, src, user_data):
    global raw_input_position
    position_tuple = args
    raw_input_position = Vector3d(*position_tuple)

def receive_sensed_input_position(path, args, types, src, user_data):
    global sensed_input_position
    position_tuple = args
    sensed_input_position = Vector3d(*position_tuple)

def receive_output_position(path, args, types, src, user_data):
    global output_inter_state_position
    source_state_name, output_state_name, relative_position = args
    source_state = state_machine.states[source_state_name]
    output_state = state_machine.states[output_state_name]
    output_inter_state_position = InterStatePosition(
        source_state, output_state, relative_position)

def receive_observed_state(path, args, types, src, user_data):
    global observed_state
    observed_state_name = args[0]
    if observed_state_name:
        observed_state = state_machine.states[observed_state_name]
    else:
        observed_state = None

raw_input_position = None
sensed_input_position = None
observed_state = None
osc_receiver = OscReceiver(7892, listen="localhost")
osc_receiver.add_method("/raw_input_position", "fff", receive_raw_input_position)
osc_receiver.add_method("/sensed_input_position", "fff", receive_sensed_input_position)
osc_receiver.add_method("/position", "ssf", receive_output_position)
osc_receiver.add_method("/observed_state", "s", receive_observed_state)
osc_receiver.start()

output_inter_state_position = None

parser = ArgumentParser()
window.Window.add_parser_arguments(parser)
args = parser.parse_args()
window.run(Display, args)
