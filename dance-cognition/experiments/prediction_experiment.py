from experiment import *
from backprop_net import BackpropNet
from prediction_teacher import *

class PredictionExperiment(Experiment):
    @staticmethod
    def add_parser_arguments(parser):
        Experiment.add_parser_arguments(parser)
        parser.add_argument("-shuffle-input", action="store_true")
        parser.add_argument("-plot", type=str)
        parser.add_argument("-plot-duration", type=float, default=10)

    def __init__(self, parser):
        self.profiles_dir = "profiles/prediction"
        Experiment.__init__(self, parser)

    def run(self, student):
        self.student = student

        if self.args.shuffle_input:
            self.teacher = ShufflingTeacher(self.stimulus)
        else:
            self.teacher = LiveTeacher(self.stimulus)

        if self.args.train:
            self._train_model()
            save_model(self.student, self._model_path)

        elif self.args.plot:
            LearningPlotter(student, teacher, self.args.plot_duration).plot(self.args.plot)

        else:
            self.student = load_model(self._model_path)
        
            app = QtGui.QApplication(sys.argv)
            self.window = MainWindow(
                self, self._scene_class, ExperimentToolbar, self.args)
            self.window.show()
            app.exec_()

    def proceed(self):
        if self.teacher.collected_enough_training_data():
            inp = self.teacher.get_input()
            expected_output = self.teacher.get_output()
            self.student.train(inp, expected_output)
        self.teacher.proceed(self.time_increment)

        self.input = self.stimulus.get_value()
        self.output = self.student.process(self.input)

    def _train_model(self):
        print "training model..."
        t = 0
        time_increment = 1.0 / 50
        training_duration = self._training_duration()
        while t < training_duration:
            if self.teacher.collected_enough_training_data():
                inp = self.teacher.get_input()
                output = self.teacher.get_output()
                self.student.train(inp, output)
            self.teacher.proceed(time_increment)
            t += time_increment
        print "ok"
