from experiment import *
from angle_parameters import radians_to_vector2d, vector2d_to_radians
from dimensionality_reduction import PCA

class CircularStimulus(Stimulus):
    def get_value(self):
        r = self._t % (2*math.pi) - math.pi
        return radians_to_vector2d(r)

    def get_duration(self):
        return 2 * math.pi

class AngleScene(ExperimentScene):
    def draw_input(self, inp):
        glColor3f(0, 1, 0)
        self._draw_angle(vector2d_to_radians(inp))

    def draw_output(self, output):
        glColor3f(0.5, 0.5, 1.0)
        self._draw_angle(vector2d_to_radians(output))

    def _draw_angle(self, r):
        z = math.cos(r)
        y = math.sin(r)
        x = 0
        glPointSize(3)
        glBegin(GL_POINTS)
        glVertex3f(x, y, z)
        glEnd()


parser = ArgumentParser()
add_parser_arguments(parser)
args = parser.parse_args()

experiment = Experiment(AngleScene, args)
stimulus = CircularStimulus()
student = PCA(n_components=1)
experiment.run(student, stimulus)
