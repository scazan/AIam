from experiment import *
from backprop_net import BackpropNet
from prediction_teacher import *

class PredictionExperiment(Experiment):
    @staticmethod
    def add_parser_arguments(parser):
        Experiment.add_parser_arguments(parser)
        parser.add_argument("-training-duration", type=float, default=100)
        parser.add_argument("-shuffle-input", action="store_true")
        parser.add_argument("-plot", type=str)
        parser.add_argument("-plot-duration", type=float, default=10)

    def __init__(self, scene, args):
        self.args = args
        self._scene_class = scene
        if args.bvh:
            self.bvh_reader = bvh_reader_module.BvhReader(args.bvh)
            self.bvh_reader.read()
        else:
            self.bvh_reader = None
        if self.args.model is None:
            self.args.model = "models/prediction/%s.model" % args.entity
        self.input = None
        self.output = None

    def run(self, student, stimulus):
        self.stimulus = stimulus
        self.student = student

        if self.args.shuffle_input:
            self.teacher = ShufflingTeacher(stimulus)
        else:
            self.teacher = LiveTeacher(stimulus)

        if self.args.train:
            self._train_model()
            self.save_model(self.args.model)

        elif self.args.plot:
            LearningPlotter(student, teacher, self.args.plot_duration).plot(self.args.plot)

        else:
            self.student = self.load_model(self.args.model)
        
            app = QtGui.QApplication(sys.argv)
            self.window = MainWindow(
                self, self._scene_class, ExperimentToolbar, self.args)
            self.window.show()
            app.exec_()

    def proceed(self, time_increment):
        if self.teacher.collected_enough_training_data():
            inp = self.teacher.get_input()
            expected_output = self.teacher.get_output()
            self.student.train(inp, expected_output)
        self.teacher.proceed(time_increment)

        self.input = self.stimulus.get_value()
        self.output = self.student.process(self.input)

    def _train_model(self):
        print "training model..."
        t = 0
        time_increment = 1.0 / 50
        while t < self.args.training_duration:
            if self.teacher.collected_enough_training_data():
                inp = self.teacher.get_input()
                output = self.teacher.get_output()
                self.student.train(inp, output)
            self.teacher.proceed(time_increment)
            t += time_increment
        print "ok"
