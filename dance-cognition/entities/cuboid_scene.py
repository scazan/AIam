from ui.ui import *

class CuboidScene(BaseScene):
    def initializeGL(self):
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.3, 0.4, 0.5))
        glLightfv(GL_LIGHT1, GL_AMBIENT, (0.2, 0.4, 1.0, 0.8))
        glLightfv(GL_LIGHT0, GL_POSITION, (1.0, 3.0, 8.0, 1.0))
        glLightfv(GL_LIGHT1, GL_POSITION, (5.0, 3.0, 0.0, 1.0))

        glEnable(GL_CULL_FACE)
        glCullFace(GL_FRONT)

        BaseScene.initializeGL(self)

    def draw_cuboid_shape(self):
        self._draw_cuboid(
            0, 0, 0.1,
            .3, .5, .3)
        self._draw_cuboid(
            0, 0.65, 0,
            .3, .1, .4)

    def _draw_cuboid(self, x, y, z, sx, sy, sz):
        glPushMatrix()
        glTranslatef(x, y, z)
        glScale(sx, sy, sz)

        glBegin(GL_QUADS)
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, (1.0, 0.3, 0.4, 0.5))

        vertex = [
            ( -1.0, -1.0, -1.0 ),
            ( 1.0, -1.0, -1.0 ),
            ( 1.0, 1.0, -1.0 ),
            ( -1.0, 1.0, -1.0 ),
            ( -1.0, -1.0, 1.0 ),
            ( 1.0, -1.0, 1.0 ),
            ( 1.0, 1.0, 1.0 ),
            ( -1.0, 1.0, 1.0 )
            ]
        edge = [
            ( 0, 1 ),
            ( 1, 2 ),
            ( 2, 3 ),
            ( 3, 0 ),
            ( 4, 5 ),
            ( 5, 6 ),
            ( 6, 7 ),
            ( 7, 4 ),
            ( 0, 4 ),
            ( 1, 5 ),
            ( 2, 6 ),
            ( 3, 7 )
            ]
        face = [
            ( 0, 1, 2, 3 ),
            ( 1, 5, 6, 2 ),
            ( 5, 4, 7, 6 ),
            ( 4, 0, 3, 7 ),
            ( 4, 5, 1, 0 ),
            ( 3, 2, 6, 7 )
            ]
        normal = [
            ( 0.0, 0.0,-1.0 ),
            ( 1.0, 0.0, 0.0 ),
            ( 0.0, 0.0, 1.0 ),
            (-1.0, 0.0, 0.0 ),
            ( 0.0,-1.0, 0.0 ),
            ( 0.0, 1.0, 0.0 )
            ]
        for j in range(6):
            glNormal3dv(normal[j]);
            for i in range(4):
                glVertex3dv(vertex[face[j][i]]);

        glEnd()
        glPopMatrix()
