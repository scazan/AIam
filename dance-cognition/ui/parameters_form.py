from PyQt4 import QtCore, QtGui
from parameters import *

SLIDER_PRECISION = 1000

class ParametersForm:
    def __init__(self, parameters, parent):
        layout = QtGui.QFormLayout()
        self._fields_by_name = {}
        for parameter in parameters:
            field = self._create_parameter_field(parameter)
            layout.addRow(QtGui.QLabel(parameter.name), field)
            self._fields_by_name[parameter.name] = field
        parent.addLayout(layout)

    def _create_parameter_field(self, parameter):
        if parameter.choices is not None:
            if parameter.choices.__class__ is ParameterFloatRange:
                field = Slider(parameter)
            else:
                field = ListChoice(parameter)
        elif parameter.type == str:
            field = LineEdit(parameter)
        elif parameter.type in [int, float]:
            field = LineEdit(parameter)
        else:
            raise Exception("don't know how to create field for %s" % parameter)
        field.update()
        return field

    def update_field(self, name):
        field = self._fields_by_name[name]
        field.update()

class Slider(QtGui.QSlider):
    def __init__(self, parameter):
        self._parameter = parameter
        QtGui.QSlider.__init__(self, QtCore.Qt.Horizontal)
        self.setRange(0, SLIDER_PRECISION)
        self.setSingleStep(1)
        self.sliderMoved.connect(lambda value: self._slider_value_changed(parameter, value))

    def _parameter_value_to_slider_value(self, parameter):
        return int((parameter.value() - parameter.choices.min_value) / \
            parameter.choices.range * SLIDER_PRECISION)

    def _slider_value_to_parameter_value(self, parameter, slider_value):
        return float(slider_value) / SLIDER_PRECISION * parameter.choices.range + \
            parameter.choices.min_value
        
    def _slider_value_changed(self, parameter, slider_value):
        value = self._slider_value_to_parameter_value(parameter, slider_value)
        parameter.set_value(value)

    def update(self):
        self.setValue(self._parameter_value_to_slider_value(self._parameter))

class ListChoice(QtGui.QComboBox):
    def __init__(self, parameter):
        self._parameter = parameter
        QtGui.QComboBox.__init__(self)
        for value in parameter.choices:
            self.addItem(value)
        self.activated.connect(
            lambda value: self._edited_choice_parameter(parameter, value))

    def _edited_choice_parameter(self, parameter, index):
        parameter.set_value(parameter.choices[index])

    def update(self):
        index = 0
        for value in self._parameter.choices:
            if self._parameter.value() == value:
                self.setCurrentIndex(index)
                return
            index += 1

class LineEdit(QtGui.QLineEdit):
    def __init__(self, parameter):
        self._parameter = parameter
        QtGui.QLineEdit.__init__(self)
        self.textEdited.connect(lambda value: self._edited_text_parameter(parameter, value))

    def _edited_text_parameter(self, parameter, string):
        if string == "":
            return
        if parameter.type == int:
            parameter.set_value(int(string))
        elif parameter.type == float:
            parameter.set_value(float(string))

    def update(self):
        self.setText(str(self._parameter.value()))
