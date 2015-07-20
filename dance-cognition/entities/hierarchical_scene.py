from ui.ui import *

MIN_OUTPUT_STRENGTH = 0.75
MIN_LINE_WIDTH = 1.5
MAX_LINE_WIDTH = 3.0

class Scene(BvhScene):
    def __init__(self, *args, **kwargs):
        BvhScene.__init__(self, *args, **kwargs)
        self._camera_translation = numpy.zeros(2)
        self._camera_movement = None
        self._shadow_shear_matrix = self._create_shadow_shear_matrix()

    def _create_shadow_shear_matrix(self):
        Ky = 0
        Kx = 0.5
        return [ 
            1, Ky, 0, 0, 
            Kx, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1]

    def camera_translation(self):
        return self._camera_translation

    def _update_camera_translation(self, vertices):
        if self._camera_translation is None:
            root_vertex = vertices[0]
            self._camera_translation = numpy.array([-root_vertex[0], -root_vertex[2]])
        elif self._camera_movement and self._camera_movement.is_active():
            self._camera_translation = self._camera_movement.translation()
            self._camera_movement.proceed(self.parent().time_increment)

    def draw_input(self, vertices):
        self._process_vertices(vertices)
        self._draw_vertices(self._parent.color_scheme["input"])

    def draw_output(self, vertices):
        self._update_camera_translation(vertices)
        self._process_vertices(vertices)
        self._draw_vertices_as_shadow()
        self._draw_vertices(self._parent.color_scheme["output"])

    def _process_vertices(self, vertices):
        edges = self.bvh_reader.vertices_to_edges(vertices)
        edge_distance_pairs = [
            (edge, self._edge_distance_to_camera(edge))
            for edge in edges]
        distances = [edge_distance_pair[1] for edge_distance_pair in edge_distance_pairs]
        self._min_distance = min(distances)
        self._max_distance = max(distances)

        self._sorted_edge_distance_pairs = sorted(
            edge_distance_pairs,
            key=lambda edge_distance_pair: -edge_distance_pair[1])

    def _draw_vertices(self, color):
        for edge, distance in self._sorted_edge_distance_pairs:
            normalized_distance = (distance - self._min_distance) / (self._max_distance - self._min_distance)
            relative_vicinity = 1 - normalized_distance
            self._set_color_by_relative_vicinity(color, relative_vicinity)
            self._set_line_width_by_relative_vicinity(relative_vicinity)
            self._draw_line(edge.v1, edge.v2)

    def _set_color_by_relative_vicinity(self, foreground_color, relative_vicinity):
        strength = MIN_OUTPUT_STRENGTH + relative_vicinity * (1 - MIN_OUTPUT_STRENGTH)
        fg_r, fg_g, fg_b = foreground_color
        bg_r, bg_g, bg_b, bg_a = self._parent.color_scheme["background"]
        r = bg_r + (fg_r - bg_r) * strength
        g = bg_g + (fg_g - bg_g) * strength
        b = bg_b + (fg_b - bg_b) * strength
        glColor3f(r, g, b)

    def _set_line_width_by_relative_vicinity(self, relative_vicinity):
        glLineWidth(MIN_LINE_WIDTH + relative_vicinity * (MAX_LINE_WIDTH - MIN_LINE_WIDTH))

    def _edge_distance_to_camera(self, edge):
        return self._distance_to_camera(edge.v1) + self._distance_to_camera(edge.v2)

    def _distance_to_camera(self, vertex):
        return math.sqrt(pow(vertex[0] + (self._camera_position[0] + self._camera_translation[0]), 2) +
                         pow(vertex[2] + (self._camera_position[2] + self._camera_translation[1]), 2))

    def _draw_line(self, v1, v2):
        glBegin(GL_LINES)
        glVertex3f(*v1)
        glVertex3f(*v2)
        glEnd()

    def _draw_vertices_as_shadow(self):
        glPushMatrix()
        self.configure_3d_projection()
        glScalef(1, 0, 1)
        glMultMatrixf(self._shadow_shear_matrix)
        self._draw_vertices(color=self._parent.color_scheme["shadow"])
        glPopMatrix()

    def centralize_output(self, processed_output):
        self._camera_movement = CameraMovement(
            source=self._camera_translation,
            target=-self.central_output_position(processed_output))

    def central_output_position(self, output):
        root_vertex = output[0]
        return numpy.array([root_vertex[0], root_vertex[2]])
