from argparse import ArgumentParser
from PyQt4 import QtGui, QtCore

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")
from fps_meter import FpsMeter

parser = ArgumentParser()
parser.add_argument("--frame-rate", type=float, default=50.0)
args = parser.parse_args()

class UiWindow(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self._fps_meter = FpsMeter()
        timer = QtCore.QTimer(self)
        timer.setInterval(1000. / args.frame_rate)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), self._update)
        timer.start()

    def _update(self):
        self._fps_meter.update()
            
qt_app = QtGui.QApplication(sys.argv)
ui_window = UiWindow()
ui_window.show()
qt_app.exec_()
