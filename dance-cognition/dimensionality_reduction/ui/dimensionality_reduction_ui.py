from ..dimensionality_reduction_experiment import *
from ui.ui import *
from reduction_tab import ReductionTab
from map_widget import MapTab
from reduction_sliders import ReductionSliders
from .. import modes
from feature_sliders import FeatureSliders

REDUCTION_PLOT_PATH = "reduction.dat"
HTML5_TOOLBAR_HEIGHT = 250

class DimensionalityReductionMainWindow(MainWindow):
    @staticmethod
    def add_parser_arguments(parser):
        MainWindow.add_parser_arguments(parser)
        parser.add_argument("--html5-toolbar", action="store_true")

    def __init__(self, *args, **kwargs):
        MainWindow.__init__(self, *args, event_handlers={
                Event.REDUCTION: self._handle_reduction,
                Event.MODE: self._set_mode,
                Event.IMPROVISER_PATH: self._set_improviser_path,
                Event.VELOCITY: self._set_velocity,
                Event.CURSOR: self._set_cursor,
                Event.BVH_INDEX: self._update_bvh_selector,
                Event.PARAMETER: self._received_parameter,
                Event.FEATURES: self._handle_features,
                Event.TARGET_FEATURES: self._handle_target_features,
                }, **kwargs)
        self._add_toggleable_action(
            '&Plot reduction', self._start_plot_reduction,
            '&Stop plot', self._stop_plot_reduction,
            False, 'F1')
        self._reduction_plot = None
        self._add_show_reduction_action()
        self._create_improvisation_menu()
        if self.args.html5_toolbar:
            self._add_html5_toolbar()

    def _received_parameter(self, event):
        self.toolbar.received_parameter(event)

    def _add_show_reduction_action(self):
        action = QtGui.QAction('Show normalized reduction', self)
        action.triggered.connect(self._show_normalized_reduction)
        self._main_menu.addAction(action)

    def _create_improvisation_menu(self):
        self._improvisation_menu = self._menu_bar.addMenu("Improvisation")
        self._add_abort_path_action()

    def _add_abort_path_action(self):
        action = QtGui.QAction('Abort path', self)
        action.setShortcut('F12')
        action.triggered.connect(lambda: self.send_event(Event(Event.ABORT_PATH)))
        self._improvisation_menu.addAction(action)

    def _show_normalized_reduction(self):
        normalized_reduction = self.student.normalize_reduction(self.reduction)
        print ",".join([str(v) for v in normalized_reduction])

    def _add_html5_toolbar(self):
        from PyQt4.QtCore import QUrl
        from PyQt4.QtWebKit import QWebView, QWebSettings
        view = QWebView()
        view.load(QUrl("dimensionality_reduction/html5/index.html?stylesheet=ui_720p"))
        view.show()
        view.setFixedSize(self.args.preferred_width, HTML5_TOOLBAR_HEIGHT)
        self.setFixedSize(self.args.preferred_width, self.args.preferred_height)
        self.outer_vertical_layout.addWidget(view)
        view.page().settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)

    def _handle_reduction(self, event):
        self.reduction = event.content
        if self._reduction_plot:
            print >>self._reduction_plot, " ".join([
                    str(v) for v in self.student.normalize_reduction(self.reduction)])
        self.toolbar.on_received_reduction_from_backend(self.reduction)

    def _start_plot_reduction(self):
        self._reduction_plot = open(REDUCTION_PLOT_PATH, "w")
        print "plotting reduction"

    def _stop_plot_reduction(self):
        self._reduction_plot.close()
        self._reduction_plot = None
        print "saved reduction data to %s" % REDUCTION_PLOT_PATH

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

    def _update_bvh_selector(self, event):
        self.toolbar.bvh_selector.setCurrentIndex(event.content)

    def update_qgl_widgets(self):
        MainWindow.update_qgl_widgets(self)
        self.toolbar.update_qgl_widgets()

    def _handle_features(self, event):
        self.toolbar.on_received_features_from_backend(event)

    def _handle_target_features(self, event):
        self.toolbar.on_received_target_features_from_backend(event)

