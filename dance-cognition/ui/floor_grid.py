from OpenGL.GL import *

class FloorGrid:
    def __init__(self, num_cells, size, floor_color, background_color, y=0):
        self._num_cells = num_cells
        self._size = size
        self._floor_color = floor_color
        self._background_color = background_color
        self._y = y

    def render(self, center_x, center_z, camera_x, camera_z):
        z1 = -self._size/2
        z2 = self._size/2
        x1 = -self._size/2
        x2 = self._size/2
        color_r, color_g, color_b, color_a = self._floor_color

        glLineWidth(1.4)

        glPushMatrix()
        glRotatef(45, 0, 1, 0)

        for n in range(self._num_cells):
            glBegin(GL_LINES)
            x = x1 + float(n) / self._num_cells * self._size
            color_a1 = color_a * (1 - abs(x - camera_x) / self._size)

            glColor4f(color_r, color_g, color_b, 0)
            glVertex3f(x, self._y, z1)
            glColor4f(color_r, color_g, color_b, color_a1)
            glVertex3f(x, self._y, camera_z)

            glColor4f(color_r, color_g, color_b, color_a1)
            glVertex3f(x, self._y, camera_z)
            glColor4f(color_r, color_g, color_b, 0)
            glVertex3f(x, self._y, z2)
            glEnd()

        for n in range(self._num_cells):
            glBegin(GL_LINES)
            z = z1 + float(n) / self._num_cells * self._size
            color_a1 = color_a * (1 - abs(z - camera_z) / self._size)

            glColor4f(color_r, color_g, color_b, 0)
            glVertex3f(x1, self._y, z)
            glColor4f(color_r, color_g, color_b, color_a1)
            glVertex3f(camera_x, self._y, z)

            glColor4f(color_r, color_g, color_b, color_a1)
            glVertex3f(camera_x, self._y, z)
            glColor4f(color_r, color_g, color_b, 0)
            glVertex3f(x2, self._y, z)
            glEnd()

        glPopMatrix()

