import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from argparse import ArgumentParser
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui, QtOpenGL
import math
import numpy
from learning_plotter import LearningPlotter
from bvh_reader import bvh_reader as bvh_reader_module
import pickle
from stopwatch import Stopwatch
import imp

class BaseEntity:
    @staticmethod
    def add_parser_arguments(parser):
        pass

    def __init__(self, args):
        pass

class BaseStimulus:
    def __init__(self, experiment):
        self._t = 0
        self.args = experiment.args
        self.bvh_reader = experiment.bvh_reader
        self.entity = experiment.entity

    def proceed(self, time_increment):
        self._t += time_increment

class BaseScene(QtOpenGL.QGLWidget):
    def __init__(self, parent, experiment, args):
        self.experiment = experiment
        self.bvh_reader = experiment.bvh_reader
        self.entity = experiment.entity
        self.args = args
        QtOpenGL.QGLWidget.__init__(self, parent)

    def render(self):
        self.configure_3d_projection(-100, 0)
        glScale(self.args.zoom, self.args.zoom, self.args.zoom)
        self._draw_io(self.experiment.input, self.draw_input, self.args.input_y_offset)
        self._draw_io(self.experiment.output, self.draw_output, self.args.output_y_offset)

    def _draw_io(self, value, rendering_method, y_offset):
        glPushMatrix()
        glTranslatef(0, y_offset, 0)
        if self.args.unit_cube:
            self._draw_unit_cube()
        if value is not None:
            rendering_method(value)
        glPopMatrix()

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 0.0)
        glClearAccum(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glShadeModel(GL_SMOOTH)
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
        self._aspect_ratio = float(window_width) / window_height
        self.min_dimension = min(self.width, self.height)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(self.margin, self.margin, 0)
        self.render()

    def _draw_unit_cube(self):
        glLineWidth(1.0)
        glColor4f(0,0,0,0.2)
        glutWireCube(2.0)

    def configure_3d_projection(self, pixdx=0, pixdy=0):
        self.fovy = 45
        self.near = 0.1
        self.far = 100.0

        fov2 = ((self.fovy*math.pi) / 180.0) / 2.0
        top = self.near * math.tan(fov2)
        bottom = -top
        right = top * self._aspect_ratio
        left = -right
        xwsize = right - left
        ywsize = top - bottom
        dx = -(pixdx*xwsize/self.width)
        dy = -(pixdy*ywsize/self.height)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glFrustum (left + dx, right + dx, bottom + dy, top + dy, self.near, self.far)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        CAMERA_POSITION = [-8, -0.5, -1.35]
        CAMERA_Y_ORIENTATION = -88
        CAMERA_X_ORIENTATION = 9
        glRotatef(CAMERA_X_ORIENTATION, 1.0, 0.0, 0.0)
        glRotatef(CAMERA_Y_ORIENTATION, 0.0, 1.0, 0.0)
        glTranslatef(*CAMERA_POSITION)


class ExperimentToolbar(QtGui.QWidget):
    def __init__(self, parent, experiment, args):
        self.experiment = experiment
        self.args = args
        QtOpenGL.QGLWidget.__init__(self, parent)

    def refresh(self):
        pass

class MainWindow(QtGui.QWidget):
    def __init__(self, experiment, scene_widget_class, toolbar_class, args):
        self.experiment = experiment
        self.args = args
        QtGui.QWidget.__init__(self)
        layout = QtGui.QHBoxLayout()
        size_policy = QtGui.QSizePolicy(
            QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(2)

        self._scene = scene_widget_class(self, experiment, args)
        self._scene.setSizePolicy(size_policy)
        layout.addWidget(self._scene)

        self.toolbar = toolbar_class(self, experiment, args)
        self.toolbar.setSizePolicy(size_policy)
        layout.addWidget(self.toolbar)

        self.setLayout(layout)

        self.time_increment = 0
        self.stopwatch = Stopwatch()
        self._frame_count = 0

        timer = QtCore.QTimer(self)
        timer.setInterval(1000. / args.frame_rate)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), self._update)
        timer.start()

    def sizeHint(self):
        return QtCore.QSize(800, 640)

    def _update(self):
        self.now = self.current_time()
        if self._frame_count == 0:
            self.stopwatch.start()
        else:
            self.time_increment = self.now - self.previous_frame_time
            self.experiment.proceed(self.time_increment)

            self._scene.updateGL()
            self.toolbar.refresh()

        self.previous_frame_time = self.now
        self._frame_count += 1

    def current_time(self):
        return self.stopwatch.get_elapsed_time()


class Experiment:
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("entity", type=str)
        parser.add_argument("-stimulus", default="Stimulus")
        parser.add_argument("-train", action="store_true")
        parser.add_argument("-training-duration", type=float)
        parser.add_argument("-training-data-frame-rate", type=int, default=50)
        parser.add_argument("-model", type=str)
        parser.add_argument("-bvh", type=str)
        parser.add_argument("-bvh-speed", type=float, default=1.0)
        parser.add_argument("-joint")
        parser.add_argument("-frame-rate", type=float, default=50.0)
        parser.add_argument("-unit-cube", action="store_true")
        parser.add_argument("-zoom", type=float, default=1.0)
        parser.add_argument("-input-y-offset", type=float, default=.0)
        parser.add_argument("-output-y-offset", type=float, default=.0)

    def __init__(self, parser):
        args, _remaining_args = parser.parse_known_args()
        entity_module = imp.load_source("entity", "entities/%s.py" % args.entity)
        if hasattr(entity_module, "Entity"):
            entity_class = entity_module.Entity
        else:
            entity_class = BaseEntity
        entity_class.add_parser_arguments(parser)

        args = parser.parse_args()
        self.args = args
        if args.bvh:
            self.bvh_reader = bvh_reader_module.BvhReader(args.bvh)
            self.bvh_reader.read()
        else:
            self.bvh_reader = None
        self.input = None
        self.output = None
        self.entity = entity_class(args)
        self._scene_class = entity_module.Scene
        stimulus_class = getattr(entity_module, args.stimulus)
        self.stimulus = stimulus_class(self)

    def save_model(self, model_filename):
        print "saving model..."
        f = open(model_filename, "w")
        pickle.dump(self.student, f)
        f.close()
        print "ok"
        
    def load_model(self, model_filename):
        print "loading model..."
        f = open(model_filename)
        model = pickle.load(f)
        f.close()
        print "ok"
        return model

    def _training_duration(self):
        if self.args.training_duration:
            return self.args.training_duration
        elif hasattr(self.stimulus, "get_duration"):
            return self.stimulus.get_duration()
        else:
            raise Exception(
                "training duration specified in neither arguments nor the %s class" % \
                    self.stimulus.__class__.__name__)
