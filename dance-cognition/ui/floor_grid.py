from OpenGL.GL import *
import math

class FloorGrid:
    def __init__(self, num_cells, size, floor_color, background_color, y=0):
        self._num_cells = num_cells
        self._size = size
        self._floor_color = floor_color
        self._background_color = background_color
        self._y = y
        self._cell_size = self._size / self._num_cells
        self._hypotenuse = math.sqrt(self._cell_size * self._cell_size * 2)

    def render(self, center_x, center_z, camera_x, camera_z):
        self._draw_grid(center_x, center_z)
        self._draw_shader(-camera_x, -camera_z)

    def _draw_grid(self, center_x, center_z):
        z1 = - self._size/2
        z2 = + self._size/2
        x1 = - self._size/2
        x2 = + self._size/2

        glColor4f(*self._floor_color)
        glLineWidth(1.4)

        quantified_center_x = int(center_x / self._hypotenuse) * self._hypotenuse
        quantified_center_z = int(center_z / self._hypotenuse) * self._hypotenuse
        glPushMatrix()
        glTranslatef(quantified_center_x, 0, quantified_center_z)
        glRotatef(45, 0, 1, 0)

        for n in range(self._num_cells):
            glBegin(GL_LINES)
            x = x1 + float(n) * self._cell_size
            glVertex3f(x, self._y, z1)
            glVertex3f(x, self._y, z2)
            glEnd()

        for n in range(self._num_cells):
            glBegin(GL_LINES)
            z = z1 + float(n) * self._cell_size
            glVertex3f(x1, self._y, z)
            glVertex3f(x2, self._y, z)
            glEnd()

        glPopMatrix()

    def _draw_shader(self, x, z, y=0, resolution=15):
        radius = math.sqrt(self._size * self._size * 2)
        bg_r, bg_g, bg_b, bg_a = self._background_color
        angle_increment = 2 * math.pi / resolution
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
