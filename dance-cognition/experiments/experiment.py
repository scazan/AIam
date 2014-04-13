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
from storage import *
from bvh_reader import bvh_reader as bvh_reader_module
from stopwatch import Stopwatch
import imp

SLIDER_PRECISION = 1000

class BaseEntity:
    @staticmethod
    def add_parser_arguments(parser):
        pass

    def __init__(self, experiment):
        self._t = 0
        self.experiment = experiment
        self.bvh_reader = experiment.bvh_reader
        self.args = experiment.args
        self.model = None

    def adapt_value_to_model(self, value):
        return value

    def proceed(self, time_increment):
        self._t += time_increment

class BaseScene(QtOpenGL.QGLWidget):
    @staticmethod
    def add_parser_arguments(parser):
        pass

    def __init__(self, parent, experiment, args):
        self.experiment = experiment
        self.bvh_reader = experiment.bvh_reader
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
        glEnable(GL_LINE_SMOOTH)
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

    def sizeHint(self):
        return QtCore.QSize(600, 640)

    def centralize_output(self):
        pass


class ExperimentToolbar(QtGui.QWidget):
    def __init__(self, parent, experiment, args):
        self.experiment = experiment
        self.args = args
        QtOpenGL.QGLWidget.__init__(self, parent)

    def refresh(self):
        pass

    def add_parameter_fields(self, parameters, parent):
        layout = QtGui.QFormLayout()
        for parameter in parameters:
            field = self._create_parameter_field(parameter)
            layout.addRow(QtGui.QLabel(parameter.name), field)
        parent.addLayout(layout)

    def _create_parameter_field(self, parameter):
        if parameter.choices is not None:
            if parameter.choices.__class__ is ParameterFloatRange:
                return self._create_slider_field(parameter)
            else:
                return self._create_list_choice_field(parameter)
        elif parameter.type == str:
            field = QtGui.QLineEdit(parameter.default)
        elif parameter.type in [int, float]:
            field = QtGui.QLineEdit(str(parameter.default))
            field.textEdited.connect(lambda value: self._edited_text_parameter(parameter, value))
        else:
            raise Exception("don't know how to create field for %s" % parameter)
        return field

    def _create_list_choice_field(self, parameter):
        index = 0
        default_index = 0
        field = QtGui.QComboBox()
        for value in parameter.choices:
            field.addItem(value)
            if parameter.default == value:
                default_index = index
            index += 1
            field.setCurrentIndex(default_index)
        field.currentIndexChanged.connect(
            lambda value: self._edited_choice_parameter(parameter, value))
        return field

    def _create_slider_field(self, parameter):
        field = QtGui.QSlider(QtCore.Qt.Horizontal)
        field.setRange(0, SLIDER_PRECISION)
        field.setSingleStep(1)
        field.setValue(self._parameter_value_to_slider_value(parameter))
        field.valueChanged.connect(lambda value: self._slider_value_changed(parameter, value))
        return field

    def _parameter_value_to_slider_value(self, parameter):
        return int((parameter.value() - parameter.choices.min_value) / \
            parameter.choices.range * SLIDER_PRECISION)

    def _slider_value_to_parameter_value(self, parameter, slider_value):
        return float(slider_value) / SLIDER_PRECISION * parameter.choices.range + \
            parameter.choices.min_value
        
    def _slider_value_changed(self, parameter, slider_value):
        value = self._slider_value_to_parameter_value(parameter, slider_value)
        parameter.setValue(value)

    def _edited_text_parameter(self, parameter, string):
        if string == "":
            return
        if parameter.type == int:
            parameter.setValue(int(string))
        elif parameter.type == float:
            parameter.setValue(float(string))

    def _edited_choice_parameter(self, parameter, index):
        parameter.setValue(parameter.choices[index])

