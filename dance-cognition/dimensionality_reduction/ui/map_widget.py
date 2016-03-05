from dimensionality_reduction_ui import *

SPLIT_SENSITIVITY = .2

class MapTab(ReductionTab, QtGui.QWidget):
    def __init__(self, parent, dimensions):
        ReductionTab.__init__(self, parent)
        QtGui.QWidget.__init__(self)
        self.student = parent.parent().student
        self._dimensions = dimensions
        self._map_layout = QtGui.QVBoxLayout()
        self._add_map_dimension_checkboxes()
        self._add_map_widget()
        self._map_layout.addStretch(1)
        self.setLayout(self._map_layout)

    def get_event_handlers(self):
        return self._map_widget.get_event_handlers()

    def set_path(self, path):
        self._map_widget.set_path(path)

    def get_normalized_reduction(self):
        return self._map_widget.get_reduction()

    def reduction_changed(self, reduction):
        self._reduction = reduction
        self._map_widget.set_reduction(reduction)

    def set_enabled(self, enabled):
        self._map_widget.set_enabled(enabled)

    def _add_map_widget(self):
        self._map_widget = MapWidget(self, self._dimensions)
        self._map_widget.setFixedSize(270, 270)
        self._map_layout.addWidget(self._map_widget)

    def _add_map_dimension_checkboxes(self):
        layout = QtGui.QHBoxLayout()
        self._map_dimension_checkboxes = []
        for n in range(self.student.n_components):
            checkbox = QtGui.QCheckBox()
            if n in self._dimensions:
                checkbox.setCheckState(QtCore.Qt.Checked)
            checkbox.stateChanged.connect(self._dimensions_changed)
            self._map_dimension_checkboxes.append(checkbox)
            layout.addWidget(checkbox)
        self._map_layout.addLayout(layout)

    def _dimensions_changed(self):
        checked_dimensions = filter(
            lambda n: self._map_dimension_checkboxes[n].checkState() == QtCore.Qt.Checked,
            range(self.student.n_components))
        if len(checked_dimensions) == 2:
            self._map_widget.set_dimensions(checked_dimensions)
            self._map_widget.set_reduction(self._reduction)

    def reduction_changed_interactively(self):
        self._reduction = self._map_widget.get_reduction()
        self._parent.reduction_changed_interactively(self)

    def update_qgl_widgets(self):
        self._map_widget.updateGL()

class MapWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent, dimensions):
        QtOpenGL.QGLWidget.__init__(self, parent)
        self._parent = parent
        self._student = parent.student
        self._observations_layer = Layer(self._render_observations)
        self.set_dimensions(dimensions)
        self._dragging = False
        self._enabled = False
        self._mode_specific_renderers = {
            modes.IMPROVISE: ImproviseMapViewRenderer(self),
            }

    def get_event_handlers(self):
        result = []
        for renderer in self._mode_specific_renderers.values():
            result += renderer.get_event_handlers().items()
        return result

    def set_dimensions(self, dimensions):
        self._dimensions = dimensions
        observations = self._student.normalized_observed_reductions[
            :,dimensions]
        self._split_into_segments(observations)
        self._reduction = None
        self._observations_layer.refresh()

    def _split_into_segments(self, observations):
        self._segments = []
        segment = []
        previous_observation = None
        for observation in observations:
            if previous_observation is not None and \
                    numpy.linalg.norm(observation - previous_observation) > SPLIT_SENSITIVITY:
                self._segments.append(segment)
                segment = []
            segment.append(observation)
            previous_observation = observation
        if len(segment) > 0:
            self._segments.append(segment)

    def set_reduction(self, reduction_all_dimensions):
        self._reduction_all_dimensions = reduction_all_dimensions
        self._reduction = reduction_all_dimensions[self._dimensions]

    def set_enabled(self, enabled):
        self._enabled = enabled

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 0.0)
        glClearAccum(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def resizeGL(self, window_width, window_height):
        self.window_width = window_width
        self.window_height = window_height
        if window_height == 0:
            window_height = 1
        self._margin = 0
        self._width = window_width - 2*self._margin
        self._height = window_height - 2*self._margin
        glViewport(0, 0, window_width, window_height)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glOrtho(0.0, self.window_width, self.window_height, 0.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glTranslatef(self._margin, self._margin, 0)
        self._observations_layer.draw()
        self._render_according_to_mode()
        if self._reduction is not None:
            self._render_reduction()

    def _render_according_to_mode(self):
        toolbar = self._parent.parent().parent().parent()
        mode = toolbar.get_mode()
        if mode in self._mode_specific_renderers:
            self._mode_specific_renderers[mode].render()

    def _render_observations(self):
        glColor4f(0, 0, 0, .1)
        glLineWidth(1.0)
        for segment in self._segments:
            self.render_line_strip(segment)

    def render_line_strip(self, segment):
        glBegin(GL_LINE_STRIP)
        for vertex in segment:
            glVertex2f(*self._vertex(*self._normalized_reduction_to_explored_range(vertex)))
        glEnd()

    def _render_reduction(self):
        glColor3f(0, 0, 0)
        glPointSize(5.0)
        glBegin(GL_POINTS)
        glVertex2f(*self._vertex(*self._normalized_reduction_to_explored_range(self._reduction)))
        glEnd()

    def _vertex(self, x, y):
        return x*self._width, y*self._height

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self._enabled:
            self._dragging = True

    def mouseReleaseEvent(self, event):
        self._dragging = False

    def mouseMoveEvent(self, event):
        if self._dragging:
            x = event.x()
            y = event.y()
            self._reduction[0] = self._parent.exploration_value_to_normalized_reduction_value(
                self._dimensions[0], float(x - self._margin) / self._width)
            self._reduction[1] = self._parent.exploration_value_to_normalized_reduction_value(
                self._dimensions[1], float(y - self._margin) / self._height)
            self._parent.reduction_changed_interactively()
            
    def get_reduction(self):
        reduction = self._reduction_all_dimensions
        reduction[self._dimensions[0]] = self._reduction[0]
        reduction[self._dimensions[1]] = self._reduction[1]
        return reduction

    def _normalized_reduction_to_explored_range(self, reduction):
        return numpy.array([
                self._normalized_reduction_value_to_explored_range(n, reduction[n])
                for n in range(2)])

    def _normalized_reduction_value_to_explored_range(self, n, value):
        return self._parent.normalized_reduction_value_to_exploration_value(
            self._dimensions[n], value)

class MapViewRenderer:
    def __init__(self, map_view):
        self.map_view = map_view

class ImproviseMapViewRenderer(MapViewRenderer):
    def __init__(self, *args, **kwargs):
        MapViewRenderer.__init__(self, *args, **kwargs)
        self._improvise_path = None

    def get_event_handlers(self):
        return {Event.IMPROVISE_PATH: self._set_improvise_path}

    def _set_improvise_path(self, event):
        self._improvise_path = numpy.array(event.content)

    def render(self):
        if self._improvise_path is not None:
            self._render_path(self._improvise_path)

    def _render_path(self, path):
        glPushAttrib(GL_ENABLE_BIT)
        glLineStipple(4, 0xAAAA)
        glEnable(GL_LINE_STIPPLE)
        glColor4f(0, 0, 0, .6)
        glLineWidth(2.0)
        self.map_view.render_line_strip(path)
        glPopAttrib()
