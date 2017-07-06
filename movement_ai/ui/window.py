from PyQt4 import QtCore, QtGui

class Window(QtGui.QWidget):
    def __init__(self, args):
        QtGui.QWidget.__init__(self)
        self._fullscreen_display = args.fullscreen

    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("--fullscreen", action="store_true")
        parser.add_argument("--fullscreen-display", type=int)

    def give_keyboard_focus_to_fullscreen_window(self):
        self.resizeEvent = lambda event: self.activateWindow()

    def enter_fullscreen(self):
        self.setCursor(QtCore.Qt.BlankCursor)
        self.showFullScreen()
        if self.args.fullscreen_display is not None:
            geometry = QtGui.QApplication.desktop().screenGeometry(
                self._fullscreen_display);
            self.move(QtCore.QPoint(geometry.x(), geometry.y()));
            self.resize(geometry.width(), geometry.height());

    def leave_fullscreen(self):
        self.setCursor(QtCore.Qt.ArrowCursor)
        self.showNormal()
