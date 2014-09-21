from experiment import *
import numpy

class Entity(BaseEntity):
    def get_value(self):
        vertices = self.bvh_reader.get_skeleton_vertices(self._t * self.args.bvh_speed)
        normalized_vectors = numpy.array(
            [self.bvh_reader.normalize_vector(vertex)
             for vertex in vertices])
        return normalized_vectors.flatten()

    def process_io(self, value):
        normalized_vectors = value.reshape([self.bvh_reader.num_joints, 3])
        vertices = [self.bvh_reader.skeleton_scale_vector(vector)
                    for vector in normalized_vectors]
        return vertices
