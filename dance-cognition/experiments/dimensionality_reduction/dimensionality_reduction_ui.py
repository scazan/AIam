from dimensionality_reduction_experiment import *
from ui.ui import *
from reduction_tab import ReductionTab
from map_widget import MapTab
from reduction_sliders import ReductionSliders
import modes

class DimensionalityReductionMainWindow(MainWindow):
    def __init__(self, *args, **kwargs):
        MainWindow.__init__(self, *args, **kwargs)
        self.add_event_handler(Event.MODE, self._set_mode)
        self.add_event_handler(Event.IMPROVISER_PATH, self._set_improviser_path)
        self.add_event_handler(Event.VELOCITY, self._set_velocity)
        self.add_event_handler(Event.CURSOR, self._set_cursor)
        self._add_toggleable_action(
            '&Plot reduction', self._start_plot_reduction,
            '&Stop plot', self._stop_plot_reduction,
            False, 'F1')

    def _set_mode(self, event):
        self.toolbar.set_mode(event.content)

    def _set_improviser_path(self, event):
        if self.toolbar.map_tab:
            self.toolbar.map_tab.set_path(numpy.array(event.content))

    def _set_velocity(self, event):
        self.toolbar.velocity_label.setText("%.3f" % event.content)

    def _set_cursor(self, event):
        if hasattr(self.toolbar, "cursor_slider"):
            self.toolbar.cursor_slider.setValue(event.content * SLIDER_PRECISION)

