import unittest
from bvh.bvh_reader.bvh_collection import BvhCollection

class MockScaleInfo:
    min_x = 0
    min_y = 0
    min_z = 0
    max_x = 0
    max_y = 0
    max_z = 0

class MockJointDefinition:
    def __init__(self, name, joints_with_static_rotation):
        self.name = name
        self.has_static_rotation = (self.name in joints_with_static_rotation)
        self.child_definitions = []

class MockHierarchy:
    def __init__(self, joints_with_static_rotation):
        self._joint_definitions = {}
        self._joints_with_static_rotation = joints_with_static_rotation
        self._add_joint_definition("Hip")
        self._add_joint_definition("LArm")
        self._add_joint_definition("RArm")
        self._root_joint_definition = self.get_joint_definition("Hip")
        self._root_joint_definition.child_definitions = [
            self.get_joint_definition("LArm"),
            self.get_joint_definition("RArm"),
            ]

    def _add_joint_definition(self, name):
        self._joint_definitions[name] = MockJointDefinition(name, self._joints_with_static_rotation)

    def get_root_joint_definition(self):
        return self._root_joint_definition

    def get_joint_definition(self, name):
        return self._joint_definitions[name]

class MockBvhReader:
    def __init__(self, duration=1.0, num_frames=1, joints_with_static_rotation=[]):
        self._duration = duration
        self._num_frames = num_frames
        self._scale_info = MockScaleInfo()
        self._hierarchy = MockHierarchy(joints_with_static_rotation)

    def read(self):
        pass

    def get_duration(self):
        return self._duration

    def get_num_frames(self):
        return self._num_frames

    def get_hierarchy(self):
        return self._hierarchy

class TestedBvhCollection(BvhCollection):
    def __init__(self, bvh_readers):
        self._init_readers(bvh_readers)

class BvhCollectionTestCase(unittest.TestCase):
    def test_duration_is_sum(self):
        self._given_bvh_reader(duration=10)
        self._given_bvh_reader(duration=5)
        self._when_creating_bvh_collection()
        self._then_duration_is(15)

    def setUp(self):
        self._bvh_readers = []

    def _given_bvh_reader(self, **kwargs):
        self._bvh_readers.append(MockBvhReader(**kwargs))

    def _when_creating_bvh_collection(self):
        self._bvh_collection = TestedBvhCollection(self._bvh_readers)
        self._bvh_collection.read()

    def _then_duration_is(self, expected_duration):
        self.assertEquals(expected_duration, self._bvh_collection.get_duration())

    def test_static_rotation_is_intersection(self):
        self._given_bvh_reader(joints_with_static_rotation=["LArm", "RArm", "Hip"])
        self._given_bvh_reader(joints_with_static_rotation=["LArm", "RArm"])
        self._given_bvh_reader(joints_with_static_rotation=["LArm"])
        self._when_creating_bvh_collection()
        self._then_joints_with_static_rotations(["LArm"])

    def _then_joints_with_static_rotations(self, expected_joints):
        hierarchy = self._bvh_collection.get_hierarchy()
        actual_joints = self._get_joints_with_static_rotation(
            hierarchy.get_root_joint_definition())
        self.assertItemsEqual(expected_joints, actual_joints)

    def _get_joints_with_static_rotation(self, joint_definition):
        result = set()
        if joint_definition.has_static_rotation:
            result.add(joint_definition.name)
        for child_definition in joint_definition.child_definitions:
            child_result = self._get_joints_with_static_rotation(child_definition)
            result = result.union(child_result)
        return result
