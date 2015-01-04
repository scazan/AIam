from experiment import *
import math
from expmap import *

class Entity(BaseEntity):
    def get_value(self):
        self.bvh_reader.set_pose_from_time(
            self.pose, self._t * self.args.bvh_speed)
        joint = self.pose.get_joint(self.args.joint)
        return expmap_from_euler(
            *joint.rotation.angles,
             axes=joint.rotation.axes)

    def get_duration(self):
        return self.bvh_reader.get_duration() / self.args.bvh_speed
