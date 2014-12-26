from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui, QtOpenGL
import math
import numpy
from parameters import *
from event import Event
from event_listener import EventListener
from stopwatch import Stopwatch
from fps_meter import FpsMeter
from parameters_form import ParametersForm

TOOLBAR_WIDTH = 400
SLIDER_PRECISION = 1000
CIRCLE_PRECISION = 100
CAMERA_Y_SPEED = .1
CAMERA_KEY_SPEED = .5
CAMERA_DRAG_SPEED = .5
FOCUS_RADIUS = 1.

class BaseScene(QtOpenGL.QGLWidget):
    @staticmethod
    def add_parser_arguments(parser):
        pass

    def __init__(self, parent, bvh_reader, args):
        self._parent = parent
        self.bvh_reader = bvh_reader
        self.args = args
        self.view_floor = args.floor
        self._dragging_orientation = False
        self._dragging_y_position = False
        self._focus = None
        self._set_camera_from_arg(args.camera)
        self.processed_input = None
        self.processed_output = None
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
        self._focus = self.central_output_position(self.processed_output)

    def _output_outside_focus(self):
        if self._focus is not None:
            distance = numpy.linalg.norm(
                self.central_output_position(self.processed_output) - self._focus)
            return distance > FOCUS_RADIUS

    def received_output(self, processed_output):
        self.processed_output = processed_output
        if self._focus is None:
            self._set_focus()
        if self._following_output() and self._output_outside_focus():
            self.centralize_output(self.processed_output)
            self._set_focus()

    def render(self):
        self.configure_3d_projection(-100, 0)
        self._draw_io(self.processed_input, self.draw_input, self.args.input_y_offset)
        self._draw_io(self.processed_output, self.draw_output, self.args.output_y_offset)
        if self.view_floor:
            self._draw_floor()
        if self._parent.focus_action.isChecked():
            self._draw_focus()

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
    def __init__(self, parent, args):
        self.args = args
        QtOpenGL.QGLWidget.__init__(self, parent)

    def refresh(self):
        pass

    def add_parameter_fields(self, parameters, parent):
        return ParametersForm(parameters, parent)

class MainWindow(QtGui.QWidget, EventListener):
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("--width", dest="preferred_width", type=int, default=1000)
        parser.add_argument("--height", dest="preferred_height", type=int, default=720)
        parser.add_argument("--no-toolbar", action="store_true")

    def __init__(self, client, entity, student, bvh_reader, scene_widget_class, toolbar_class, args):
        self.client = client
        self.entity = entity
        self.student = student
        self.args = args

        EventListener.__init__(self)
        self.add_event_handler(Event.INPUT, self._handle_input)
        self.add_event_handler(Event.OUTPUT, self._handle_output)

        QtGui.QWidget.__init__(self)
        self._layout = QtGui.QHBoxLayout()
        size_policy = QtGui.QSizePolicy(
            QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(2)

        self._scene = scene_widget_class(self, bvh_reader, args)
        self._scene.setSizePolicy(size_policy)
        self._create_menu()
        self._layout.addWidget(self._scene)

        self.toolbar = toolbar_class(self, args)
        if self.args.no_toolbar:
            self._hide_toolbar()
        else:
            self._show_toolbar()
        self._layout.addWidget(self.toolbar)

        self._layout.setAlignment(self.toolbar, QtCore.Qt.AlignTop)
        self.setLayout(self._layout)

        self.time_increment = 0
        self._stopwatch = Stopwatch()
        self._frame_count = 0
        if self.args.show_fps:
            self._fps_meter = FpsMeter()

        client.set_event_listener(self)
        client.connect()

    def received_event(self, event):
        callback = lambda: self.handle_event(event)
        QtGui.QApplication.postEvent(self, CustomQtEvent(callback))

    def sizeHint(self):
        return QtCore.QSize(self.args.preferred_width, self.args.preferred_height)

    def _create_menu(self):
        self._menu_bar = QtGui.QMenuBar()
        self._layout.setMenuBar(self._menu_bar)
        self._create_main_menu()
        self._create_view_menu()

    def _create_main_menu(self):
        self._main_menu = self._menu_bar.addMenu("Main")
        self._add_toggleable_action(
            "Start", lambda: self.client.send_event(Event(Event.START)),
            "Stop", lambda: self.client.send_event(Event(Event.STOP)),
            True, " ")
        self._add_toggleable_action(
            '&Export output', lambda: self.client.send_event(Event(Event.START_EXPORT_OUTPUT)),
            '&Stop export', lambda: self.client.send_event(Event(Event.STOP_EXPORT_OUTPUT)),
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
        self._toolbar_action.setChecked(not self.args.no_toolbar)
        self._toolbar_action.setShortcut('Ctrl+T')
        self._toolbar_action.toggled.connect(self._toggled_toolbar)
        self._view_menu.addAction(self._toolbar_action)

    def _toggled_toolbar(self):
        if self._toolbar_action.isChecked():
            self._show_toolbar()
        else:
            self._hide_toolbar()

    def _show_toolbar(self):
        self.toolbar.setFixedSize(TOOLBAR_WIDTH, self.args.preferred_height)

    def _hide_toolbar(self):
        self.toolbar.setFixedSize(0, self.args.preferred_height)

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
        self._now = self._stopwatch.get_elapsed_time()
        if self._frame_count == 0:
            self._stopwatch.start()
        else:
            self.time_increment = self._now - self._previous_frame_time
            if self.args.show_fps:
                self._fps_meter.update()

            self._scene.updateGL()
            self.toolbar.refresh()

        self._previous_frame_time = self._now
        self._frame_count += 1

    def keyPressEvent(self, event):
        self._scene.keyPressEvent(event)
        QtGui.QWidget.keyPressEvent(self, event)

    def customEvent(self, custom_qt_event):
        custom_qt_event.callback()

    def _handle_input(self, event):
        self._scene.processed_input = event.content

    def _handle_output(self, event):
        self._scene.received_output(event.content)
        self._refresh()

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

class CustomQtEvent(QtCore.QEvent):
    EVENT_TYPE = QtCore.QEvent.Type(QtCore.QEvent.registerEventType())

    def __init__(self, callback):
        QtCore.QEvent.__init__(self, CustomQtEvent.EVENT_TYPE)
        self.callback = callback
