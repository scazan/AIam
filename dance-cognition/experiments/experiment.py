import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from argparse import ArgumentParser
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import window
import math
from teacher import *
from learning_plotter import LearningPlotter
from bvh_reader import bvh_reader as bvh_reader_module
import pickle

class Stimulus:
    def __init__(self):
        self._t = 0

    def proceed(self, time_increment):
        self._t += time_increment

class Improviser:
    def __init__(self):
        self._n_components = student.n_components
        self._value = [random.random() for n in range(self._n_components)]

    def proceed(self, time_increment):
        for n in range(self._n_components):
            self._value[n] = self._clamp(
                self._value[n] +
                random.uniform(-.5, .5) * min(time_increment*10, 1.))

    def value(self):
        return self._value

    def _clamp(self, x):
        return min(max(x, 0.), 1.)
    
class ExperimentWindow(window.Window):
    def __init__(self, experiment, args):
        self.bvh_reader = experiment.bvh_reader
        window.Window.__init__(self, args)
        if self.args.improvise:
            self._improviser = Improviser()

    def render(self):
        if self.args.improvise:
            self._improviser.proceed(self.time_increment)
            reduction = self._improviser.value()
        else:
            stimulus.proceed(self.time_increment)
            inp = stimulus.get_value()
            reduction = student.transform(inp)
        output = student.inverse_transform(reduction)

        self._draw_reduction(reduction)

        self.configure_3d_projection(-100, 0)
        self._draw_unit_cube()
        if not self.args.improvise:
            self.draw_input(inp)
        self.draw_output(output)

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

def add_parser_arguments(parser):
    window.Window.add_parser_arguments(parser)
    parser.add_argument("-train")
    parser.add_argument("-training-data-frame-rate", type=int, default=50)
    parser.add_argument("-model")
    parser.add_argument("-improvise", action="store_true")
    parser.add_argument("-bvh")
    parser.add_argument("-bvh-speed", type=float, default=1.0)
    parser.add_argument("-bvh-scale", type=float, default=40)
    parser.add_argument("-plot", type=str)
    parser.add_argument("-plot-duration", type=float, default=10)


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
