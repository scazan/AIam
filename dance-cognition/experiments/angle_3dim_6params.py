from experiment import *
from angle_parameters import radians_to_vector2d, vector2d_to_radians
import numpy

class SphericalStimulus(Stimulus):
    def get_value(self):
        r1 = (self._t / 1) % (2*math.pi)
        r2 = (self._t / 2) % (2*math.pi)
        r3 = (self._t / 4) % (2*math.pi)
        return numpy.append(
            radians_to_vector2d(r1),
            numpy.append(
                radians_to_vector2d(r2),
                radians_to_vector2d(r3)))

    def get_duration(self):
        return 2 * math.pi * 4

class AngleWindow(ExperimentWindow):
    def draw_input(self, inp):
        glColor3f(0, 1, 0)
        self._draw_3dim_angle(*self._vector6d_to_3radians(inp))

    def draw_output(self, output):
        glColor3f(0.5, 0.5, 1.0)
        self._draw_3dim_angle(*self._vector6d_to_3radians(output))

    def _vector6d_to_3radians(self, vector6d):
        r1 = vector2d_to_radians(vector6d[0:2])
        r2 = vector2d_to_radians(vector6d[2:4])
        r3 = vector2d_to_radians(vector6d[4:6])
        return r1, r2, r3

    def _draw_3dim_angle(self, r1, r2, r3):
        glPointSize(3)
        glRotatef(math.degrees(r1), 1., 0., 0.)
        glRotatef(math.degrees(r2), 0., 1., 0.)
        glRotatef(math.degrees(r3), 0., 0., 1.)
        glBegin(GL_POINTS)
        glVertex3f(1, 0, 0)
        glEnd()


parser = ArgumentParser()
add_parser_arguments(parser)
args = parser.parse_args()

experiment = Experiment(AngleWindow, args)
stimulus = SphericalStimulus()
student = BackpropNet(6, 12, 6)
experiment.run(student, stimulus)
