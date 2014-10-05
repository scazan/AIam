from PyQt4 import QtCore, QtGui
from parameters import *

SLIDER_PRECISION = 1000

class ParametersForm:
    def __init__(self, parameters, parent):
        layout = QtGui.QFormLayout()
        for parameter in parameters:
            field = self._create_parameter_field(parameter)
            layout.addRow(QtGui.QLabel(parameter.name), field)
        parent.addLayout(layout)

    def _create_parameter_field(self, parameter):
        if parameter.choices is not None:
            if parameter.choices.__class__ is ParameterFloatRange:
                return Slider(parameter)
            else:
                return ListChoice(parameter)
        elif parameter.type == str:
            return LineEdit(parameter)
        elif parameter.type in [int, float]:
            return LineEdit(parameter)
        else:
            raise Exception("don't know how to create field for %s" % parameter)

class Slider(QtGui.QSlider):
    def __init__(self, parameter):
        QtGui.QSlider.__init__(self, QtCore.Qt.Horizontal)
        self.setRange(0, SLIDER_PRECISION)
        self.setSingleStep(1)
        self.setValue(self._parameter_value_to_slider_value(parameter))
        self.valueChanged.connect(lambda value: self._slider_value_changed(parameter, value))

    def _parameter_value_to_slider_value(self, parameter):
        return int((parameter.value() - parameter.choices.min_value) / \
            parameter.choices.range * SLIDER_PRECISION)

    def _slider_value_to_parameter_value(self, parameter, slider_value):
        return float(slider_value) / SLIDER_PRECISION * parameter.choices.range + \
            parameter.choices.min_value
        
    def _slider_value_changed(self, parameter, slider_value):
        value = self._slider_value_to_parameter_value(parameter, slider_value)
        parameter.set_value(value)

class ListChoice(QtGui.QComboBox):
    def __init__(self, parameter):
        QtGui.QComboBox.__init__(self)
        index = 0
        default_index = 0
        for value in parameter.choices:
            self.addItem(value)
            if parameter.default == value:
                default_index = index
            index += 1
            self.setCurrentIndex(default_index)
        self.currentIndexChanged.connect(
            lambda value: self._edited_choice_parameter(parameter, value))

    def _edited_choice_parameter(self, parameter, index):
        parameter.set_value(parameter.choices[index])

class LineEdit(QtGui.QLineEdit):
    def __init__(self, parameter):
        QtGui.QLineEdit.__init__(self, str(parameter.default))
        self.textEdited.connect(lambda value: self._edited_text_parameter(parameter, value))

    def _edited_text_parameter(self, parameter, string):
        if string == "":
            return
        if parameter.type == int:
            parameter.set_value(int(string))
        elif parameter.type == float:
            parameter.set_value(float(string))