class MainWindow(QtGui.QWidget):
    def __init__(self, experiment, scene_widget_class, toolbar_class, args):
        self.experiment = experiment
        self.args = args
        QtGui.QWidget.__init__(self)
        self._layout = QtGui.QHBoxLayout()
        self._scene = scene_widget_class(self, experiment, args)
        self._create_menu()
        self._layout.addWidget(self._scene)

        self.toolbar = toolbar_class(self, experiment, args)
        self.toolbar.setFixedSize(400, 640)
        self._layout.addWidget(self.toolbar)

        self.setLayout(self._layout)

        self.experiment.time_increment = 0
        self.stopwatch = Stopwatch()
        self._frame_count = 0

        timer = QtCore.QTimer(self)
        timer.setInterval(1000. / args.frame_rate)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), self._update)
        timer.start()

    def _create_menu(self):
        menu_bar = QtGui.QMenuBar()
        self._layout.setMenuBar(menu_bar)
        self._menu = menu_bar.addMenu("Main")
        self._add_centralize_action()

    def _add_centralize_action(self):
        action = QtGui.QAction('&Centralize output', self)
        action.setShortcut('Ctrl+R')
        action.triggered.connect(self._scene.centralize_output)
        self._menu.addAction(action)

    def _update(self):
        self.now = self.current_time()
        if self._frame_count == 0:
            self.stopwatch.start()
        else:
            self.experiment.time_increment = self.now - self.previous_frame_time
            self.experiment.proceed()

            self._scene.updateGL()
            self.toolbar.refresh()

        self.previous_frame_time = self.now
        self._frame_count += 1

    def current_time(self):
        return self.stopwatch.get_elapsed_time()


class Experiment:
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("-profile", "-p")
        parser.add_argument("-entity", type=str)
        parser.add_argument("-train", action="store_true")
        parser.add_argument("-training-duration", type=float)
        parser.add_argument("-training-data-frame-rate", type=int, default=50)
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
        if args.profile:
            profile_path = "%s/%s.profile" % (self.profiles_dir, args.profile)
            profile_args_string = open(profile_path).read()
            profile_args_strings = profile_args_string.split()
            args, _remaining_args = parser.parse_known_args(profile_args_strings, namespace=args)
            self._model_path = "%s/%s.model" % (self.profiles_dir, args.profile)
            self._training_data_path = "%s/%s.data" % (self.profiles_dir, args.profile)

        entity_module = imp.load_source("entity", "entities/%s.py" % args.entity)
        if hasattr(entity_module, "Entity"):
            entity_class = entity_module.Entity
        else:
            entity_class = BaseEntity
        entity_class.add_parser_arguments(parser)
        entity_module.Scene.add_parser_arguments(parser)

        args = parser.parse_args()
        if args.profile:
            args = parser.parse_args(profile_args_strings, namespace=args)

        self.args = args
        if args.bvh:
            self.bvh_reader = bvh_reader_module.BvhReader(args.bvh)
            self.bvh_reader.read()
        else:
            self.bvh_reader = None
        self.input = None
        self.output = None
        self.entity = entity_class(self)
        self._scene_class = entity_module.Scene

    def _training_duration(self):
        if self.args.training_duration:
            return self.args.training_duration
        elif hasattr(self.entity, "get_duration"):
            return self.entity.get_duration()
        else:
            raise Exception(
                "training duration specified in neither arguments nor the %s class" % \
                    self.entity.__class__.__name__)

class CameraMovement:
    def __init__(self, source, target, duration=0.25):
        self._source = source
        self._target = target
        self._duration = duration
        self._t = 0
    
    def proceed(self, time_increment):
        self._t += time_increment

    def is_active(self):
        return self._t < self._duration

    def translation(self):
        return self._source + (self._target - self._source) * \
            self._envelope(self._t / self._duration)

    def _envelope(self, relative_t):
        return (math.sin((relative_t / 2 + .75) * math.pi*2) + 1) / 2


class Parameter:
    def __init__(self, name, type=str, default=None, choices=None):
        self.name = name
        self.type = type
        self.default = default
        self.choices = choices
        self._value = default

    def value(self):
        return self._value

    def setValue(self, value):
        self._value = value

    def __repr__(self):
        return "Parameter(name=%s, type=%s, default=%s, choices=%s)" % (
            self.name, self.type, self.default, self.choices)

class Parameters:
    def __init__(self):
        self._parameters = []
        self._parameters_by_name = {}

    def add_parameter(self, *args, **kwargs):
        parameter = Parameter(*args, **kwargs)
        self._parameters.append(parameter)
        self._parameters_by_name[parameter.name] = parameter

    def __getattr__(self, name):
        if name in self._parameters_by_name:
            return self._parameters_by_name[name].value()
        else:
            raise AttributeError()

    def __iter__(self):
        return self._parameters.__iter__()

class ParameterFloatRange:
    def __init__(self, min_value, max_value):
        self.min_value = min_value
        self.max_value = max_value
        self.range = max_value - min_value
