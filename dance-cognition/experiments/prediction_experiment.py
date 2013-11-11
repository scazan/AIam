from experiment import *
from backprop_net import BackpropNet
from prediction_teacher import *

class Stimulus:
    def __init__(self):
        self._t = 0

    def proceed(self, time_increment):
        self._t += time_increment


class PredictionExperiment(Experiment):
    @staticmethod
    def add_parser_arguments(parser):
        Experiment.add_parser_arguments(parser)
        parser.add_argument("-pretrain", type=float)
        parser.add_argument("-bvh")
        parser.add_argument("-bvh-speed", type=float, default=1.0)
        parser.add_argument("-plot", type=str)
        parser.add_argument("-plot-duration", type=float, default=10)
        parser.add_argument("-shuffle-input", action="store_true")

    def __init__(self, scene, args):
        self.args = args
        self._scene_class = scene
        if args.bvh:
            self.bvh_reader = bvh_reader_module.BvhReader(args.bvh)
            self.bvh_reader.read()
        else:
            self.bvh_reader = None
        self.input = None
        self.output = None

    def run(self, _student, _stimulus):
        global student, teacher, stimulus
        stimulus = _stimulus
        student = _student

        if self.args.shuffle_input:
            teacher = ShufflingTeacher(stimulus)
        else:
            teacher = LiveTeacher(stimulus)

        if self.args.pretrain > 0:
            pretrain(student, teacher, self.args.pretrain)

        if self.args.plot:
            LearningPlotter(student, teacher, self.args.plot_duration).plot(self.args.plot)
        else:
            app = QtGui.QApplication(sys.argv)
            self.window = MainWindow(
                self, self._scene_class, ExperimentToolbar, self.args)
            self.window.show()
            app.exec_()

    def proceed(self, time_increment):
        if teacher.collected_enough_training_data():
            inp = teacher.get_input()
            expected_output = teacher.get_output()
            student.train(inp, expected_output)
        teacher.proceed(time_increment)

        self.input = stimulus.get_value()
        self.output = student.process(self.input)
