from ui.ui import *

class Scene(BaseScene):
    def __init__(self, *args, **kwargs):
        BaseScene.__init__(self, *args, **kwargs)
        self._camera_translation = None
        self._camera_movement = None

    def camera_translation(self):
        if self._camera_translation is not None:
            return self._camera_translation
        else:
            return numpy.zeros(3)

    def _update_camera_translation(self, vertices):
        if self._camera_translation is None:
            self._camera_translation = -vertices[0]
        elif self._camera_movement and self._camera_movement.is_active():
            self._camera_translation = self._camera_movement.translation()
            self._camera_movement.proceed(self.parent().time_increment)

    def draw_input(self, vertices):
        glColor3f(0, 1, 0)
        self._draw_vertices(vertices)

    def draw_output(self, vertices):
        self._update_camera_translation(vertices)
        glColor3f(0, 0, 0)
        self._draw_vertices(vertices)

    def parameters_to_hips(self, parameters):
        return self._parameters_to_joint(parameters)

    def _draw_vertices(self, vertices):
        edges = self.bvh_reader.vertices_to_edges(vertices)
        glLineWidth(2.0)
        for edge in edges:
            self._draw_line(edge.v1, edge.v2)

    def _draw_line(self, v1, v2):
        glBegin(GL_LINES)
        glVertex3f(*v1)
        glVertex3f(*v2)
        glEnd()

    def centralize_output(self, processed_output):
        self._camera_movement = CameraMovement(
            source=self._camera_translation,
            target=-self.central_output_position(processed_output))

    def central_output_position(self, output):
        hip_vertex = output[0]
        return numpy.array([hip_vertex[0], 0, hip_vertex[2]])
