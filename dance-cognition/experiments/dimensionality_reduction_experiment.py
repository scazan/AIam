from experiment import *
from dimensionality_reduction_teacher import *

class DimensionalityReductionToolbar(ExperimentToolbar):
    def __init__(self, *args):
        ExperimentToolbar.__init__(self, *args)
        layout = QtGui.QVBoxLayout()
        self._sliders = []
        for n in range(self.experiment.student.n_components):
            slider = QtGui.QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, 1000)
            slider.setSingleStep(1)
            slider.setValue(500)
            layout.addWidget(slider)
            self._sliders.append(slider)
        self.setLayout(layout)

    def refresh(self):
        if not self.args.interactive_control:
            for n in range(self.experiment.student.n_components):
                self._sliders[n].setValue(
                    self._reduction_value_to_slider_value(n, self.experiment.reduction[n]))

    def _reduction_value_to_slider_value(self, n, value):
        range_n = self.experiment.student.reduction_range[n]
        return (value - range_n["min"]) / \
            (range_n["max"] - range_n["min"]) * 1000

    def _slider_value_to_reduction_value(self, n, value):
        range_n = self.experiment.student.reduction_range[n]
        return float(value) / 1000 * (range_n["max"] - range_n["min"]) + \
            range_n["min"]

    def get_reduction(self):
        return numpy.array(
            [self._slider_value_to_reduction_value(n, self._sliders[n].value())
             for n in range(self.experiment.student.n_components)])


class DimensionalityReductionExperiment(Experiment):
    @staticmethod
    def add_parser_arguments(parser):
        Experiment.add_parser_arguments(parser)
        parser.add_argument("-interactive-control", action="store_true")

    def __init__(self, scene, args):
        Experiment.__init__(self, scene, args)
        if self.args.model is None:
            self.args.model = "models/dimensionality_reduction/%s.model" % args.entity
        self.reduction = None

    def run(self, student, stimulus):
        self.stimulus = stimulus
        self.student = student

        if self.args.train:
            teacher = Teacher(stimulus, self.args.training_data_frame_rate)
            self._train_model(teacher)
            self.save_model(self.args.model)

        else:
            self.student = self.load_model(self.args.model)

            app = QtGui.QApplication(sys.argv)
            self.window = MainWindow(
                self, self._scene_class, DimensionalityReductionToolbar, self.args)
            self.window.show()
            app.exec_()

    def _train_model(self, teacher):
        print "training model..."
        self.student.fit(teacher.get_training_data())
        print "explained variance ratio: %s (sum %s)" % (
            self.student.explained_variance_ratio_, sum(self.student.explained_variance_ratio_))
        print "ok"

        print "probing model..."
        self.student.probe(teacher.get_training_data())
        print "ok"

    def proceed(self, time_increment):
        if self.args.interactive_control:
            self.reduction = self.window.toolbar.get_reduction()
        else:
            self.stimulus.proceed(time_increment)
            self.input = self.stimulus.get_value()
            self.reduction = self.student.transform(self.input)
        self.output = self.student.inverse_transform(self.reduction)
