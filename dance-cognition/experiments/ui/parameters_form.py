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
                return self._create_slider_field(parameter)
            else:
                return self._create_list_choice_field(parameter)
        elif parameter.type == str:
            field = QtGui.QLineEdit(parameter.default)
        elif parameter.type in [int, float]:
            field = QtGui.QLineEdit(str(parameter.default))
            field.textEdited.connect(lambda value: self._edited_text_parameter(parameter, value))
        else:
            raise Exception("don't know how to create field for %s" % parameter)
        return field

    def _create_list_choice_field(self, parameter):
        index = 0
        default_index = 0
        field = QtGui.QComboBox()
        for value in parameter.choices:
            field.addItem(value)
            if parameter.default == value:
                default_index = index
            index += 1
            field.setCurrentIndex(default_index)
        field.currentIndexChanged.connect(
            lambda value: self._edited_choice_parameter(parameter, value))
        return field

    def _create_slider_field(self, parameter):
        field = QtGui.QSlider(QtCore.Qt.Horizontal)
        field.setRange(0, SLIDER_PRECISION)
        field.setSingleStep(1)
        field.setValue(self._parameter_value_to_slider_value(parameter))
        field.valueChanged.connect(lambda value: self._slider_value_changed(parameter, value))
        return field

    def _parameter_value_to_slider_value(self, parameter):
        return int((parameter.value() - parameter.choices.min_value) / \
            parameter.choices.range * SLIDER_PRECISION)

    def _slider_value_to_parameter_value(self, parameter, slider_value):
        return float(slider_value) / SLIDER_PRECISION * parameter.choices.range + \
            parameter.choices.min_value
        
    def _slider_value_changed(self, parameter, slider_value):
        value = self._slider_value_to_parameter_value(parameter, slider_value)
        parameter.set_value(value)

    def _edited_text_parameter(self, parameter, string):
        if string == "":
            return
        if parameter.type == int:
            parameter.set_value(int(string))
        elif parameter.type == float:
            parameter.set_value(float(string))

    def _edited_choice_parameter(self, parameter, index):
        parameter.set_value(parameter.choices[index])
