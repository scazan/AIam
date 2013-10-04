from experiment import *
from skeleton_hierarchy_parameters import *
from dimensionality_reduction import PCA

class BvhStimulus(Stimulus):
    def __init__(self, bvh_reader):
        Stimulus.__init__(self)
        self.bvh_reader = bvh_reader

    def get_value(self):
        hips = self.bvh_reader.get_hips(self._t * args.bvh_speed)
        return skeleton_parametrization.joint_to_parameters(hips)

    def get_duration(self):
        return self.bvh_reader.get_duration()

class HierarchicalWindow(ExperimentWindow):
    def draw_input(self, parameters):
        glColor3f(0, 1, 0)
        self._draw_skeleton(parameters)

    def draw_output(self, parameters):
        glColor3f(0.5, 0.5, 1.0)
        self._draw_skeleton(parameters)

    def _draw_skeleton(self, parameters):
        hips = skeleton_parametrization.parameters_to_joint(parameters)
        vertices = hips.get_vertices()
        
        glLineWidth(2.0)
        edges = self.bvh_reader.vertices_to_edges(vertices)
        for edge in edges:
            vector1 = self.bvh_reader.normalize_vector(self.bvh_reader.vertex_to_vector(edge.v1))
            vector2 = self.bvh_reader.normalize_vector(self.bvh_reader.vertex_to_vector(edge.v2))
            self._draw_line(vector1, vector2)

    def _draw_line(self, v1, v2):
        glBegin(GL_LINES)
        glVertex3f(*v1)
        glVertex3f(*v2)
        glEnd()

parser = ArgumentParser()
add_parser_arguments(parser)
args = parser.parse_args()

experiment = Experiment(HierarchicalWindow, args)
skeleton_parametrization = SkeletonHierarchyParametrization(experiment.bvh_reader)
stimulus = BvhStimulus(experiment.bvh_reader)
num_skeleton_parameters = len(stimulus.get_value())

student = PCA(n_components=4)
experiment.run(student, stimulus)
