import sys
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui, QtOpenGL
import numpy
import random
from navigator import Navigator
from sklearn.datasets import make_classification

class MapView(QtOpenGL.QGLWidget):
    def __init__(self, parent):
        QtOpenGL.QGLWidget.__init__(self, parent)

    def render(self):
        self._main_window = self.parent()
        self.render_map()
        self.render_path()

    def render_map(self):
        glColor3f(0, 1, 0)
        glPointSize(3.0)
        glBegin(GL_POINTS)
        for x,y in self._main_window.map_points:
            glVertex2f(x*self.width, y*self.height)
        glEnd()

    def render_path(self):
        glColor3f(0.5, 0.5, 1.0)

        departure_x, departure_y = self._main_window.path[0]
        destination_x, destination_y = self._main_window.path[-1]
        glLineWidth(1.0)
        glRectf(departure_x*self.width-3,
                departure_y*self.height-3,
                departure_x*self.width+3,
                departure_y*self.height+3)

        glPointSize(6.0)
        glBegin(GL_POINTS)
        glVertex2f(destination_x*self.width, destination_y*self.height)
        glEnd()

        glPointSize(3.0)
        glBegin(GL_POINTS)
        for x,y in self._main_window.path[1:-1]:
            glVertex2f(x*self.width, y*self.height)
        glEnd()

        glBegin(GL_LINE_STRIP)
        for x,y in self._main_window.path:
            glVertex2f(x*self.width, y*self.height)
        glEnd()

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 0.0)
        glClearAccum(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glEnable(GL_POINT_SMOOTH)
        glutInit(sys.argv)

    def resizeGL(self, window_width, window_height):
        self.window_width = window_width
        self.window_height = window_height
        if window_height == 0:
            window_height = 1
        glViewport(0, 0, window_width, window_height)
        self.margin = 0
        self.width = window_width - 2*self.margin
        self.height = window_height - 2*self.margin
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, self.window_width, self.window_height, 0.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(self.margin, self.margin, 0)
        self.render()

    def sizeHint(self):
        return QtCore.QSize(500, 500)

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self._map_view = MapView(self)
        self.setCentralWidget(self._map_view)
        self._create_menu()
        self._generate_map_and_path()

    def _create_menu(self):
        self._menu = self.menuBar().addMenu("Navigator test")
        self._add_generate_path_action()
        self._add_generate_map_action()

    def _add_generate_path_action(self):
        action = QtGui.QAction('Generate &path', self)
        action.setShortcut('Ctrl+P')
        action.triggered.connect(self._generate_path)
        self._menu.addAction(action)        

    def _add_generate_map_action(self):
        action = QtGui.QAction('Generate &map', self)
        action.setShortcut('Ctrl+M')
        action.triggered.connect(self._generate_map_and_path)
        self._menu.addAction(action)        

    def _generate_map_and_path(self):
        self._generate_map()
        self._create_navigator()
        self._generate_path()

    def _generate_map(self):
        samples, labels = make_classification(
            n_features=2, n_redundant=0, n_informative=1,
            n_clusters_per_class=1)
        self.map_points = self._normalize(samples)

    def _normalize(self, points):
        min_value = min([min(point) for point in points])
        max_value = max([max(point) for point in points])
        return (points - min_value) / (max_value - min_value)

    def _random_map_position(self):
        return numpy.array([random.uniform(0., 1.),
                            random.uniform(0., 1.)])

    def _create_navigator(self):
        self._navigator = Navigator(map_points=self.map_points)

    def _generate_path(self):
        departure = random.choice(self.map_points)
        destination = self._random_map_position()
        self.path = self._navigator.generate_path(
            departure=departure, destination=destination, resolution=10)
        self._map_view.repaint()

app = QtGui.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
