from experiment import *

class Entity(BaseEntity):
    def get_value(self):
        self.bvh_reader.set_pose_from_time(self.pose, self._t * self.args.bvh_speed)
        vertices = self.pose.get_vertices()
        root_joint = self.bvh_reader.normalize_vector(vertices[0])
        return root_joint

    def get_duration(self):
        return self.bvh_reader.get_duration() / args.bvh_speed
