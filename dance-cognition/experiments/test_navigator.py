import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui, QtOpenGL
import numpy
from navigator import Navigator, PathFollower
from sklearn.datasets import make_classification
from stopwatch import Stopwatch
from argparse import ArgumentParser
import cPickle

FRAME_RATE = 50
SLIDER_PRECISION = 1000

class MapView(QtOpenGL.QGLWidget):
    def __init__(self, parent, experiment):
        QtOpenGL.QGLWidget.__init__(self, parent)
        self._experiment = experiment

    def render(self):
        self._render_map()
        self._render_path_segments()
        self._render_path()
        for path_follower in self._experiment.path_followers:
            self._render_path_follower_position(path_follower)

    def _render_map(self):
        glColor3f(0, 1, 0)
        glPointSize(1.0)
        glBegin(GL_POINTS)
        for x,y in self._experiment.map_points:
            glVertex2f(*self._vertex(x, y))
        glEnd()

    def _vertex(self, x, y):
        return x*self.width, y*self.height
        
    def _render_path_segments(self):
        glColor3f(0.5, 0.5, 1.0)

        departure_x, departure_y = self._experiment.path_segments[0]
        destination_x, destination_y = self._experiment.path_segments[-1]
        glLineWidth(1.0)
        glRectf(departure_x*self.width-3,
                departure_y*self.height-3,
                departure_x*self.width+3,
                departure_y*self.height+3)

        glPointSize(6.0)
        glBegin(GL_POINTS)
        glVertex2f(*self._vertex(destination_x, destination_y))
        glEnd()

        glPointSize(3.0)
        glBegin(GL_POINTS)
        for x,y in self._experiment.path_segments[1:-1]:
            glVertex2f(*self._vertex(x, y))
        glEnd()

    def _render_path(self):
        glLineWidth(1.0)
        glColor3f(0.5, 0.5, 1.0)
        glBegin(GL_LINE_STRIP)
        for x,y in self._experiment.path:
            glVertex2f(*self._vertex(x, y))
        glEnd()

    def _render_path_follower_position(self, path_follower):
        glColor3f(1, 0, 0)
        glPointSize(3.0)
        glBegin(GL_POINTS)
        glVertex2f(*self._vertex(*path_follower.current_position()))
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
    def __init__(self, experiment):
        QtGui.QMainWindow.__init__(self)
        experiment.window = self
        self._experiment = experiment
        self._central_widget = QtGui.QWidget()
        self._layout = QtGui.QVBoxLayout()
        self._central_widget.setLayout(self._layout)
        self.setCentralWidget(self._central_widget)
        self._add_novelty_slider()
        self._add_map_view()
        self._create_menu()
        self._generate_map_and_path()

        self.stopwatch = Stopwatch()
        self._frame_count = 0
        timer = QtCore.QTimer(self)
        timer.setInterval(1000. / FRAME_RATE)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), self._update)
        timer.start()

    def _add_map_view(self):
        self._map_view = MapView(self, experiment)
        self._layout.addWidget(self._map_view)

    def _add_novelty_slider(self):
        self.novelty_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.novelty_slider.setRange(0, SLIDER_PRECISION)
        self.novelty_slider.setSingleStep(1)
        self.novelty_slider.setValue(0.0)
        self._layout.addWidget(self.novelty_slider)

    def _create_menu(self):
        self._menu = self.menuBar().addMenu("Navigator test")
        self._add_generate_new_path_action()
        self._add_extend_path_action()
        self._add_generate_map_action()

    def _add_generate_new_path_action(self):
        action = QtGui.QAction('Generate new &path', self)
        action.setShortcut('Ctrl+P')
        action.triggered.connect(self._experiment.generate_new_path)
        self._menu.addAction(action)

    def _add_extend_path_action(self):
        action = QtGui.QAction('&Extend path', self)
        action.setShortcut('Ctrl+E')
        action.triggered.connect(self._experiment.extend_path)
        self._menu.addAction(action)

    def _add_generate_map_action(self):
        action = QtGui.QAction('Generate &map', self)
        action.setShortcut('Ctrl+M')
        action.triggered.connect(self._generate_map_and_path)
        self._menu.addAction(action)

    def _generate_map_and_path(self):
        self._experiment.generate_map()
        self._experiment.create_navigator()
        self._experiment.generate_new_path()

    def _update(self):
        self.now = self.stopwatch.get_elapsed_time()
        if self._frame_count == 0:
            self.stopwatch.start()
        else:
            time_increment = self.now - self.previous_frame_time
            self._experiment.proceed(time_increment)
            self._map_view.updateGL()
        self.previous_frame_time = self.now
        self._frame_count += 1

class Experiment:
    def __init__(self, args):
        self._args = args

    def generate_map(self):
        if self._args.model:
            self.map_points = self._load_map_points_from_model()
        else:
            self.map_points = self._generate_random_map_points()

    def _load_map_points_from_model(self):
        f = open(self._args.model)
        model = cPickle.load(f)
        f.close()
        return self._normalize(model.observed_reductions)

    def _generate_random_map_points(self):
        samples, _labels = make_classification(
            n_features=2, n_redundant=0, n_informative=1,
            n_clusters_per_class=1, n_samples=1000)
        return self._normalize(samples)

    def _normalize(self, points):
        min_value = min([min(point) for point in points])
        max_value = max([max(point) for point in points])
        return (points - min_value) / (max_value - min_value)

    def create_navigator(self):
        self._navigator = Navigator(map_points=self.map_points)

    def generate_new_path(self):
        departure = self._select_destination()
        destination = self._select_destination()
        self._generate_path(departure, destination)

    def extend_path(self):
        departure = self.path[-1]
        destination = self._select_destination()
        self._generate_path(departure, destination)

    def _select_destination(self):
        novelty = float(self.window.novelty_slider.value()) / SLIDER_PRECISION
        return self._navigator.select_destination(
            desired_distance_to_nearest_map_point=novelty)

    def _generate_path(self, departure, destination):
        self.path_segments = self._navigator.generate_path(
            departure=departure,
            destination=destination,
            num_segments=10)
        self.path = self._navigator.interpolate_path(
            self.path_segments,
            resolution=100)
        self.path_followers = [
            PathFollower(self.path, velocity=0.1, envelope="constant"),
            PathFollower(self.path, velocity=0.1, envelope="sine"),
            ]

    def proceed(self, time_increment):
        for path_follower in self.path_followers:
            path_follower.proceed(time_increment)

parser = ArgumentParser()
parser.add_argument("-model")
args = parser.parse_args()

experiment = Experiment(args)
app = QtGui.QApplication(sys.argv)
window = MainWindow(experiment)
window.show()
app.exec_()
