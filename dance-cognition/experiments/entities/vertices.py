from experiment import *

class Stimulus(BaseStimulus):
    def get_value(self):
        vertices = self.bvh_reader.get_skeleton_vertices(self._t * self.args.bvh_speed)
        normalized_vectors = numpy.array(
            [self.bvh_reader.normalize_vector(self.bvh_reader.vertex_to_vector(vertex))
             for vertex in vertices])
        return normalized_vectors.flatten()

class Scene(BaseScene):
    def draw_input(self, inp):
        glColor3f(0, 1, 0)
        input_vectors = inp.reshape([self.bvh_reader.num_joints, 3])
        self._draw_skeleton(input_vectors)

    def draw_output(self, output):
        glColor3f(0.5, 0.5, 1.0)
        output_vectors = output.reshape([self.bvh_reader.num_joints, 3])
        self._draw_skeleton(output_vectors)

    def _draw_skeleton(self, normalized_vectors):
        glLineWidth(2.0)
        vertices = [self.bvh_reader.vector_to_vertex(self.bvh_reader.skeleton_scale_vector(vector))
                    for vector in normalized_vectors]
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
