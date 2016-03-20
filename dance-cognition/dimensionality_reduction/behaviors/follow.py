import numpy
from event import Event
from dimensionality_reduction.behavior import Behavior

class Follow(Behavior):
    def get_input(self):
        return self._experiment.entity.adapt_value_to_model(
            self._experiment.entity.get_value())

    def get_reduction(self):
        return self._experiment.student.transform(numpy.array([self._experiment.input]))[0]

    def proceed(self, time_increment):
        self._experiment.entity.proceed(time_increment)
        self._experiment.send_event_to_ui(Event(
                Event.CURSOR,
                self._experiment.entity.get_cursor() / self._experiment.entity.get_duration()))
        self._potentially_send_bvh_index_to_ui()

    def on_updated_cursor(self):
        self._potentially_send_bvh_index_to_ui()

    def _potentially_send_bvh_index_to_ui(self):
        if self._experiment.args.bvh:
            bvh_index = self._get_current_bvh_index()
            self._experiment.send_event_to_ui(Event(Event.BVH_INDEX, bvh_index))

    def _get_current_bvh_index(self):
        bvh_reader = self._experiment.bvh_reader.get_reader_at_time(
            self._experiment.entity.get_cursor())
        return bvh_reader.index
