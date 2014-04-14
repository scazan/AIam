from entities.point import *

class Entity(BaseEntity):
    def get_value(self):
        vertices = self.bvh_reader.get_skeleton_vertices(self._t * self.args.bvh_speed)
        hips = self.bvh_reader.normalize_vector(vertices[0])
        return hips

    def get_duration(self):
        return self.bvh_reader.get_duration() / args.bvh_speed