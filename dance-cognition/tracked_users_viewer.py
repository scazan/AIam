from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui
import collections
from vector import Vector3d
from ui.scene import Scene
text_renderer_module = __import__("text_renderer")

FRAME_RATE = 30
CAMERA_Y_SPEED = 1
CAMERA_KEY_SPEED = 40
CAMERA_DRAG_SPEED = .1
PROJECTION_NEAR = 0.1
PROJECTION_FAR = 20000.0
LOG_HEIGHT = 50
SKELETON_WIDTH_SELECTED = 2
SKELETON_WIDTH_UNSELECTED = 1
SKELETON_COLOR_SELECTED = (0, 0, 0)
SKELETON_COLOR_UNSELECTED = (.2, .2, .4)
CIRCLE_PRECISION = 100
CENTER_POSITION_SYMBOL_SIZE = 200

class TrackedUsersScene(Scene):
    def __init__(self, parent):
        Scene.__init__(self, parent, parent.args,
                       camera_y_speed=CAMERA_Y_SPEED,
                       camera_key_speed=CAMERA_KEY_SPEED,
                       camera_drag_speed=CAMERA_DRAG_SPEED)
        self._text_renderer_class = getattr(text_renderer_module, "GlutTextRenderer")

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 0.0)
        glClearAccum(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glEnable(GL_POINT_SMOOTH)

        glShadeModel(GL_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glutInit(sys.argv)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(self.margin, self.margin, 0)
        self.configure_3d_projection(pixdx=-100, pixdy=0, fovy=40.0,
                                     near=PROJECTION_NEAR, far=PROJECTION_FAR)

        self.draw_floor(
            num_cells=30,
            size=PROJECTION_FAR-PROJECTION_NEAR,
            y=self.parent().floor_y,
            color=(0,0,0,0.2))

        self._selected_user = self.parent().interpreter.get_selected_user()
        for user in self.parent().interpreter.get_users().values():
            self._draw_user(user)

        if self.parent().show_center_position_action.isChecked():
            self._draw_center_position()

        if self.parent().show_positions_action.isChecked():
            self._print_positions()

    def _draw_user(self, user):
        self._draw_label(user)
        self._draw_activity(user)
        self._draw_skeleton(user)

    def _draw_skeleton(self, user):
        if user == self._selected_user:
            line_width = SKELETON_WIDTH_SELECTED
        else:
            line_width = SKELETON_WIDTH_UNSELECTED
        glLineWidth(line_width)
        self._draw_limb(user, "head", "neck")
        self._draw_limb(user, "left_shoulder", "left_elbow")
        self._draw_limb(user, "left_elbow", "left_hand")
        self._draw_limb(user, "right_shoulder", "right_elbow")
        self._draw_limb(user, "right_elbow", "right_hand")
        self._draw_limb(user, "left_shoulder", "right_shoulder")
        self._draw_limb(user, "left_shoulder", "torso")
        self._draw_limb(user, "right_shoulder", "torso")
        self._draw_limb(user, "left_hip", "torso")
        self._draw_limb(user, "right_hip", "torso")
        self._draw_limb(user, "left_hip", "right_hip")
        self._draw_limb(user, "left_hip", "left_knee")
        self._draw_limb(user, "left_knee", "left_foot")
        self._draw_limb(user, "right_hip", "right_knee")
        self._draw_limb(user, "right_knee", "right_foot")

    def _draw_label(self, user):
        head_position = user.get_joint("head").get_position()
        glColor3f(0, 0, 0)
        position = Vector3d(*head_position) + Vector3d(0, 140, 0)
        self._draw_text(str(user.get_id()), 100, *position, h_align="center")

    def _draw_activity(self, user):
        head_position = user.get_joint("head").get_position()
        position = Vector3d(*head_position) + Vector3d(150, 140, 0)
        activity = user.get_activity()

        glColor3f(.8, .8, 1)
        self._draw_solid_cube(*position, sx=70, sz=70, sy=self._activity_as_height(
                self.parent().interpreter.activity_ceiling))

        glColor3f(.5, .5, 1)
        self._draw_solid_cube(*position, sx=70, sz=70, sy=self._activity_as_height(activity))

        glColor3f(.5, .5, 1)
        self._draw_text("%.1f" % activity, 100, *(position + Vector3d(0, -100, 0)), h_align="center")

    def _activity_as_height(self, activity):
        return activity * 3

    def _draw_solid_cube(self, x, y, z, sx, sy, sz, y_align_bottom=True):
        if y_align_bottom:
            y += sy/2
        glPushMatrix()
        glTranslatef(x, y, z)
        glScale(sx, sy, sz)
        glutSolidCube(1)
        glPopMatrix()

    def _draw_limb(self, user, name1, name2):
        glBegin(GL_LINES)
        self._set_color_by_joint(user, user.get_joint(name1))
        glVertex3f(*user.get_joint(name1).get_position())
        self._set_color_by_joint(user, user.get_joint(name2))
        glVertex3f(*user.get_joint(name2).get_position())
        glEnd()

    def _set_color_by_joint(self, user, joint):
        a = 1 - (.8 - joint.get_confidence() * .8)
        if user == self._selected_user:
            r, g, b = SKELETON_COLOR_SELECTED
        else:
            r, g, b = SKELETON_COLOR_UNSELECTED
        glColor4f(r, g, b, a)

    def _draw_text(self, text, size, x, y, z, font=GLUT_STROKE_ROMAN, spacing=None,
                  v_align="left", h_align="top"):
        self._text_renderer(text, size, font).render(x, y, z, v_align, h_align)

    def _text_renderer(self, text, size, font):
        return self._text_renderer_class(self, text, size, font)

    def _draw_center_position(self):
        glLineWidth(1)
        glColor4f(0, 0, 0, .8)
        x = self.parent().interpreter.center_x
        z = self.parent().interpreter.center_z
        y = self.parent().floor_y
        x1 = x - CENTER_POSITION_SYMBOL_SIZE/2
        x2 = x + CENTER_POSITION_SYMBOL_SIZE/2
        z1 = z - CENTER_POSITION_SYMBOL_SIZE/2
        z2 = z + CENTER_POSITION_SYMBOL_SIZE/2
        glBegin(GL_LINES)
        glVertex3f(x1, y, z1)
        glVertex3f(x2, y, z2)
        glVertex3f(x2, y, z1)
        glVertex3f(x1, y, z2)
        glEnd()
        
    def _print_positions(self):
        for user in self.parent().interpreter.get_users().values():
            torso_x, _, torso_z = user.get_joint("torso").get_position()
            floor_y = min([user.get_joint("left_foot").get_position()[1],
                           user.get_joint("right_foot").get_position()[1]])
            print "[%s] torso: %.1f,%.1f  floor_y: %.1f" % (user.get_id(), torso_x, torso_z, floor_y)

class LogWidget(QtGui.QTextEdit):
    def __init__(self, *args, **kwargs):
        QtGui.QTextEdit.__init__(self, *args, **kwargs)
        self.setReadOnly(True)

    def append(self, string):
        self.insertPlainText(string)
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def sizeHint(self):
        return QtCore.QSize(640, LOG_HEIGHT)

class TrackedUsersViewer(QtGui.QWidget):
    def __init__(self, interpreter, args, enable_osc_replay=False, osc_receiver=None):
        QtGui.QWidget.__init__(self)
        self.args = args
        self._enable_osc_replay = enable_osc_replay
        self._osc_receiver = osc_receiver
        self.interpreter = interpreter
        self.floor_y = args.floor_y
        self._layout = QtGui.QVBoxLayout()
        self._layout.setSpacing(0)
        self._layout.setMargin(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        self._scene = TrackedUsersScene(self)
        size_policy = QtGui.QSizePolicy(
            QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        size_policy.setVerticalStretch(2)
        size_policy.setHorizontalStretch(2)
        self._scene.setSizePolicy(size_policy)

        self._layout.addWidget(self._scene)
        self._log_widget = LogWidget(self)
        self._layout.addWidget(self._log_widget)
        self._create_menu()

        timer = QtCore.QTimer(self)
        timer.setInterval(1000. / FRAME_RATE)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), self._scene.updateGL)
        timer.start()

    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("--camera", help="posX,posY,posZ,orientY,orientX",
                            default="463.324,-20.000,1515.835,-194.200,4.400")
        parser.add_argument("--floor-y", type=float, default=0)

    def _create_menu(self):
        self._menu_bar = QtGui.QMenuBar()
        self._layout.setMenuBar(self._menu_bar)
        self._create_main_menu()
        self._create_view_menu()
        if self._enable_osc_replay:
            self._create_replay_menu()

    def _create_main_menu(self):
        self._main_menu = self._menu_bar.addMenu("Main")
        self._add_show_camera_settings_action()
        self._add_show_positions_action()

    def _add_show_camera_settings_action(self):
        action = QtGui.QAction('Show camera settings', self)
        action.triggered.connect(self._scene.print_camera_settings)
        self._main_menu.addAction(action)

    def _add_show_positions_action(self):
        self.show_positions_action = QtGui.QAction('Show positions', self)
        self.show_positions_action.setCheckable(True)
        self.show_positions_action.setShortcut("Ctrl+Shift+p")
        self._main_menu.addAction(self.show_positions_action)

    def _create_view_menu(self):
        self._view_menu = self._menu_bar.addMenu("View")
        self._add_show_center_position_action()

    def _add_show_center_position_action(self):
        self.show_center_position_action = QtGui.QAction('Show center position', self)
        self.show_center_position_action.setCheckable(True)
        self.show_center_position_action.setShortcut("Ctrl+p")
        self._view_menu.addAction(self.show_center_position_action)

    def _create_replay_menu(self):
        self._replay_menu = self._menu_bar.addMenu("Replay")
        self._add_replay_slower_action()
        self._add_replay_faster_action()
        self._add_reset_replay_speed_action()

    def _add_replay_slower_action(self):
        action = QtGui.QAction("Replay slower", self)
        action.setShortcut("-")
        action.triggered.connect(lambda: self._change_replay_speed(-1))
        self._replay_menu.addAction(action)

    def _add_replay_faster_action(self):
        action = QtGui.QAction("Replay faster", self)
        action.setShortcut("+")
        action.triggered.connect(lambda: self._change_replay_speed(+1))
        self._replay_menu.addAction(action)

    def _add_reset_replay_speed_action(self):
        action = QtGui.QAction("Reset replay speed", self)
        action.setShortcut("0")
        action.triggered.connect(lambda: self._set_replay_speed(1))
        self._replay_menu.addAction(action)

    def _change_replay_speed(self, factor):
        current_speed = self._osc_receiver.log_replay_speed
        new_speed = max(current_speed + factor * 0.2, 0.1)
        self._set_replay_speed(new_speed)

    def _set_replay_speed(self, speed):
        self._osc_receiver.log_replay_speed = speed
        print "OSC replay speed: %.1f" % speed
        
    def keyPressEvent(self, event):
        self._scene.keyPressEvent(event)
        QtGui.QWidget.keyPressEvent(self, event)

    def handle_joint_data(self, *args):
        self._scene.handle_joint_data(*args)

    def handle_state(self, user_id, state):
        self._log_widget.append("%s %s\n" % (state, user_id))

    def sizeHint(self):
        return QtCore.QSize(640, 480)
