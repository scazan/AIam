import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui, QtOpenGL
import numpy
from flaneur import Flaneur
import storage
from sklearn.datasets import make_classification
from stopwatch import Stopwatch
from argparse import ArgumentParser
import random
import math

FRAME_RATE = 50
SLIDER_PRECISION = 1000
PARAMETERS = [
    "translational_speed",
    "directional_speed",
    "look_ahead_distance",
    ]

class MapView(QtOpenGL.QGLWidget):
    def __init__(self, parent, experiment):
        QtOpenGL.QGLWidget.__init__(self, parent)
        self._experiment = experiment

    def render(self):
        self._render_map()
        self._render_neighbors()
        self._render_neighbors_center()
        self._render_flaneur_position()

    def _render_map(self):
        glColor3f(.8, .8, .8)
        glPointSize(1.0)
        glBegin(GL_POINTS)
        for x,y in self._experiment.map_points:
            glVertex2f(*self._vertex(x, y))
        glEnd()

    def _vertex(self, x, y):
        return x*self.width, y*self.height

    def _render_neighbors(self):
        if self.parent().weight_function_action.isChecked():
            self._render_neighbors_colored_by_weights()
        else:
            self._render_neighbors_with_color(self._color_by_weight(1))

    def _render_neighbors_colored_by_weights(self):
        glPointSize(2.0)
        glBegin(GL_POINTS)
        for weight, point in zip(self._experiment.flaneur.get_weights(),
                                 self._experiment.flaneur.get_neighbors()):
            glColor4f(*self._color_by_weight(weight))
            glVertex2f(*self._vertex(*point))
        glEnd()

    def _color_by_weight(self, weight):
        return (.3, 0, 0, weight)

    def _render_neighbors_with_color(self, rgba):
        glColor4f(*rgba)
        glPointSize(1.0)
        glBegin(GL_POINTS)
        for x, y in self._experiment.flaneur.get_neighbors():
            glVertex2f(*self._vertex(x, y))
        glEnd()

    def _render_neighbors_center(self):
        if self._experiment.flaneur.get_neighbors_center() is not None:
            glColor3f(.8, .2, .2)
            glPointSize(3.0)
            glBegin(GL_POINTS)
            glVertex2f(*self._vertex(*self._experiment.flaneur.get_neighbors_center()))
            glEnd()

    def _render_flaneur_position(self):
        glColor3f(1, 0, 0)
        glPointSize(4.0)
        glBegin(GL_POINTS)
        glVertex2f(*self._vertex(*self._experiment.flaneur.get_position()))
        glEnd()

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 0.0)
        glClearAccum(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
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

class MainWindow(QtGui.QWidget):
    def __init__(self, experiment):
        QtGui.QMainWindow.__init__(self)
        experiment.window = self
        self._experiment = experiment
        self._layout = QtGui.QVBoxLayout()
        self.setLayout(self._layout)
        self._add_parameter_form()
        self._add_map_view()
        self._create_menu()

        self.stopwatch = Stopwatch()
        self._frame_count = 0
        timer = QtCore.QTimer(self)
        timer.setInterval(1000. / FRAME_RATE)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), self._update)
        timer.start()

    def _add_map_view(self):
        self._map_view = MapView(self, experiment)
        self._layout.addWidget(self._map_view)

    def _add_parameter_form(self):
        self._parameter_sliders = {}
        layout = QtGui.QFormLayout()
        for parameter_name in PARAMETERS:
            default_value = getattr(args, parameter_name)
            self._add_slider(layout, parameter_name, default_value)
        self._layout.addLayout(layout)

    def _add_slider(self, layout, name, default_value):
        slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, SLIDER_PRECISION)
        slider.setSingleStep(1)
        slider.setValue(int(default_value * SLIDER_PRECISION))
        slider.valueChanged.connect(lambda event: self.update_flaneur_parameter(name))
        layout.addRow(name, slider)
        self._parameter_sliders[name] = slider

    def update_flaneur_parameter(self, parameter_name):
        slider = self._parameter_sliders[parameter_name]
        value = float(slider.value()) / SLIDER_PRECISION
        setattr(self._experiment.flaneur, parameter_name, value)

    def _create_menu(self):
        menu_bar = QtGui.QMenuBar()
        self._layout.setMenuBar(menu_bar)
        self._menu = menu_bar.addMenu("Flaneur test")
        self._add_reset_action()
        self._add_generate_map_action()
        self._addweight_function_action()

    def _add_reset_action(self):
        action = QtGui.QAction('Reset', self)
        action.setShortcut('R')
        action.triggered.connect(self._experiment.reset)
        self._menu.addAction(action)

    def _add_generate_map_action(self):
        action = QtGui.QAction('Generate &map', self)
        action.setShortcut('Ctrl+M')
        action.triggered.connect(self._generate_map)
        self._menu.addAction(action)

    def _addweight_function_action(self):
        self.weight_function_action = QtGui.QAction('Weight function', self)
        self.weight_function_action.setShortcut('w')
        self.weight_function_action.setCheckable(True)
        self.weight_function_action.triggered.connect(self._toggled_weight_function)
        self._menu.addAction(self.weight_function_action)

    def _toggled_weight_function(self):
        if self.weight_function_action.isChecked():
            self._experiment.flaneur.weight_function = self._experiment.weight_function
        else:
            self._experiment.flaneur.weight_function = None
            
    def _generate_map(self):
        self._experiment.generate_map()

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
        self._create_flaneur()

    def _create_flaneur(self):
        self.flaneur = Flaneur(map_points=self.map_points)
        for parameter_name in PARAMETERS:
            window.update_flaneur_parameter(parameter_name)

    def _load_map_points_from_model(self):
        model = storage.load(self._args.model)[0]
        return model.normalized_observed_reductions

    def _generate_random_map_points(self):
        samples, _labels = make_classification(
            n_features=2, n_redundant=0, n_informative=1,
            n_clusters_per_class=1, n_samples=1000)
        return self._normalize(samples)

    def _normalize(self, points):
        min_value = min([min(point) for point in points])
        max_value = max([max(point) for point in points])
        return (points - min_value) / (max_value - min_value)

    def proceed(self, time_increment):
        self.flaneur.proceed(time_increment)

    def reset(self):
        self.flaneur.reset()

    def weight_function(self, point_index):
        point = self.map_points[point_index]
        return self._vicinity_to_center(point)

    def _vicinity_to_center(self, point):
        distance_to_center = numpy.linalg.norm(point - [.5, .5])
        if distance_to_center == 0:
            return 1
        else:
            return max(0, 1 - distance_to_center)

parser = ArgumentParser()
parser.add_argument("-model")
parser.add_argument("--translational-speed", type=float, default=0.2)
parser.add_argument("--directional-speed", type=float, default=0.05)
parser.add_argument("--look-ahead-distance", type=float, default=0.1)
args = parser.parse_args()

experiment = Experiment(args)
app = QtGui.QApplication(sys.argv)
window = MainWindow(experiment)
experiment.generate_map()
window.show()
app.exec_()
