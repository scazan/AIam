import math
from OpenGL.GL import *

RESOLUTION = 15

class Shader:
    def __init__(self, radius, background_color):
        self._radius = radius
        self._background_color = background_color
        self._display_list_id = None

    def render(self, x, y, z):
        if self._display_list_id is None:
            self._display_list_id = self._create_display_list()
        glPushMatrix()
        glTranslatef(x, y, z)
        glCallList(self._display_list_id)
        glPopMatrix()
    
    def _create_display_list(self):
        bg_r, bg_g, bg_b, bg_a = self._background_color
        angle_increment = 2 * math.pi / RESOLUTION
        display_list_id = glGenLists(1)
        glNewList(display_list_id, GL_COMPILE)
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(bg_r, bg_g, bg_b, 0)
        glVertex3f(0, 0, 0)
        glColor4f(bg_r, bg_g, bg_b, 1)
        for i in range(RESOLUTION):
            angle1 = angle_increment * i
            angle2 = angle_increment * (i+1)
            glVertex3f(math.cos(angle1) * self._radius, 0, math.sin(angle1) * self._radius)
            glVertex3f(math.cos(angle2) * self._radius, 0, math.sin(angle2) * self._radius)
        glEnd()
        glEndList()
        return display_list_id
