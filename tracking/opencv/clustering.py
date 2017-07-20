from openni import openni2
import argparse
import sys
import numpy
import sklearn.cluster
import random
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui, QtOpenGL

class CameraWidget(QtOpenGL.QGLWidget):
    def __init__(self, *args, **kwargs):
        QtOpenGL.QGLWidget.__init__(self, *args, **kwargs)
        self._cluster_colors = {}

    def render(self):
        glPointSize(1)
        glBegin(GL_POINTS)
        for point, cluster_index in zip(points, kmeans.labels_):
            glColor3f(*self._get_cluster_color(cluster_index))
            x, y, _ = openni2.convert_world_to_depth(depth_stream, *point)
            glVertex2f(x, y)
        glEnd()
            
    def _get_cluster_color(self, cluster_index):
        if cluster_index in self._cluster_colors:
            return self._cluster_colors[cluster_index]
        else:
            cluster_color = [random.uniform(0.0, 1.0) for n in range(3)]
            self._cluster_colors[cluster_index] = cluster_color
            return cluster_color

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClearAccum(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
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
        return QtCore.QSize(640, 480)

class MainWindow(QtGui.QWidget):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self._layout = QtGui.QVBoxLayout()
        self.setLayout(self._layout)
        self._camera_widget = CameraWidget(self)
        self._layout.addWidget(self._camera_widget)

class Blob:
    def __init__(self):
        self.points = []

def process_depth_frame():
    buf = depth_frame.get_buffer_as_uint16()
    row_size = depth_frame.stride / 2
    i_row = 0
    for y in range(depth_frame.height):
        i = i_row
        for x in range(depth_frame.width):
            depth = buf[i]
            if depth > 0 and depth <= args.max_depth:
                point = openni2.convert_depth_to_world(depth_stream, x, y, depth)
                points.append(point)
            i += 1
        i_row += row_size

    global kmeans
    kmeans = sklearn.cluster.KMeans(max_iter=1)
    kmeans.fit(points)
    print "found %d clusters" % len(kmeans.cluster_centers_)

parser = argparse.ArgumentParser()
parser.add_argument("-device")
parser.add_argument("--max-depth", type=int, default=10000)
args = parser.parse_args()

openni2.initialize()
device = openni2.Device.open_file(args.device)
depth_stream = device.create_depth_stream()
depth_stream.start()
depth_frame = depth_stream.read_frame()

points = []
process_depth_frame()

app = QtGui.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