class DimensionalityReductionToolbar(ExperimentToolbar):
    def __init__(self, *args):
        ExperimentToolbar.__init__(self, *args)
        self._layout = QtGui.QVBoxLayout()
        self._add_mode_tabs()
        self._add_reduction_tabs()
        self.setLayout(self._layout)
        self.set_mode(self.args.mode)

    def set_mode(self, mode):
        if mode == modes.IMPROVISE:
            self.tabs.setCurrentWidget(self.improvise_tab)
        elif mode == modes.EXPLORE:
            self.tabs.setCurrentWidget(self.explore_tab)
        elif mode == modes.FOLLOW:
            self.tabs.setCurrentWidget(self.follow_tab)
        else:
            raise Exception("unknown mode %r" % mode)

    def _add_mode_tabs(self):
        self.tabs = QtGui.QTabWidget()
        self._add_follow_tab()
        self._add_explore_tab()
        self._add_improvise_tab()
        self.tabs.currentChanged.connect(self._changed_mode_tab)
        self._layout.addWidget(self.tabs)

    def _changed_mode_tab(self):
        exploring = (self.tabs.currentWidget() == self.explore_tab)
        for n in range(self._reduction_tabs.count()):
            tab = self._reduction_tabs.widget(n)
            tab.set_enabled(exploring)
        self.parent().client.send_event(
            Event(Event.MODE, self.tabs.currentWidget()._mode_id))

    def _add_follow_tab(self):
        self.follow_tab = ModeTab(modes.FOLLOW)
        self._follow_tab_layout = QtGui.QVBoxLayout()
        if hasattr(self.parent().entity, "get_duration"):
            self._add_cursor_slider()
        self._add_velocity_view()
        self._follow_tab_layout.addStretch(1)
        self.follow_tab.setLayout(self._follow_tab_layout)
        self.tabs.addTab(self.follow_tab, "Follow")

    def _add_cursor_slider(self):
        self.cursor_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.cursor_slider.setRange(0, SLIDER_PRECISION)
        self.cursor_slider.setSingleStep(1)
        self.cursor_slider.setValue(0.0)
        self.cursor_slider.sliderMoved.connect(self._cursor_changed)
        self._follow_tab_layout.addWidget(self.cursor_slider)

    def _cursor_changed(self, value):
        self.parent().client.send_event(Event(
                Event.SET_CURSOR,
                float(value) / SLIDER_PRECISION * self.parent().entity.get_duration()))

    def _add_velocity_view(self):
        layout = QtGui.QHBoxLayout()
        layout.addWidget(QtGui.QLabel("Input velocity: "))
        self.velocity_label = QtGui.QLabel("")
        layout.addWidget(self.velocity_label)
        self._follow_tab_layout.addLayout(layout)

    def _add_explore_tab(self):
        self.explore_tab = ModeTab(modes.EXPLORE)
        self._explore_tab_layout = QtGui.QVBoxLayout()
        self._add_random_button()
        self._add_deviate_button()
        self._explore_tab_layout.addStretch(1)
        self.explore_tab.setLayout(self._explore_tab_layout)
        self.tabs.addTab(self.explore_tab, "Explore")

    def _add_random_button(self):
        button = QtGui.QPushButton("Random", self)
        button.clicked.connect(self._set_random_reduction)
        self._explore_tab_layout.addWidget(button)

    def _add_deviate_button(self):
        layout = QtGui.QHBoxLayout()
        self.deviation_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.deviation_slider.setRange(0, SLIDER_PRECISION)
        self.deviation_slider.setSingleStep(1)
        self.deviation_slider.setValue(0.0)
        layout.addWidget(self.deviation_slider)
        button = QtGui.QPushButton("Deviate", self)
        button.clicked.connect(self._set_deviated_reduction)
        layout.addWidget(button)
        self._explore_tab_layout.addLayout(layout)

    def _add_improvise_tab(self):
        self.improvise_tab = ModeTab(modes.IMPROVISE)
        self._improvise_tab_layout = QtGui.QVBoxLayout()
        self._improviser_params = ImproviserParameters()
        self.parent().add_event_handler(Event.PARAMETER, self._received_parameter)
        self._improviser_params.add_notifier(self.parent().client)
        self._improviser_params_form = self.add_parameter_fields(
            self._improviser_params, self._improvise_tab_layout)
        self.improvise_tab.setLayout(self._improvise_tab_layout)
        self.tabs.addTab(self.improvise_tab, "Improvise")

    def _received_parameter(self, event):
        self._improviser_params.handle_event(event)
        self._improviser_params_form.update_field(event.content["name"])

    def _add_reduction_tabs(self):
        self._set_exploration_ranges()
        self._reduction_tabs = QtGui.QTabWidget()
        if self.parent().student.n_components >= 2:
            self._add_map_tab()
        else:
            self.map_tab = None
        self._add_reduction_sliders_tab()
        self._layout.addWidget(self._reduction_tabs)

    def _add_reduction_sliders_tab(self):
        self.reduction_sliders_tab = ReductionSliders(self)
        self._reduction_tabs.addTab(self.reduction_sliders_tab, "Orthogonal control")

    def _add_map_tab(self):
        self._map_dimensions = [0,1]
        self.map_tab = MapTab(self, self._map_dimensions)
        self._reduction_tabs.addTab(self.map_tab, "2D map")

    def _set_random_reduction(self):
        for n in range(self.parent().student.n_components):
            self._set_random_reduction_n(
                n, self.parent().student.reduction_range[n])

    def _set_random_reduction_n(self, n, reduction_range):
        self.reduction_sliders_tab.slider(n).setValue(
            self._normalized_reduction_value_to_slider_value(
                n, random.uniform(reduction_range["explored_min"],
                                  reduction_range["explored_max"])))

    def _set_deviated_reduction(self):
        random_observation = self.parent().entity.get_random_value()
        undeviated_reduction = self.parent().student.transform(numpy.array([
                    random_observation]))[0]
        deviated_reduction = undeviated_reduction + self._random_deviation()
        self._set_reduction(deviated_reduction)

    def _random_deviation(self):
        return [self._random_deviation_n(n)
                for n in range(self.parent().student.n_components)]
    
    def _random_deviation_n(self, n):
        reduction_range = self.parent().student.reduction_range[n]
        max_deviation = float(self.deviation_slider.value()) / SLIDER_PRECISION \
            * (reduction_range["max"] - reduction_range["min"])
        return random.uniform(-max_deviation, max_deviation)

    def _set_reduction(self, reduction):
        normalized_reduction = self.parent().student.normalize_reduction(reduction)
        self._update_current_reduction_widget(normalized_reduction)

    def _update_current_reduction_widget(self, normalized_reduction):
        self._reduction_tabs.currentWidget().reduction_changed(normalized_reduction)

    def refresh(self):
        if self.tabs.currentWidget() != self.explore_tab:
            normalized_reduction = self.parent().student.normalize_reduction(
                self.parent().reduction)
            self._update_current_reduction_widget(normalized_reduction)

    def reduction_changed_interactively(self, source_tab):
        normalized_reduction = self.parent().student.normalize_reduction(
            self.parent().reduction)
        for n in range(self._reduction_tabs.count()):
            tab = self._reduction_tabs.widget(n)
            if tab != source_tab:
                tab.reduction_changed(normalized_reduction)

    def get_reduction(self):
        return self.parent().student.unnormalize_reduction(
            self._reduction_tabs.currentWidget().get_normalized_reduction())
        
    def _set_exploration_ranges(self):
        for n in range(self.parent().student.n_components):
            self._set_exploration_range(self.parent().student.reduction_range[n])

    def _set_exploration_range(self, reduction_range):
        reduction_range["explored_range"] = (1.0 + self.parent().args.explore_beyond_observations)
        reduction_range["explored_min"] = .5 - reduction_range["explored_range"]/2
        reduction_range["explored_max"] = .5 + reduction_range["explored_range"]/2

class ModeTab(QtGui.QWidget):
    def __init__(self, mode_id):
        self._mode_id = mode_id
        QtGui.QWidget.__init__(self)
