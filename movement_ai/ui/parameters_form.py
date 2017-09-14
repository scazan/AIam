from PyQt4 import QtCore, QtGui
from parameters import *

SLIDER_PRECISION = 1000

class ParametersForm:
    def __init__(self, parameters, parent=None, layout=None, row_offset=0):
        if layout is None:
            self._layout = QtGui.QGridLayout()
        else:
            self._layout = layout
        self._field_widgets = {}
        self._value_widgets = {}
        self._row = row_offset
        for parameter in parameters:
            name_widget = QtGui.QLabel(parameter.name)
            field_widget = self._create_parameter_field(parameter)
            self._field_widgets[parameter.name] = field_widget
            self._add_widget(name_widget, 0)
            if isinstance(field_widget, Slider):
                value_widget = QtGui.QLabel()
                value_widget.setFixedWidth(30)
                self._add_widget(field_widget, 1)
                self._add_widget(value_widget, 2)
                self._value_widgets[parameter.name] = value_widget
                self._update_value_widget(parameter)
            else:
                self._add_widget(field_widget, 1, column_span=2)                
            self._row += 1
        if layout is None:
            parent.addLayout(self._layout)

    def _add_widget(self, widget, column, row_span=1, column_span=1):
        self._layout.addWidget(widget, self._row, column, row_span, column_span)

    def _create_parameter_field(self, parameter):
        if parameter.choices is not None:
            if parameter.choices.__class__ is ParameterFloatRange:
                field = Slider(self, parameter)
            else:
                field = ListChoice(parameter)
        elif parameter.type == str:
            field = LineEdit(parameter)
        elif parameter.type in [int, float]:
            field = LineEdit(parameter)
        else:
            raise Exception("don't know how to create field for %s" % parameter)
        field.update_to_reflect_value()
        return field

    def update_field_to_reflect_changed_value(self, parameter):
        field_widget = self._field_widgets[parameter.name]
        field_widget.update_to_reflect_value()
        self.value_changed(parameter)

    def value_changed(self, parameter):
        self._update_value_widget(parameter)

    def _update_value_widget(self, parameter):
        if parameter.name in self._value_widgets:
            value_widget = self._value_widgets[parameter.name]
            value_widget.setText("%.2f" % parameter.value())

class Slider(QtGui.QSlider):
    def __init__(self, form, parameter):
        self._form = form
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
        self._form.value_changed(parameter)

    def update_to_reflect_value(self):
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

    def update_to_reflect_value(self):
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

    def update_to_reflect_value(self):
        self.setText(str(self._parameter.value()))
