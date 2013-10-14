from stimulus import Stimulus
from skeleton_hierarchy_parameters import *

class BvhStimulus(Stimulus):
    def __init__(self, bvh_reader, speed):
        Stimulus.__init__(self)
        self.bvh_reader = bvh_reader
        self.speed = speed
        self.skeleton_parametrization = SkeletonHierarchyParametrization(bvh_reader)

    def filename(self):
        return self.bvh_reader.filename

    def get_value(self):
        hips = self.bvh_reader.get_hips(self._t * self.speed)
        return self.skeleton_parametrization.joint_to_parameters(hips)

    def get_duration(self):
        return self.bvh_reader.get_duration()
