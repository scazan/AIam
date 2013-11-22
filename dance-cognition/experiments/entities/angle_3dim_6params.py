from experiment import *
from angle_parameters import euler_to_vector6d, vector6d_to_euler

class Stimulus(BaseStimulus):
    def get_value(self):
        r1 = (self._t / 1) % (2*math.pi)
        r2 = (self._t / 2) % (2*math.pi)
        r3 = (self._t / 4) % (2*math.pi)
        return euler_to_vector6d(r1, r2, r3)

    def get_duration(self):
        return 2 * math.pi * 4

class Scene(BaseScene):
    def draw_input(self, inp):
        glColor3f(0, 1, 0)
        self._draw_3dim_angle(*vector6d_to_euler(inp))

    def draw_output(self, output):
        glColor3f(0.5, 0.5, 1.0)
        self._draw_3dim_angle(*vector6d_to_euler(output))

    def _draw_3dim_angle(self, r1, r2, r3):
        glPointSize(3)
        glRotatef(math.degrees(r1), 1., 0., 0.)
        glRotatef(math.degrees(r2), 0., 1., 0.)
        glRotatef(math.degrees(r3), 0., 0., 1.)
        glBegin(GL_POINTS)
        glVertex3f(1, 0, 0)
        glEnd()
