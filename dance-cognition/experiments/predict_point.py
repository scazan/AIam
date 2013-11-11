from prediction_experiment import *

class BvhStimulus(Stimulus):
    def __init__(self, bvh_reader):
        Stimulus.__init__(self)
        self.bvh_reader = bvh_reader

    def get_value(self):
        vertices = self.bvh_reader.get_skeleton_vertices(self._t * args.bvh_speed)
        hips = self.bvh_reader.normalize_vector(self.bvh_reader.vertex_to_vector(vertices[0]))
        return hips

    def get_duration(self):
        return self.bvh_reader.get_duration() / args.bvh_speed

class CircularStimulus(Stimulus):
    def get_value(self):
        z = math.cos(self._t)
        y = math.sin(self._t)
        x = 0
        return [x, y, z]

    def get_duration(self):
        return 2 * math.pi

class PointWindow(ExperimentWindow):
    def draw_input(self, inp):
        glColor3f(0, 1, 0)
        self._draw_point(inp)

    def draw_output(self, output):
        glColor3f(0.5, 0.5, 1.0)
        self._draw_point(output)

    def _draw_point(self, p):
        glPointSize(3)
        glBegin(GL_POINTS)
        glVertex3f(p[0], p[1], p[2])
        glEnd()


parser = ArgumentParser()
add_parser_arguments(parser)
args = parser.parse_args()

experiment = Experiment(PointWindow, args)

if args.bvh:
    stimulus = BvhStimulus(experiment.bvh_reader)
else:
    stimulus = CircularStimulus()

student = BackpropNet(3, 6, 3)
experiment.run(student, stimulus)
