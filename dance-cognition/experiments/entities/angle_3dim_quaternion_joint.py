from entities.angle_3dim_quaternion import *

class Entity(QuaternionEntity):
    def get_value(self):
        self.bvh_reader.set_skeleton_pose_from_frame(
            self.skeleton, self._t * self.args.bvh_speed)
        joint = self.skeleton.get_joint(self.args.joint)
        return quaternion_from_euler(
            *joint.rotation.angles,
             axes=joint.rotation.axes)

    def get_duration(self):
        return self.bvh_reader.get_duration() / self.args.bvh_speed