class DimensionalityReductionToolbar(ExperimentToolbar):
    def __init__(self, *args):
        ExperimentToolbar.__init__(self, *args)
        self._layout = QtGui.QVBoxLayout()
        self._add_mode_tabs()
        self._add_reduction_tabs()
        if self.args.enable_features:
            self._add_features_tab_widgets()
        self.setLayout(self._layout)
        self.set_mode(self.args.mode)

    def set_mode(self, mode):
        mode_tab = self._mode_tabs[mode]
        self._changing_mode_non_interactively = True
        self.tabs.setCurrentWidget(mode_tab)
        self._changing_mode_non_interactively = False

    def _add_mode_tabs(self):
        self.tabs = QtGui.QTabWidget()
        self._mode_tabs = {}
        self._add_follow_tab()
        self._add_explore_tab()
        self._add_improvise_tab()
        self.tabs.currentChanged.connect(self._changed_mode_tab)
        self._layout.addWidget(self.tabs)
        self._changing_mode_non_interactively = False

    def _changed_mode_tab(self):
        exploring = (self.tabs.currentWidget() == self.explore_tab)
        for n in range(self._reduction_tabs.count()):
            tab = self._reduction_tabs.widget(n)
            tab.set_enabled(exploring)
        if not self._changing_mode_non_interactively:
            self.parent().send_event(
                Event(Event.MODE, self.tabs.currentWidget()._mode_id))

    def _add_follow_tab(self):
        self.follow_tab = ModeTab(modes.FOLLOW)
        self._follow_tab_layout = QtGui.QVBoxLayout()
        if hasattr(self.parent().entity, "get_duration"):
            self._add_cursor_slider()
        if self.args.bvh:
            self._add_bvh_selector()
        self._add_velocity_view()
        self._follow_tab_layout.addStretch(1)
        self.follow_tab.setLayout(self._follow_tab_layout)
        self.tabs.addTab(self.follow_tab, "Follow")
        self._mode_tabs[modes.FOLLOW] = self.follow_tab

    def _add_cursor_slider(self):
        self.cursor_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.cursor_slider.setRange(0, SLIDER_PRECISION)
        self.cursor_slider.setSingleStep(1)
        self.cursor_slider.setValue(0.0)
        self.cursor_slider.valueChanged.connect(self._cursor_changed)
        self._follow_tab_layout.addWidget(self.cursor_slider)

    def _add_bvh_selector(self):
        self.bvh_selector = QtGui.QComboBox()
        for bvh_reader in self.parent().entity.bvh_reader.get_readers():
            self.bvh_selector.addItem(bvh_reader.filename)
        self._follow_tab_layout.addWidget(self.bvh_selector)

    def _cursor_changed(self, value):
        self.parent().send_event(Event(
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
        self._mode_tabs[modes.EXPLORE] = self.explore_tab

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
        self._improviser_params.add_notifier(self.parent().client)
        self._improviser_params_form = self.add_parameter_fields(
            self._improviser_params, self._improvise_tab_layout)
        self.improvise_tab.setLayout(self._improvise_tab_layout)
        self.tabs.addTab(self.improvise_tab, "Improvise")
        self._mode_tabs[modes.IMPROVISE] = self.improvise_tab

    def received_parameter(self, event):
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
        normalized_reduction = source_tab.get_normalized_reduction()
        reduction = self.parent().student.unnormalize_reduction(normalized_reduction)
        self.parent().send_event(Event(Event.REDUCTION, reduction))
        self.parent().reduction = reduction
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

    def on_received_reduction_from_backend(self, reduction):
        self._set_reduction(reduction)

    def update_qgl_widgets(self):
        self._reduction_tabs.currentWidget().update_qgl_widgets()

    def _add_features_tab_widgets(self):
        self._add_output_features_tab_widget()
        self._add_input_features_tab_widget()

    def _add_output_features_tab_widget(self):
        self._output_features_tab_widget = QtGui.QTabWidget()
        self._output_features_sliders = FeatureSliders(self, self.parent().entity.feature_extractor)
        self._output_features_tab_widget.addTab(self._output_features_sliders, "Output features")
        self._layout.addWidget(self._output_features_tab_widget)

    def _add_input_features_tab_widget(self):
        self._target_features_tab_widget = QtGui.QTabWidget()
        self._target_features_sliders_tab = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        self._target_features_sliders_tab.setLayout(layout)
        self._target_features_sliders = FeatureSliders(self, self.parent().entity.feature_extractor)
        layout.addLayout(self._create_target_features_checkbox_layout())
        layout.addWidget(self._target_features_sliders)
        self._target_features_tab_widget.addTab(self._target_features_sliders_tab, "Target features")
        self._layout.addWidget(self._target_features_tab_widget)

    def _create_target_features_checkbox_layout(self):
        layout = QtGui.QHBoxLayout()
        self._target_features_checkbox = QtGui.QCheckBox()
        self._target_features_checkbox.stateChanged.connect(self._target_features_checkbox_changed)
        label = QtGui.QLabel("Enable target")
        layout.addWidget(self._target_features_checkbox)
        layout.addWidget(label)
        layout.addStretch(1)
        return layout

    def _target_features_checkbox_changed(self):
        enabled = (self._target_features_checkbox.checkState() == QtCore.Qt.Checked)
        self._target_features_sliders.set_enabled(enabled)
        if enabled:
            self.features_changed_interactively()
        else:
            self.parent().send_event(Event(Event.TARGET_FEATURES, None))
            
    def on_received_features_from_backend(self, event):
        features = event.content
        self._output_features_sliders.features_changed(features)
            
    def on_received_target_features_from_backend(self, event):
        features = event.content
        self._target_features_sliders.features_changed(features)

    def features_changed_interactively(self):
        features = self._target_features_sliders.get_features()
        self.parent().send_event(Event(Event.TARGET_FEATURES, features))

class ModeTab(QtGui.QWidget):
    def __init__(self, mode_id):
        self._mode_id = mode_id
        QtGui.QWidget.__init__(self)
