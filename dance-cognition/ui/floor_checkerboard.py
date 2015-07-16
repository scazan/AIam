from OpenGL.GL import *
import math
from shader import Shader

class FloorCheckerboard:
    def __init__(self, num_cells, size, floor_color, background_color,
                 board_color1, board_color2, y=0):
        self._num_cells = num_cells
        self._size = size
        self._floor_color = floor_color
        self._board_color1 = board_color1
        self._board_color2 = board_color2
        self._y = y
        self._cell_size = self._size / self._num_cells
        self._hypotenuse = math.sqrt(self._cell_size * self._cell_size * 2)
        self._shader = Shader(
            radius = math.sqrt(self._size * self._size * 2),
            background_color = background_color)
        self._grid_display_list_id = None

    def render(self, center_x, center_z, camera_x, camera_z):
        self._draw_grid(center_x, center_z)
        self._shader.render(-camera_x, 0, -camera_z)

    def _draw_grid(self, center_x, center_z):
        quantified_center_x = int(center_x / self._hypotenuse) * self._hypotenuse
        quantified_center_z = int(center_z / self._hypotenuse) * self._hypotenuse
        glPushMatrix()
        glTranslatef(quantified_center_x, 0, quantified_center_z)
        glRotatef(45, 0, 1, 0)

        if self._grid_display_list_id is None:
            self._grid_display_list_id = self._create_grid_display_list()
        glCallList(self._grid_display_list_id)

        glPopMatrix()

    def _create_grid_display_list(self):
        display_list_id = glGenLists(1)
        glEnable(GL_POLYGON_SMOOTH)
        glNewList(display_list_id, GL_COMPILE)

        # n = 0
        # for nx in range(self._num_cells - 1):
        #     x1 = -self._size/2 + float(nx)   * self._cell_size
        #     x2 = -self._size/2 + float(nx+1) * self._cell_size
        #     for nz in range(self._num_cells - 1):
        #         z1 = -self._size/2 + float(nz)   * self._cell_size
        #         z2 = -self._size/2 + float(nz+1) * self._cell_size
        #         if(n % 2 == 0):
        #             glColor3f(*self._board_color1)
        #         else:
        #             glColor3f(*self._board_color2)
        #         glBegin(GL_QUADS)
        #         glVertex3f(x1, self._y, z1)
        #         glVertex3f(x2, self._y, z1)
        #         glVertex3f(x2, self._y, z2)
        #         glVertex3f(x1, self._y, z2)
        #         glVertex3f(x1, self._y, z1)
        #         glEnd()
        #         n += 1

        glColor4f(*self._board_color1)
        z1 = - self._size/2
        z2 = + self._size/2
        x1 = - self._size/2
        x2 = + self._size/2
        glBegin(GL_QUADS)
        glVertex3f(x1, self._y, z1)
        glVertex3f(x2, self._y, z1)
        glVertex3f(x2, self._y, z2)
        glVertex3f(x1, self._y, z2)
        glVertex3f(x1, self._y, z1)
        glEnd()
        
        glColor4f(*self._board_color2)
        n = 0
        for nx in range(self._num_cells - 1):
            x1 = -self._size/2 + float(nx)   * self._cell_size
            x2 = -self._size/2 + float(nx+1) * self._cell_size
            for nz in range(self._num_cells - 1):
                if(n % 2 == 1):
                    z1 = -self._size/2 + float(nz)   * self._cell_size
                    z2 = -self._size/2 + float(nz+1) * self._cell_size
                    glBegin(GL_QUADS)
                    glVertex3f(x1, self._y, z1)
                    glVertex3f(x2, self._y, z1)
                    glVertex3f(x2, self._y, z2)
                    glVertex3f(x1, self._y, z2)
                    glVertex3f(x1, self._y, z1)
                    glEnd()
                n += 1

        glEndList()
        return display_list_id
