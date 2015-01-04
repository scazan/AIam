from ui.ui import *
import math
import transformations
import so3

class Scene(BaseScene):
    def draw_input(self, inp):
        glColor3f(0, 1, 0)
        self._draw_expmap_rotation(inp)

    def draw_output(self, output):
        glColor3f(0.5, 0.5, 1.0)
        self._draw_expmap_rotation(output)

    def _draw_expmap_rotation(self, axis_angle_parameters):
        axis_angle = (axis_angle_parameters[0:3], axis_angle_parameters[3])
        R = so3.from_axis_angle(axis_angle)
        matrix = so3.matrix(R)
        x, y, z = transformations.euler_from_matrix(matrix)
        glRotatef(math.degrees(x), 1., 0., 0.)
        glRotatef(math.degrees(y), 0., 1., 0.)
        glRotatef(math.degrees(z), 0., 0., 1.)
        glScale(.5, .5, .5)
        glBegin(GL_LINE_STRIP)
        glVertex3f(0, 0, 0)
        glVertex3f(1, 0, 0)
        glVertex3f(1, 1, 0)
        glEnd()
