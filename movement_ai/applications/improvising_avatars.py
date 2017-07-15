#!/usr/bin/env python

# STUDENT_MODEL_PATH = "profiles/dimensionality_reduction/valencia_pn_autoencoder.model"
# SKELETON_DEFINITION = "scenes/pn-01.22_skeleton.bvh"
# DIMENSIONALITY_REDUCTION_TYPE = "AutoEncoder"
# DIMENSIONALITY_REDUCTION_ARGS = "--num-hidden-nodes=0 --learning-rate=0.005"
# ENTITY_ARGS = "-r quaternion --friction --translate"

STUDENT_MODEL_PATH = "profiles/dimensionality_reduction/valencia_pn.model"
SKELETON_DEFINITION = "scenes/pn-01.22_skeleton.bvh"
DIMENSIONALITY_REDUCTION_TYPE = "KernelPCA"
DIMENSIONALITY_REDUCTION_ARGS = ""
ENTITY_ARGS = "-r quaternion --friction --translate"

NUM_REDUCED_DIMENSIONS = 7
Z_UP = False
FLOOR = True
MAX_NOVELTY = 1.4

from argparse import ArgumentParser
import threading
from PyQt4 import QtGui, QtCore, QtOpenGL
import numpy

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")
from application import Application, Avatar
from entities.hierarchical import Entity
from bvh.bvh_reader import BvhReader
from dimensionality_reduction.behaviors.improvise import ImproviseParameters, Improvise
from dimensionality_reduction.factory import DimensionalityReductionFactory
import tracking.pn.receiver

parser = ArgumentParser()
parser.add_argument("--num-avatars", type=int, default=1)
parser.add_argument("--pn-host", default="localhost")
parser.add_argument("--pn-port", type=int, default=tracking.pn.receiver.SERVER_PORT_BVH)
parser.add_argument("--with-ui", action="store_true")
Application.add_parser_arguments(parser)
ImproviseParameters().add_parser_arguments(parser)
args = parser.parse_args()

bvh_reader = BvhReader(SKELETON_DEFINITION)
bvh_reader.read()
entity_args_strings = ENTITY_ARGS.split()
entity_args = parser.parse_args(entity_args_strings)

student = None

avatars = []
for index in range(args.num_avatars):
    pose = bvh_reader.get_hierarchy().create_pose()
    entity = Entity(bvh_reader, pose, FLOOR, Z_UP, entity_args)
    
    if student is None:
        num_input_dimensions = entity.get_value_length()
        student = DimensionalityReductionFactory.create(
            DIMENSIONALITY_REDUCTION_TYPE, num_input_dimensions, NUM_REDUCED_DIMENSIONS, DIMENSIONALITY_REDUCTION_ARGS)
        student.load(STUDENT_MODEL_PATH)

    improvise_params = ImproviseParameters()
    preferred_location = None
    improvise = Improvise(
        student,
        student.num_reduced_dimensions,
        improvise_params,
        preferred_location,
        MAX_NOVELTY)
    avatar = Avatar(index, entity, improvise)
    avatars.append(avatar)

application = Application(student, avatars, args)

def receive_from_pn(pn_entity):
    for frame in pn_receiver.get_frames():
        input_from_pn = pn_entity.get_value_from_frame(frame)
        application.set_input(input_from_pn)
        
pn_receiver = tracking.pn.receiver.PnReceiver()
print "connecting to PN server..."
pn_receiver.connect(args.pn_host, args.pn_port)
print "ok"
pn_pose = bvh_reader.get_hierarchy().create_pose()
pn_entity = Entity(bvh_reader, pn_pose, FLOOR, Z_UP, entity_args)
pn_receiver_thread = threading.Thread(target=lambda: receive_from_pn(pn_entity))
pn_receiver_thread.daemon = True
pn_receiver_thread.start()

class ControlWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent):
        QtOpenGL.QGLWidget.__init__(self, parent)
        self._dragging = False
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._dragging = True
            self._previous_position = numpy.array([event.x(), event.y()])
        else:
            QtOpenGL.QGLWidget.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        QtOpenGL.QGLWidget.mouseReleaseEvent(self, event)
            
    def mouseMoveEvent(self, event):
        if self._dragging:
            position = numpy.array([event.x(), event.y()])
            energy = numpy.linalg.norm(position - self._previous_position)
            self._previous_position = position
        
class UiWindow(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self._layout = QtGui.QVBoxLayout()
        self._layout.setSpacing(0)
        self._layout.setMargin(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        self._control_widget = ControlWidget(self)
        size_policy = QtGui.QSizePolicy(
            QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        size_policy.setVerticalStretch(2)
        size_policy.setHorizontalStretch(2)
        self._control_widget.setSizePolicy(size_policy)

        self._layout.addWidget(self._control_widget)
        
        timer = QtCore.QTimer(self)
        timer.setInterval(1000. / args.frame_rate)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), application.update)
        timer.start()

    def sizeHint(self):
        return QtCore.QSize(300, 300)

if args.with_ui:
    qt_app = QtGui.QApplication(sys.argv)
    ui_window = UiWindow()
    ui_window.show()
    qt_app.exec_()
else:
    application.run()
    
