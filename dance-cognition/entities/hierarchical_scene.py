from ui.ui import *

MIN_OUTPUT_STRENGTH = 0.75
MIN_LINE_WIDTH = 1.5
MAX_LINE_WIDTH = 3.0

class Scene(BvhScene):
    @staticmethod
    def add_parser_arguments(parser):
        BvhScene.add_parser_arguments(parser)
        parser.add_argument("--enable-light-source", action="store_true")
        parser.add_argument("--enable-shadow", action="store_true")

    def __init__(self, *args, **kwargs):
        BvhScene.__init__(self, *args, **kwargs)
        self.feature_match_result = None
        if self.args.enable_shadow:
            self._shadow_shear_matrix = self._create_shadow_shear_matrix()

    def _create_shadow_shear_matrix(self):
        Ky = 0
        Kx = 0.5
        return [ 
            1, Ky, 0, 0, 
            Kx, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1]

    def render_io(self):
        if self.feature_match_result is None:
            BvhScene.render_io(self)
        else:
            self._render_feature_matches()

    def draw_input(self, vertices):
        self._process_vertices(vertices)
        self._draw_vertices(self._parent.color_scheme["input"])

    def draw_output(self, vertices, opacity=1):
        self._process_vertices(vertices)
        if self.args.enable_shadow:
            self._draw_vertices_as_shadow()
        color = self._get_color_by_opacity(self._parent.color_scheme["output"], opacity)
        self._draw_vertices(color)

    def _get_color_by_opacity(self, foreground_color, opacity):
        fg_r, fg_g, fg_b = foreground_color
        bg_r, bg_g, bg_b, bg_a = self._parent.color_scheme["background"]
        r = bg_r + (fg_r - bg_r) * opacity
        g = bg_g + (fg_g - bg_g) * opacity
        b = bg_b + (fg_b - bg_b) * opacity
        return r, g, b

    def get_root_vertex(self, processed_output):
        root_vertex = processed_output[0]
        return numpy.array([
                root_vertex[self.bvh_coordinate_left],
                root_vertex[self.bvh_coordinate_far]])

    def _process_vertices(self, vertices):
        edges = self.bvh_reader.vertices_to_edges(vertices)
        if self.args.enable_light_source:
            edge_distance_pairs = [
                (edge, self._edge_distance_to_camera(edge))
                for edge in edges]
            distances = [edge_distance_pair[1] for edge_distance_pair in edge_distance_pairs]
            self._min_distance = min(distances)
            self._max_distance = max(distances)
            self._sorted_edge_distance_pairs = sorted(
                edge_distance_pairs,
                key=lambda edge_distance_pair: -edge_distance_pair[1])
        else:
            self._edges = edges

    def _draw_vertices(self, color):
        if self.args.enable_light_source:
            self._draw_vertices_with_light_source(color)
        else:
            self._draw_vertices_without_light_source(color)

    def _draw_vertices_without_light_source(self, color):
        glColor3f(*color)
        glLineWidth(3.0)
        for edge in self._edges:
            self._draw_line(edge.v1, edge.v2)
            
    def _draw_vertices_with_light_source(self, color):
        for edge, distance in self._sorted_edge_distance_pairs:
            normalized_distance = (distance - self._min_distance) / (self._max_distance - self._min_distance)
            relative_vicinity = 1 - normalized_distance
            self._set_color_by_relative_vicinity(color, relative_vicinity)
            self._set_line_width_by_relative_vicinity(relative_vicinity)
            self._draw_line(edge.v1, edge.v2)

    def _set_color_by_relative_vicinity(self, foreground_color, relative_vicinity):
        opacity = MIN_OUTPUT_STRENGTH + relative_vicinity * (1 - MIN_OUTPUT_STRENGTH)
        glColor3f(*self._get_color_by_opacity(foreground_color, opacity))

    def _set_line_width_by_relative_vicinity(self, relative_vicinity):
        glLineWidth(MIN_LINE_WIDTH + relative_vicinity * (MAX_LINE_WIDTH - MIN_LINE_WIDTH))

    def _edge_distance_to_camera(self, edge):
        return self._distance_to_camera(edge.v1) + self._distance_to_camera(edge.v2)

    def _distance_to_camera(self, vertex):
        return math.sqrt(
            pow(vertex[self.bvh_coordinate_up] + (
                    self._camera_position[0] +
                    self._camera_translation[0]), 2) +
            pow(vertex[self.bvh_coordinate_far] + (
                    self._camera_position[2] +
                    self._camera_translation[1]), 2))

    def _draw_line(self, v1, v2):
        glBegin(GL_LINES)
        self.bvh_vertex(v1)
        self.bvh_vertex(v2)
        glEnd()

    def _draw_vertices_as_shadow(self):
        glPushMatrix()
        self.configure_3d_projection()
        glScalef(1, 0, 1)
        glMultMatrixf(self._shadow_shear_matrix)
        self._draw_vertices(color=self._parent.color_scheme["shadow"])
        glPopMatrix()

    def _render_feature_matches(self):
        for processed_output, opacity in self.feature_match_result:
            self._render_feature_match(processed_output, opacity)

    def _render_feature_match(self, processed_output, opacity):
        self._draw_io(
            processed_output, self.draw_output, self.args.output_y_offset, opacity=opacity)
