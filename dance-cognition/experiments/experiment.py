import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from argparse import ArgumentParser
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui, QtOpenGL
import math
from teacher import *
from learning_plotter import LearningPlotter
from bvh_reader import bvh_reader as bvh_reader_module
import pickle
from stopwatch import Stopwatch

class Stimulus:
    def __init__(self):
        self._t = 0

    def proceed(self, time_increment):
        self._t += time_increment

class ExperimentScene(QtOpenGL.QGLWidget):
    def __init__(self, parent, experiment, args):
        self.experiment = experiment
        self.bvh_reader = experiment.bvh_reader
        QtOpenGL.QGLWidget.__init__(self, parent)

    def render(self):
        self.configure_3d_projection(-100, 0)
        self._draw_unit_cube()
        if self.experiment.input is not None:
            self.draw_input(self.experiment.input)
        if self.experiment.output is not None:
            self.draw_output(self.experiment.output)

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
        QtOpenGL.QGLWidget.__init__(self, parent)
        layout = QtGui.QVBoxLayout()
        self._sliders = []
        for n in range(self.experiment.student.n_components):
            slider = QtGui.QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setSingleStep(1)
            layout.addWidget(slider)
            self._sliders.append(slider)
        self.setLayout(layout)

    def refresh(self):
        for n in range(self.experiment.student.n_components):
            self._sliders[n].setValue(
                self._reduction_value_to_slider_value(n, self.experiment.reduction[n]))

    def _reduction_value_to_slider_value(self, n, value):
        range_n = self.experiment.student.reduction_range[n]
        return (value - range_n["min"]) / \
            (range_n["max"] - range_n["min"]) * 100

    def _slider_value_to_reduction_value(self, n, value):
        range_n = self.experiment.student.reduction_range[n]
        return float(value) / 100 * (range_n["max"] - range_n["min"]) + \
            range_n["min"]

    def get_reduction(self):
        return numpy.array(
            [self._slider_value_to_reduction_value(n, self._sliders[n].value())
             for n in range(self.experiment.student.n_components)])


class MainWindow(QtGui.QWidget):
    def __init__(self, experiment, scene_widget_class, args):
        self.experiment = experiment
        self.args = args
        QtGui.QWidget.__init__(self)
        self.resize(800, 640)
        layout = QtGui.QHBoxLayout()
        self._scene = scene_widget_class(self, experiment, args)
        self._scene.setFixedSize(400, 640)
        layout.addWidget(self._scene)

        self.toolbar = ExperimentToolbar(self, experiment, args)
        layout.addWidget(self.toolbar)

        self.setLayout(layout)

        self.time_increment = 0
        self.stopwatch = Stopwatch()
        self._frame_count = 0

        timer = QtCore.QTimer(self)
        timer.setInterval(1000. / args.frame_rate)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), self._update)
        timer.start()

    def _update(self):
        self.now = self.current_time()
        if self._frame_count == 0:
            self.stopwatch.start()
        else:
            self.time_increment = self.now - self.previous_frame_time
            self.experiment.proceed(self.time_increment)

            self._scene.updateGL()
            if not self.args.interactive_control:
                self.toolbar.refresh()

        self.previous_frame_time = self.now
        self._frame_count += 1

    def current_time(self):
        return self.stopwatch.get_elapsed_time()

def add_parser_arguments(parser):
    parser.add_argument("-train")
    parser.add_argument("-training-data-frame-rate", type=int, default=50)
    parser.add_argument("-model")
    parser.add_argument("-bvh")
    parser.add_argument("-bvh-speed", type=float, default=1.0)
    parser.add_argument("-plot", type=str)
    parser.add_argument("-plot-duration", type=float, default=10)
    parser.add_argument("-frame-rate", type=float, default=50.0)
    parser.add_argument("-interactive-control", action="store_true")

class Experiment:
    def __init__(self, scene, args):
        self.args = args
        self._scene_class = scene
        if args.bvh:
            self.bvh_reader = bvh_reader_module.BvhReader(args.bvh)
            self.bvh_reader.read()
        else:
            self.bvh_reader = None
        self.input = None
        self.output = None
        self.reduction = None

    def run(self, student, stimulus):
        self.stimulus = stimulus
        self.student = student

        if self.args.train:
            teacher = Teacher(stimulus, self.args.training_data_frame_rate)
            self._train(teacher, self.args.train)

            # if self.args.plot:
            #     LearningPlotter(student, teacher, self.args.plot_duration).plot(self.args.plot)

        elif self.args.model:
            self.student = self._load_model(self.args.model)

            app = QtGui.QApplication(sys.argv)
            self.window = MainWindow(self, self._scene_class, self.args)
            self.window.show()
            app.exec_()

        else:
            raise Exception("a model must either be loaded or trained")

    def _train(self, teacher, model_filename):
        print "training model..."
        self.student.fit(teacher.get_training_data())
        print "explained variance ratio: %s (sum %s)" % (
            self.student.explained_variance_ratio_, sum(self.student.explained_variance_ratio_))
        print "ok"

        print "probing model..."
        self.student.probe(teacher.get_training_data())
        print "ok"

        print "saving model..."
        f = open(model_filename, "w")
        pickle.dump(self.student, f)
        f.close()
        print "ok"
        
    def _load_model(self, model_filename):
        print "loading model..."
        f = open(model_filename)
        model = pickle.load(f)
        f.close()
        print "ok"
        return model

    def proceed(self, time_increment):
        if self.args.interactive_control:
            self.reduction = self.window.toolbar.get_reduction()
        else:
            self.stimulus.proceed(time_increment)
            self.input = self.stimulus.get_value()
            self.reduction = self.student.transform(self.input)
        self.output = self.student.inverse_transform(self.reduction)
