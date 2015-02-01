import bvh_reader
from numpy import array

class BvhCollection:
    def __init__(self, filenames):
        self._readers = [bvh_reader.BvhReader(filename) for filename in filenames]
        self._base_reader = self._readers[0]

    def read(self):
        self._read_bvhs()
        self._set_scale_info()

    def _read_bvhs(self):
        self._duration = 0
        for reader in self._readers:
            reader.read()
            reader.start_time = self._duration
            reader.end_time = self._duration + reader.get_duration()
            self._duration += reader.get_duration()

    def _set_scale_info(self):
        self._scale_info = bvh_reader.ScaleInfo()
        for reader in self._readers:
            self._scale_info.update_with_vector(
                reader._scale_info.min_x,
                reader._scale_info.min_y,
                reader._scale_info.min_z)
            self._scale_info.update_with_vector(
                reader._scale_info.max_x,
                reader._scale_info.max_y,
                reader._scale_info.max_z)
        self._scale_info.update_scale_factor()

    def get_frame_time(self):
        return self._base_reader.frame_time

    def get_duration(self):
        return self._duration

    def set_pose_from_time(self, pose, t):
        for reader in self._readers:
            if reader.start_time <= t and t < reader.end_time:
                reader.set_pose_from_time(pose, t - reader.start_time)
                return
        raise Exception("set_pose_from_time failed for t=%s" % t)

    def normalize_vector(self, v):
        return array([
            (v[0] - self._scale_info.min_x) / self._scale_info.scale_factor * 2 - 1,
            (v[1] - self._scale_info.min_y) / self._scale_info.scale_factor * 2 - 1,
            (v[2] - self._scale_info.min_z) / self._scale_info.scale_factor * 2 - 1])

    def skeleton_scale_vector(self, v):
        return array([
            (v[0] + 1) / 2 * self._scale_info.scale_factor + self._scale_info.min_x,
            (v[1] + 1) / 2 * self._scale_info.scale_factor + self._scale_info.min_y,
            (v[2] + 1) / 2 * self._scale_info.scale_factor + self._scale_info.min_z])

    def get_hierarchy(self, *args, **kwargs):
        return self._base_reader.get_hierarchy(*args, **kwargs)

    def vertices_to_edges(self, *args, **kwargs):
        return self._base_reader.vertices_to_edges(*args, **kwargs)
