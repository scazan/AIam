from experiment import *

class BvhStimulus(Stimulus):
    def __str__(self):
        return "BvhStimulus"

    def get_value(self):
        vertices = bvh_reader.get_skeleton_vertices(self._t * args.bvh_speed)
        hips = bvh_reader.normalize_vector(bvh_reader.vertex_to_vector(vertices[0]))
        return hips

    def get_duration(self):
        return bvh_reader.get_duration() / args.bvh_speed

class CircularStimulus(Stimulus):
    def __str__(self):
        return "CircularStimulus"

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

if args.bvh:
    stimulus = BvhStimulus()
else:
    stimulus = CircularStimulus()

print "stimulus: %s" % stimulus

student = BackpropNet(3, 6, 3)
run_experiment(student, stimulus, PointWindow, args)
