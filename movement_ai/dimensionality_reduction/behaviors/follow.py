import numpy
from event import Event
from dimensionality_reduction.behavior import Behavior

class Follow(Behavior):
    def __init__(self, student, entity, bvh_reader):
        Behavior.__init__(self)
        self._student = student
        self._entity = entity
        self._bvh_reader = bvh_reader
        
    def get_input(self):
        return self._entity.adapt_value_to_model(self._entity.get_value())

    def on_input(self, input_):
        self._reduction = self._student.transform(numpy.array([input_]))[0]

    def proceed(self, time_increment):
        self._entity.proceed(time_increment)
        self.notify(Event(
                Event.CURSOR,
                self._entity.get_cursor() / self._entity.get_duration()))
        self._potentially_send_bvh_index_to_ui()

    def on_updated_cursor(self):
        self._potentially_send_bvh_index_to_ui()

    def _potentially_send_bvh_index_to_ui(self):
        if self._bvh_reader is not None:
            bvh_index = self._get_current_bvh_index()
            self.notify(Event(Event.BVH_INDEX, bvh_index))

    def _get_current_bvh_index(self):
        bvh_reader = self._bvh_reader.get_reader_at_time(self._entity.get_cursor())
        return bvh_reader.index
