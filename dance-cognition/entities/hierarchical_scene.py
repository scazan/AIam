from ui.ui import *

class Scene(BvhScene):
    def __init__(self, *args, **kwargs):
        BvhScene.__init__(self, *args, **kwargs)
        self._camera_translation = None
        self._camera_movement = None

    def camera_translation(self):
        if self._camera_translation is not None:
            return self._camera_translation
        else:
            return numpy.zeros(2)

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
        glColor3f(*self._parent.color_scheme["output"])
        self._draw_vertices(vertices)

    def _draw_vertices(self, vertices):
        edges = self.bvh_reader.vertices_to_edges(vertices)
        glLineWidth(3.0)
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
        root_vertex = output[0]
        return numpy.array([root_vertex[0], root_vertex[2]])

    def draw_floor(self):
        if self._focus is not None:
            self._draw_floor_spots(
                center_x=self._focus[0],
                center_z=self._focus[1],
                spot_radius=30, grid_size=5)

    def _draw_floor_spots(self, center_x, center_z, spot_radius, grid_size):
        cell_size = spot_radius * 2
        center_nx = int(center_x / cell_size)
        center_nz = int(center_z / cell_size)
        for nx in range(grid_size):
            x = (center_nx + nx - float(grid_size)/2 + 0.5) * cell_size
            if nx % 2 == 0:
                offset_z = 0
            else:
                offset_z = spot_radius
            for nz in range(grid_size):
                z = offset_z + (center_nz + nz - float(grid_size)/2 + 0.5) * cell_size
                self._draw_floor_spot(
                    radius=spot_radius,
                    color=self._parent.color_scheme["floor"],
                    x=x, z=z)

    def _draw_floor_spot(self, radius, color,
                         x, z, y=0, resolution=15):
        color_r, color_g, color_b, color_a = color

        angle_increment = (float) (2 * math.pi / resolution);
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(*color)
        glVertex3f(x, y, z)
        glColor4f(color_r, color_g, color_b, 0)
        for i in range(resolution):
            angle1 = angle_increment * i
            angle2 = angle_increment * (i+1)
            glVertex3f(x + math.cos(angle1) * radius, y, z + math.sin(angle1) * radius)
            glVertex3f(x + math.cos(angle2) * radius, y, z + math.sin(angle2) * radius)
        glEnd()
