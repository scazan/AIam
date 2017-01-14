from openni import openni2
import argparse
import sys
import threading
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PyQt4 import QtCore, QtGui, QtOpenGL

MAX_DEPTH = 10000

class CameraWidget(QtOpenGL.QGLWidget):
    def __init__(self, *args, **kwargs):
        QtOpenGL.QGLWidget.__init__(self, *args, **kwargs)
        self._depth_frame = None

    def on_depth_frame(self, depth_frame):
        self._depth_frame = depth_frame
        self.updateGL()

    def render(self):
        if self._depth_frame is None:
            return
        buf = self._depth_frame.get_buffer_as_uint16()
        row_size = self._depth_frame.stride / 2
        glBegin(GL_POINTS)
        i_row = 0
        for y in range(self._depth_frame.height):
            i = i_row
            for x in range(self._depth_frame.width):
                depth = buf[i]
                if depth > 0:
                    normalized_depth = 1 - float(depth) / MAX_DEPTH
                    glColor3f(normalized_depth, normalized_depth, normalized_depth)
                    glVertex2f(x, y)
                i += 1
            i_row += row_size
        glEnd()

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

    def customEvent(self, custom_qt_event):
        custom_qt_event.callback()

    def on_depth_frame(self, depth_frame):
        self._camera_widget.on_depth_frame(depth_frame)
        
class CustomQtEvent(QtCore.QEvent):
    EVENT_TYPE = QtCore.QEvent.Type(QtCore.QEvent.registerEventType())

    def __init__(self, callback):
        QtCore.QEvent.__init__(self, CustomQtEvent.EVENT_TYPE)
        self.callback = callback

def process_depth_stream():
    while True:
        depth_frame = depth_stream.read_frame()
        QtGui.QApplication.postEvent(window, CustomQtEvent(
                lambda: window.on_depth_frame(depth_frame)))

parser = argparse.ArgumentParser()
parser.add_argument("-device")
# parser.add_argument("-fps", type=int, default=30)
args = parser.parse_args()

openni2.initialize()
device = openni2.Device.open_file(args.device)
depth_stream = device.create_depth_stream()
# depth_mode = depth_stream.get_video_mode()
# print depth_mode
# depth_mode.fps = args.fps
# depth_mode.resolutionX = 640
# depth_mode.resolutionY = 480
# depth_mode.pixelFormat = openni2.PIXEL_FORMAT_DEPTH_1_MM
# depth_stream.set_video_mode(depth_mode)
depth_stream.start()

app = QtGui.QApplication(sys.argv)
window = MainWindow()
window.show()
depth_stream_processing_thread = threading.Thread(
    target=process_depth_stream)
depth_stream_processing_thread.daemon = True
depth_stream_processing_thread.start()
app.exec_()
