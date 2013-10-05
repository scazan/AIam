import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from argparse import ArgumentParser
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import wx
from wx import glcanvas
import math
from teacher import *
from learning_plotter import LearningPlotter
from bvh_reader import bvh_reader as bvh_reader_module
import pickle
from stopwatch import Stopwatch

class Stimulus:
    def __init__(self):
        self._t = 0

    def proceed(self, time_increment):
        self._t += time_increment

class ExperimentWindow(wx.Frame):
    def __init__(self, experiment, args):
        self.bvh_reader = experiment.bvh_reader
        self.timer_duration = 1000. / args.frame_rate
        self.time_increment = 0
        self.stopwatch = Stopwatch()

        self.app = wx.App(False)
        style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Frame.__init__(self, None, wx.ID_ANY, "",
                          size=wx.Size(800, 600), style=style)
        self.canvas = glcanvas.GLCanvas(
            self,
            attribList=(glcanvas.WX_GL_RGBA,
                        glcanvas.WX_GL_DOUBLEBUFFER,
                        glcanvas.WX_GL_DEPTH_SIZE, 24))
        self.canvas.Bind(wx.EVT_SIZE, self._process_size_event)
        self.canvas.Bind(wx.EVT_PAINT, self._paint_canvas)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self._on_timer)
        self.GLinitialized = False

    def run(self):
        self.Show()
        self.app.MainLoop()

    def _process_size_event(self, event):
        self._resized_canvas()
        event.Skip()

    def _resized_canvas(self):
        if self.canvas.GetContext():
            self.Show()
            self.canvas.SetCurrent()
            size = self.canvas.GetClientSize()
            self._canvas_width = size.width
            self._canvas_height = size.height
            self._aspect_ratio = float(size.width) / size.height
            self.canvas.Refresh(False)

    def _paint_canvas(self, event):
        self.canvas.SetCurrent()
        if not self.GLinitialized:
            self.InitGL()
            self._resized_canvas()
            self.GLinitialized = True
            self.stopwatch.start()
            self.previous_frame_time = self.current_time()
        self._draw_canvas()
        self.timer.Start(self.timer_duration)
        event.Skip()

    def _on_timer(self, event):
        self.canvas.Refresh()

    def _draw_canvas(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        self.now = self.current_time()
        self.time_increment = self.now - self.previous_frame_time

        stimulus.proceed(self.time_increment)
        inp = stimulus.get_value()
        reduction = student.transform(inp)
        output = student.inverse_transform(reduction)

        self._draw_reduction(reduction)

        self.configure_3d_projection(-100, 0)
        self._draw_unit_cube()
        self.draw_input(inp)
        self.draw_output(output)

        self.canvas.SwapBuffers()
        self.previous_frame_time = self.now

    def current_time(self):
        return self.stopwatch.get_elapsed_time()

    def InitGL(self):
        glClearColor(1.0, 1.0, 1.0, 0.0)
        glClearAccum(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glShadeModel(GL_SMOOTH)
        glutInit(sys.argv)

    def _draw_reduction(self, reduction):
        glTranslatef(0, 50, 0)
        for n in range(len(reduction)):
            glTranslatef(50, 0, 0)
            glColor3f(.9, .9, .9)
            self._draw_rectangle(0, 0, 10, 100)
            glColor3f(0, 0, 0)
            glLineWidth(3.0)
            range_n = student.reduction_range[n]
            y = (reduction[n] - range_n["min"]) / \
                (range_n["max"] - range_n["min"]) * 100
            self._draw_line(0, y, 10, y)

    def _draw_rectangle(self, x1, y1, x2, y2):
        glBegin(GL_POLYGON)
        glVertex2f(x1, y1)
        glVertex2f(x1, y2)
        glVertex2f(x2, y2)
        glVertex2f(x2, y1)
        glVertex2f(x1, y1)
        glEnd()

    def _draw_line(self, x1, y1, x2, y2):
        glBegin(GL_LINES)
        glVertex2f(x1, y1)
        glVertex2f(x2, y2)
        glEnd()

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
        dx = -(pixdx*xwsize/self._canvas_width)
        dy = -(pixdy*ywsize/self._canvas_height)

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

def add_parser_arguments(parser):
    parser.add_argument("-train")
    parser.add_argument("-training-data-frame-rate", type=int, default=50)
    parser.add_argument("-model")
    parser.add_argument("-bvh")
    parser.add_argument("-bvh-speed", type=float, default=1.0)
    parser.add_argument("-bvh-scale", type=float, default=40)
    parser.add_argument("-plot", type=str)
    parser.add_argument("-plot-duration", type=float, default=10)
    parser.add_argument("-frame-rate", type=float, default=50.0)


class Experiment:
    def __init__(self, window_class, args):
        self.args = args
        self.window_class = window_class
        if args.bvh:
            self.bvh_reader = bvh_reader_module.BvhReader(args.bvh)
            self.bvh_reader.scale_factor = args.bvh_scale
            self.bvh_reader.read()
        else:
            self.bvh_reader = None

    def run(self, _student, _stimulus):
        global student, teacher, stimulus
        stimulus = _stimulus
        student = _student

        if self.args.train:
            teacher = Teacher(stimulus, self.args.training_data_frame_rate)
            self._train(student, teacher, self.args.train)

            # if self.args.plot:
            #     LearningPlotter(student, teacher, self.args.plot_duration).plot(self.args.plot)

        elif self.args.model:
            student = self._load_model(self.args.model)
            self.window_class(self, self.args).run()

        else:
            raise Exception("a model must either be loaded or trained")

    def _train(self, student, teacher, model_filename):
        print "training model..."
        student.fit(teacher.get_training_data())
        print student.explained_variance_ratio_, sum(student.explained_variance_ratio_)
        print "ok"

        print "probing model..."
        student.probe(teacher.get_training_data())
        print "ok"

        print "saving model..."
        f = open(model_filename, "w")
        pickle.dump(student, f)
        f.close()
        print "ok"
        
    def _load_model(self, model_filename):
        print "loading model..."
        f = open(model_filename)
        model = pickle.load(f)
        f.close()
        print "ok"
        return model
