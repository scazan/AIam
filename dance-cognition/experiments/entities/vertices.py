from experiment import *

class Entity(BaseEntity):
    def get_value(self):
        vertices = self.bvh_reader.get_skeleton_vertices(self._t * self.args.bvh_speed)
        normalized_vectors = numpy.array(
            [self.bvh_reader.normalize_vector(vertex)
             for vertex in vertices])
        return normalized_vectors.flatten()

    def process_io(self, value):
        normalized_vectors = value.reshape([self.bvh_reader.num_joints, 3])
        vertices = [self.bvh_reader.skeleton_scale_vector(vector)
                    for vector in normalized_vectors]
        return vertices

class Scene(BaseScene):
    def draw_input(self, inp):
        glColor3f(0, 1, 0)
        self._draw_skeleton(inp)

    def draw_output(self, output):
        glColor3f(0.5, 0.5, 1.0)
        self._draw_skeleton(output)

    def _draw_skeleton(self, vertices):
        glLineWidth(2.0)
        edges = self.bvh_reader.vertices_to_edges(vertices)
        for edge in edges:
            vector1 = self.bvh_reader.normalize_vector(edge.v1)
            vector2 = self.bvh_reader.normalize_vector(edge.v2)
            self._draw_line(vector1, vector2)

    def _draw_line(self, v1, v2):
        glBegin(GL_LINES)
        glVertex3f(*v1)
        glVertex3f(*v2)
        glEnd()
