from ui.ui import *

FLOOR_SPOT_RADIUS = 1
FLOOR_GRID_SIZE = 9
MIN_OUTPUT_OPACITY = 0.75
MIN_LINE_WIDTH = 1.5
MAX_LINE_WIDTH = 3.0

class Scene(BvhScene):
    def __init__(self, *args, **kwargs):
        BvhScene.__init__(self, *args, **kwargs)
        self._camera_translation = numpy.zeros(2)
        self._camera_movement = None
        self._floor_spot_display_list_id = None

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
        glColor3f(*self._parent.color_scheme["input"])
        self._draw_vertices(vertices)

    def draw_output(self, vertices):
        self._update_camera_translation(vertices)
        self._draw_vertices(vertices)

    def _draw_vertices(self, vertices):
        edges = self.bvh_reader.vertices_to_edges(vertices)
        edge_distance_pairs = [
            (edge, self._edge_distance_to_camera(edge))
            for edge in edges]
        distances = [edge_distance_pair[1] for edge_distance_pair in edge_distance_pairs]
        min_distance = min(distances)
        max_distance = max(distances)

        sorted_edge_distance_pairs = sorted(
            edge_distance_pairs,
            key=lambda edge_distance_pair: -edge_distance_pair[1])
        for edge, distance in sorted_edge_distance_pairs:
            normalized_distance = (distance - min_distance) / (max_distance - min_distance)
            relative_vicinity = 1 - normalized_distance
            self._set_output_color_by_relative_vicinity(relative_vicinity)
            self._set_line_width_by_relative_vicinity(relative_vicinity)
            self._draw_line(edge.v1, edge.v2)

    def _set_output_color_by_relative_vicinity(self, relative_vicinity):
        opacity = MIN_OUTPUT_OPACITY + relative_vicinity * (1 - MIN_OUTPUT_OPACITY)
        fg_r, fg_g, fg_b = self._parent.color_scheme["output"]
        bg_r, bg_g, bg_b, bg_a = self._parent.color_scheme["background"]
        r = bg_r + (fg_r - bg_r) * opacity
        g = bg_g + (fg_g - bg_g) * opacity
        b = bg_b + (fg_b - bg_b) * opacity
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

    def centralize_output(self, processed_output):
        self._camera_movement = CameraMovement(
            source=self._camera_translation,
            target=-self.central_output_position(processed_output))

    def central_output_position(self, output):
        root_vertex = output[0]
        return numpy.array([root_vertex[0], root_vertex[2]])

    def draw_floor(self):
        if self.processed_output is not None:
            central_output_position = self.central_output_position(self.processed_output)
            self._draw_floor_spots(
                center_x=central_output_position[0],
                center_z=central_output_position[1])
            self._draw_floor_shader(
                x = -(self._camera_position[0] + self._camera_translation[0]),
                z = -(self._camera_position[2] + self._camera_translation[1]))

    def _draw_floor_spots(self, center_x, center_z):
        cell_size = FLOOR_SPOT_RADIUS * 2
        quantified_center_x = int(center_x / cell_size / 2) * cell_size * 2
        quantified_center_z = int(center_z / cell_size) * cell_size
        for nx in range(FLOOR_GRID_SIZE):
            x = quantified_center_x + (nx - float(FLOOR_GRID_SIZE)/2 + 0.5) * cell_size
            if nx % 2 == 0:
                offset_z = 0
            else:
                offset_z = FLOOR_SPOT_RADIUS
            for nz in range(FLOOR_GRID_SIZE):
                z = offset_z + quantified_center_z + (nz - float(FLOOR_GRID_SIZE)/2 + 0.5) * cell_size
                self._draw_floor_spot(x=x, z=z)

    def _draw_floor_spot(self, x, z, y=0):
        if self._floor_spot_display_list_id is None:
            self._create_floor_spot_display_list()
        glPushMatrix()
        glTranslatef(x, y, z)
        glCallList(self._floor_spot_display_list_id)
        glPopMatrix()

    def _create_floor_spot_display_list(self, resolution=15):
        floor_color = self._parent.color_scheme["floor"]
        color_r, color_g, color_b, color_a = floor_color
        angle_increment = (float) (2 * math.pi / resolution);
        self._floor_spot_display_list_id = glGenLists(1)
        glNewList(self._floor_spot_display_list_id, GL_COMPILE)
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(*floor_color)
        glVertex3f(0, 0, 0)
        glColor4f(color_r, color_g, color_b, 0)
        for i in range(resolution):
            angle1 = angle_increment * i
            angle2 = angle_increment * (i+1)
            glVertex3f(math.cos(angle1) * FLOOR_SPOT_RADIUS, 0, math.sin(angle1) * FLOOR_SPOT_RADIUS)
            glVertex3f(math.cos(angle2) * FLOOR_SPOT_RADIUS, 0, math.sin(angle2) * FLOOR_SPOT_RADIUS)
        glEnd()
        glEndList()

    def _draw_floor_shader(self, x, z, y=0, resolution=15):
        radius = FLOOR_SPOT_RADIUS * 2 * FLOOR_GRID_SIZE * 1.5
        bg_r, bg_g, bg_b, bg_a = self._parent.color_scheme["background"]
        angle_increment = (float) (2 * math.pi / resolution);
        glPushMatrix()
        glTranslatef(x, 0, z)
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(bg_r, bg_g, bg_b, 0)
        glVertex3f(0, 0, 0)
        glColor4f(bg_r, bg_g, bg_b, 1)
        for i in range(resolution):
            angle1 = angle_increment * i
            angle2 = angle_increment * (i+1)
            glVertex3f(math.cos(angle1) * radius, 0, math.sin(angle1) * radius)
            glVertex3f(math.cos(angle2) * radius, 0, math.sin(angle2) * radius)
        glEnd()
        glPopMatrix()
