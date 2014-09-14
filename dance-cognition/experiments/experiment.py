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
from bvh_writer import BvhWriter
from stopwatch import Stopwatch
import imp

TOOLBAR_WIDTH = 400
TOOLBAR_HEIGHT = 720
SLIDER_PRECISION = 1000
CIRCLE_PRECISION = 100
CAMERA_Y_SPEED = .1
CAMERA_KEY_SPEED = .5
CAMERA_DRAG_SPEED = .5
FOCUS_RADIUS = 1.

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

    def process_input(self, value):
        return self.process_io(value)

    def process_output(self, value):
        return self.process_io(value)

    def process_io(self, value):
        return value

    def update(self):
        if self.experiment.input is None:
            self.processed_input = None
        else:
            self.processed_input = self.process_input(self.experiment.input)

        if self.experiment.output is None:
            self.processed_output = None
        else:
            self.processed_output = self.process_output(self.experiment.output)

    def get_cursor(self):
        if hasattr(self, "get_duration"):
            return self._t % self.get_duration()
        else:
            return self._t

    def set_cursor(self, t):
        self._t = t

class BaseScene(QtOpenGL.QGLWidget):
    @staticmethod
    def add_parser_arguments(parser):
        pass

    def __init__(self, parent, experiment, args):
        self._parent = parent
        self.experiment = experiment
        self.bvh_reader = experiment.bvh_reader
        self.args = args
        self._exporting_output = False
        self.view_floor = args.floor
        self._dragging_orientation = False
        self._dragging_y_position = False
        self._focus = None
        self._set_camera_from_arg(args.camera)
        QtOpenGL.QGLWidget.__init__(self, parent)
        self.setMouseTracking(True)

    def _set_camera_from_arg(self, arg):
        pos_x, pos_y, pos_z, orient_y, orient_z = map(float, arg.split(","))
        self._set_camera_position([pos_x, pos_y, pos_z])
        self._set_camera_orientation(orient_y, orient_z)

    def set_default_camera_orientation(self):
        pos_x, pos_y, pos_z, orient_y, orient_z = map(float, self.args.camera.split(","))
        self._set_camera_orientation(orient_y, orient_z)

    def _set_focus(self):
        self._focus = self.central_output_position(self.experiment.entity.processed_output)

    def _output_outside_focus(self):
        if self._focus is not None:
            distance = numpy.linalg.norm(
                self.central_output_position(self.experiment.entity.processed_output) - self._focus)
            return distance > FOCUS_RADIUS

    def _update(self):
        if self.experiment.output is not None:
            if self._focus is None:
                self._set_focus()
            if self._following_output() and self._output_outside_focus():
                self.centralize_output(self.experiment.entity.processed_output)
                self._set_focus()

    def render(self):
        self._update()
        self.configure_3d_projection(-100, 0)
        self._draw_io(self.experiment.entity.processed_input, self.draw_input, self.args.input_y_offset)
        self._draw_io(self.experiment.entity.processed_output, self.draw_output, self.args.output_y_offset)
        if self.view_floor:
            self._draw_floor()
        if self._parent.focus_action.isChecked():
            self._draw_focus()
        if self._exporting_output:
            self._export_output()

    def _draw_io(self, value, rendering_method, y_offset):
        glPushMatrix()
        glTranslatef(0, y_offset, 0)
        if self.args.unit_cube:
            self._draw_unit_cube()
        if value is not None:
            rendering_method(value)
        glPopMatrix()

    def start_export_output(self):
        print "exporting output"
        self._exporting_output = True

    def stop_export_output(self):
        if not os.path.exists(self.experiment.args.export_dir):
            os.mkdir(self.experiment.args.export_dir)
        export_path = self._get_export_path()
        print "saving export to %s" % export_path
        self.experiment.bvh_writer.write(export_path)
        self._exporting_output = False

    def _get_export_path(self):
        i = 1
        while True:
            path = "%s/export%03d.bvh" % (self.experiment.args.export_dir, i)
            if not os.path.exists(path):
                return path
            i += 1

    def _export_output(self):
        if self.experiment.output is not None:
            hips = self.parameters_to_hips(self.experiment.output)
            frame = self._joint_to_bvh_frame(hips)
            self.experiment.bvh_writer.add_frame(frame)

    def _joint_to_bvh_frame(self, joint):
        result = []
        for channel in joint.channels:
            result.append(self._bvh_channel_data(joint, channel))
        for child in joint.children:
            result += self._joint_to_bvh_frame(child)
        return result

    def _bvh_channel_data(self, joint, channel):
        return getattr(joint, channel)()

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
        self.experiment.entity.update()
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

        glRotatef(self._camera_x_orientation, 1.0, 0.0, 0.0)
        glRotatef(self._camera_y_orientation, 0.0, 1.0, 0.0)
        glTranslatef(*(self.camera_translation() + self._camera_position))

    def camera_translation(self):
        return numpy.zeros(3)

    def sizeHint(self):
        return QtCore.QSize(600, 640)

    def centralize_output(self):
        pass

    def _draw_floor(self):
        GRID_NUM_CELLS = 30
        GRID_SIZE = 100
        y = 0
        z1 = -GRID_SIZE/2
        z2 = GRID_SIZE/2
        x1 = -GRID_SIZE/2
        x2 = GRID_SIZE/2

        glLineWidth(1.0)
        glColor4f(0, 0, 0, 0.2)

        for n in range(GRID_NUM_CELLS):
            glBegin(GL_LINES)
            x = x1 + float(n) / GRID_NUM_CELLS * GRID_SIZE
            glVertex3f(x, y, z1)
            glVertex3f(x, y, z2)
            glEnd()

        for n in range(GRID_NUM_CELLS):
            glBegin(GL_LINES)
            z = z1 + float(n) / GRID_NUM_CELLS * GRID_SIZE
            glVertex3f(x1, y, z)
            glVertex3f(x2, y, z)
            glEnd()

    def _draw_focus(self):
        glLineWidth(1.0)
        glColor4f(0, 0, 0, 0.2)
        self._draw_circle(self._focus, FOCUS_RADIUS)

    def _draw_circle(self, center, radius):
        y = center[1]
        glBegin(GL_LINE_STRIP)
        for i in range(CIRCLE_PRECISION):
            angle = math.pi * 2 * float(i) / (CIRCLE_PRECISION-1)
            x = center[0] + radius * math.cos(angle)
            z = center[2] + radius * math.sin(angle)
            glVertex3f(x, y, z)
        glEnd()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and not self._following_output():
            self._dragging_orientation = True
        elif event.button() == QtCore.Qt.RightButton:
            self._dragging_y_position = True

    def mouseReleaseEvent(self, event):
        self._dragging_orientation = False
        self._dragging_y_position = False
        self._drag_x_previous = event.x()
        self._drag_y_previous = event.y()

    def mouseMoveEvent(self, event):
        x = event.x()
        y = event.y()
        if self._dragging_orientation:
            self._set_camera_orientation(
                self._camera_y_orientation + CAMERA_DRAG_SPEED * (x - self._drag_x_previous),
                self._camera_x_orientation + CAMERA_DRAG_SPEED * (y - self._drag_y_previous))
        elif self._dragging_y_position:
            self._camera_position[1] += CAMERA_Y_SPEED * (y - self._drag_y_previous)
        self._drag_x_previous = x
        self._drag_y_previous = y

    def print_camera_settings(self):
        print "%.3f,%.3f,%.3f,%.3f,%.3f" % (
            self._camera_position[0],
            self._camera_position[1],
            self._camera_position[2],
            self._camera_y_orientation, self._camera_x_orientation)

    def _set_camera_position(self, position):
        self._camera_position = position

    def _set_camera_orientation(self, y_orientation, x_orientation):
        self._camera_y_orientation = y_orientation
        self._camera_x_orientation = x_orientation

    def keyPressEvent(self, event):
        if not self._following_output():
            r = math.radians(self._camera_y_orientation)
            new_position = self._camera_position
            key = event.key()
            if key == QtCore.Qt.Key_A:
                new_position[0] += CAMERA_KEY_SPEED * math.cos(r)
                new_position[2] += CAMERA_KEY_SPEED * math.sin(r)
                self._set_camera_position(new_position)
            elif key == QtCore.Qt.Key_D:
                new_position[0] -= CAMERA_KEY_SPEED * math.cos(r)
                new_position[2] -= CAMERA_KEY_SPEED * math.sin(r)
                self._set_camera_position(new_position)
            elif key == QtCore.Qt.Key_W:
                new_position[0] += CAMERA_KEY_SPEED * math.cos(r + math.pi/2)
                new_position[2] += CAMERA_KEY_SPEED * math.sin(r + math.pi/2)
                self._set_camera_position(new_position)
            elif key == QtCore.Qt.Key_S:
                new_position[0] -= CAMERA_KEY_SPEED * math.cos(r + math.pi/2)
                new_position[2] -= CAMERA_KEY_SPEED * math.sin(r + math.pi/2)
                self._set_camera_position(new_position)

    def _following_output(self):
        return self._parent.following_output()

    def central_output_position(self, output):
        return numpy.zeros(3)

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
        size_policy = QtGui.QSizePolicy(
            QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(2)

        self._scene = scene_widget_class(self, experiment, args)
        self._scene.setSizePolicy(size_policy)
        self._create_menu()
        self._layout.addWidget(self._scene)

        self.toolbar = toolbar_class(self, experiment, args)
        self.toolbar.setFixedSize(TOOLBAR_WIDTH, TOOLBAR_HEIGHT)
        self._layout.addWidget(self.toolbar)
        self._layout.setAlignment(self.toolbar, QtCore.Qt.AlignTop)

        self.setLayout(self._layout)

        self.experiment.time_increment = 0
        self.stopwatch = Stopwatch()
        self._frame_count = 0
        self._set_up_timed_refresh()

    def sizeHint(self):
        return QtCore.QSize(1000, 640)

    def _set_up_timed_refresh(self):
        timer = QtCore.QTimer(self)
        timer.setInterval(1000. / self.args.frame_rate)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), self._refresh)
        timer.start()

    def _create_menu(self):
        self._menu_bar = QtGui.QMenuBar()
        self._layout.setMenuBar(self._menu_bar)
        self._create_main_menu()
        self._create_view_menu()

    def _create_main_menu(self):
        self._main_menu = self._menu_bar.addMenu("Main")
        self._add_toggleable_action(
            "Start", self.experiment.start,
            "Stop", self.experiment.stop,
            True, " ")
        self._add_toggleable_action(
            '&Export output', self._scene.start_export_output,
            '&Stop export', self._scene.stop_export_output,
            False, 'Ctrl+E')
        self._add_show_camera_settings_action()

    def _add_toggleable_action(self,
                               enable_title, enable_handler,
                               disable_title, disable_handler,
                               default, shortcut):
        enable_action = QtGui.QAction(enable_title, self)
        enable_action.setShortcut(shortcut)
        enable_action.triggered.connect(lambda: self._enable(enable_handler, enable_action, disable_action))
        enable_action.setEnabled(not default)
        self._main_menu.addAction(enable_action)

        disable_action = QtGui.QAction(disable_title, self)
        disable_action.setShortcut(shortcut)
        disable_action.triggered.connect(lambda: self._disable(disable_handler, enable_action, disable_action))
        disable_action.setEnabled(default)
        self._main_menu.addAction(disable_action)

    def _enable(self, handler, enable_action, disable_action):
        enable_action.setEnabled(False)
        disable_action.setEnabled(True)
        handler()

    def _disable(self, handler, enable_action, disable_action):
        disable_action.setEnabled(False)
        enable_action.setEnabled(True)
        handler()

    def _add_show_camera_settings_action(self):
        action = QtGui.QAction('Show camera settings', self)
        action.triggered.connect(self._scene.print_camera_settings)
        self._main_menu.addAction(action)
        
    def _create_view_menu(self):
        self._view_menu = self._menu_bar.addMenu("View")
        self._add_toolbar_action()
        self._add_fullscreen_action()
        self._add_follow_action()
        self._add_focus_action()
        self._add_floor_action()

    def _add_toolbar_action(self):
        self._toolbar_action = QtGui.QAction('Toolbar', self)
        self._toolbar_action.setCheckable(True)
        self._toolbar_action.setChecked(True)
        self._toolbar_action.setShortcut('Ctrl+T')
        self._toolbar_action.toggled.connect(self._toggled_toolbar)
        self._view_menu.addAction(self._toolbar_action)

    def _toggled_toolbar(self):
        if self._toolbar_action.isChecked():
            self.toolbar.setFixedSize(TOOLBAR_WIDTH, TOOLBAR_HEIGHT)
        else:
            self.toolbar.setFixedSize(0, TOOLBAR_HEIGHT)

    def _add_fullscreen_action(self):
        self._fullscreen_action = QtGui.QAction('Fullscreen', self)
        self._fullscreen_action.setCheckable(True)
        self._fullscreen_action.setShortcut('Ctrl+Return')
        self._fullscreen_action.toggled.connect(self._toggled_fullscreen)
        self._view_menu.addAction(self._fullscreen_action)

    def _toggled_fullscreen(self):
        if self._fullscreen_action.isChecked():
            self.showFullScreen()
        else:
            self.showNormal()

    def _add_follow_action(self):
        self._follow_action = QtGui.QAction('&Follow output', self)
        self._follow_action.setCheckable(True)
        self._follow_action.setChecked(True)
        self._follow_action.setShortcut('Ctrl+F')
        self._follow_action.toggled.connect(self._toggled_follow)
        self._view_menu.addAction(self._follow_action)

    def _toggled_follow(self):
        if self.following_output():
            self._scene.set_default_camera_orientation()

    def following_output(self):
        return self._follow_action.isChecked()

    def _add_focus_action(self):
        self.focus_action = QtGui.QAction("Assumed focus", self)
        self.focus_action.setCheckable(True)
        self.focus_action.setShortcut('Ctrl+G')
        self._view_menu.addAction(self.focus_action)

    def _add_floor_action(self):
        self._floor_action = QtGui.QAction("Floor", self)
        self._floor_action.setCheckable(True)
        self._floor_action.setChecked(self._scene.view_floor)
        self._floor_action.setShortcut("f")
        self._floor_action.toggled.connect(self._toggled_floor)
        self._view_menu.addAction(self._floor_action)

    def _toggled_floor(self):
        self._scene.view_floor = self._floor_action.isChecked()

    def _refresh(self):
        self.now = self.current_time()
        if self._frame_count == 0:
            self.stopwatch.start()
        else:
            if self.experiment.is_running():
                self.experiment.time_increment = self.now - self.previous_frame_time
                self.experiment.proceed()

            self.experiment.update()
            self._scene.updateGL()
            self.toolbar.refresh()

        self.previous_frame_time = self.now
        self._frame_count += 1

    def current_time(self):
        return self.stopwatch.get_elapsed_time()

    def keyPressEvent(self, event):
        self._scene.keyPressEvent(event)
        QtGui.QWidget.keyPressEvent(self, event)


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
        parser.add_argument("-input-y-offset", type=float, default=.0)
        parser.add_argument("-output-y-offset", type=float, default=.0)
        parser.add_argument("-export-dir", default="export")
        parser.add_argument("--camera", help="posX,posY,posZ,orientY,orientX",
                            default="-3.767,-1.400,-3.485,-55.500,18.500")
        parser.add_argument("--floor", action="store_true")

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
            self.bvh_writer = BvhWriter(self.bvh_reader)
        else:
            self.bvh_reader = None
        self.input = None
        self.output = None
        self.entity = entity_class(self)
        self._scene_class = entity_module.Scene
        self._running = True

    def start(self):
        self._running = True

    def stop(self):
        self._running = False

    def is_running(self):
        return self._running

    def update(self):
        pass

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
    def __init__(self, source, target, duration=2):
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
            self._velocity(self._t / self._duration)

    def _velocity(self, relative_t):
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

class Layer:
    def __init__(self, rendering_function):
        self._rendering_function = rendering_function
        self._updated = False
        self._display_list_id = None

    def draw(self):
        if not self._updated:
            if self._display_list_id is None:
                self._display_list_id = glGenLists(1)
            glNewList(self._display_list_id, GL_COMPILE)
            self._rendering_function()
            glEndList()
            self._updated = True
        glCallList(self._display_list_id)

    def refresh(self):
        self._updated = False
