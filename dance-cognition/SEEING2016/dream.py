import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui, QtOpenGL
from dimensionality_reduction.dimensionality_reduction_experiment import *
from ui.scene import Scene

FRAME_RATE = 50
CAMERA_Y_SPEED = .01
CAMERA_KEY_SPEED = .1
CAMERA_DRAG_SPEED = .1
PROJECTION_NEAR = 0.1
PROJECTION_FAR = 20000.0

class DreamScene(Scene):
    def __init__(self, parent):
        Scene.__init__(self, parent, parent.args,
                       camera_y_speed=CAMERA_Y_SPEED,
                       camera_key_speed=CAMERA_KEY_SPEED,
                       camera_drag_speed=CAMERA_DRAG_SPEED)
        self._experiment = parent.experiment

        if parent.args.z_up:
            self.bvh_coordinate_left = 0
            self.bvh_coordinate_up = 2
            self.bvh_coordinate_far = 1
        else:
            self.bvh_coordinate_left = 0
            self.bvh_coordinate_up = 1
            self.bvh_coordinate_far = 2

        self._vertices = None

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClearAccum(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glEnable(GL_POINT_SMOOTH)

        glShadeModel(GL_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glutInit(sys.argv)

    def update(self):
        time_increment = 1.0 / FRAME_RATE
        improviser.proceed(time_increment)
        reduction = improviser.current_position()
        output = self._experiment.student.inverse_transform(numpy.array([reduction]))[0]
        self._vertices = self._experiment.entity.process_output(output)
        self.updateGL()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        self.configure_3d_projection(pixdx=-100, pixdy=0, fovy=40.0,
                                     near=PROJECTION_NEAR, far=PROJECTION_FAR)
        if self._vertices:
            self._draw_skeleton()

    def _draw_skeleton(self):
        glColor3f(1, 1, 1)
        edges = self._experiment.bvh_reader.vertices_to_edges(self._vertices)
        self._draw_edges(edges)

    def _draw_edges(self, edges):
        for edge in edges:
            self._draw_line(edge.v1, edge.v2)

    def _draw_line(self, v1, v2):
        glBegin(GL_LINES)
        self.bvh_vertex(v1)
        self.bvh_vertex(v2)
        glEnd()

    def bvh_vertex(self, v):
        glVertex3f(
            v[self.bvh_coordinate_left],
            v[self.bvh_coordinate_up],
            v[self.bvh_coordinate_far])

class MainWindow(QtGui.QWidget):
    def __init__(self, experiment):
        self.experiment = experiment
        self.args = experiment.args

        QtGui.QMainWindow.__init__(self)
        self._layout = QtGui.QVBoxLayout()
        self._layout.setSpacing(0)
        self._layout.setMargin(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
        self._add_scene()

        timer = QtCore.QTimer(self)
        timer.setInterval(1000. / FRAME_RATE)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), self._update)
        timer.start()

    def _add_scene(self):
        self._scene = DreamScene(self)
        self._layout.addWidget(self._scene)

    def _update(self):
        self._scene.update()

    def sizeHint(self):
        return QtCore.QSize(640, 480)

parser = ArgumentParser()
DimensionalityReductionExperiment.add_parser_arguments(parser)
experiment = DimensionalityReductionExperiment(parser)
experiment._load_model()
experiment.navigator = Navigator(map_points=experiment.student.normalized_observed_reductions)
improviser_params = ImproviserParameters()
improviser = Improviser(experiment, improviser_params)

app = QtGui.QApplication(sys.argv)
window = MainWindow(experiment)
window.show()
app.exec_()
