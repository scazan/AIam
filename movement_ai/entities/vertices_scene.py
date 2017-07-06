from ui.ui import *

class Scene(BvhScene):
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
