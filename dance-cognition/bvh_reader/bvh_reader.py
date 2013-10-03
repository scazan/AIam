# adopted from BVHplay (http://sourceforge.net/projects/bvhplay)

import cgkit.bvh
from geo import *
from numpy import array, dot
import numpy

class joint:
    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.children = []
        self.channels = []
        self.hasparent = 0
        self.parent = 0
        self.transposition = array([0.,0.,0.])
        self.transposition_matrix = array([
            [0.,0.,0.,0.],
            [0.,0.,0.,0.],
            [0.,0.,0.,0.],
            [0.,0.,0.,0.] ])

    def addchild(self, childjoint):
        self.children.append(childjoint)
        childjoint.hasparent = 1
        childjoint.parent = self

    def get_vertex(self):
        return vertex(
            self.worldpos[0],
            self.worldpos[1],
            self.worldpos[2])

    def get_vertices(self):
        result = []
        self.add_vertices_recurse(result)
        return result

    def add_vertices_recurse(self, vertices):
        vertices.append(self.get_vertex())
        for child in self.children:
            child.add_vertices_recurse(vertices)

    def populate_edges_from_vertices_recurse(self, vertices, edgelist):
        if self.hasparent:
            new_edge = edge(
              vertices[self.parent.index],
              vertices[self.index])
            edgelist.append(new_edge)

        for child in self.children:
            child.populate_edges_from_vertices_recurse(vertices, edgelist)



class skeleton:
    def __init__(self, hips, keyframes, num_frames=0, dt=.033333333):
        self.hips = hips
        self.keyframes = keyframes
        self.num_frames = num_frames
        self.dt = dt

# Precompute hips min and max values in all 3 dimensions.
# First determine how far into a keyframe we need to look to find the
# XYZ hip positions
        offset = 0
        for channel in self.hips.channels:
            if(channel == "Xposition"): xoffset = offset
            if(channel == "Yposition"): yoffset = offset
            if(channel == "Zposition"): zoffset = offset
            offset += 1
        self.minx = 999999999999
        self.miny = 999999999999
        self.minz = 999999999999
        self.maxx = -999999999999
        self.maxy = -999999999999
        self.maxz = -999999999999
# We can't just look at the keyframe values, we also have to correct
# by the static hips OFFSET value, since sometimes this can be quite
# large.  I feel it's bad BVH file form to have a non-zero HIPS offset
# position, but there are definitely files that do this.
        xcorrect = self.hips.transposition[0]
        ycorrect = self.hips.transposition[1]
        zcorrect = self.hips.transposition[2]

        for keyframe in self.keyframes:
            x = keyframe[xoffset] + xcorrect
            y = keyframe[yoffset] + ycorrect
            z = keyframe[zoffset] + zcorrect
            if x < self.minx: self.minx = x
            if x > self.maxx: self.maxx = x
            if y < self.miny: self.miny = y
            if y > self.maxy: self.maxy = y
            if z < self.minz: self.minz = z
            if z > self.maxz: self.maxz = z

    def get_hips(self, t=None):
        self._process_bvhkeyframe(self.keyframes[t], self.hips)
        return self.hips

    def get_vertices(self, t):
        self._process_bvhkeyframe(self.keyframes[t], self.hips)
        return self.hips.get_vertices()

    def populate_edges_from_vertices(self, vertices, edges):
        self.hips.populate_edges_from_vertices_recurse(vertices, edges)

    def _process_bvhkeyframe(self, keyframe, joint, frame_data_index=0):
        keyframe_dict = dict()
        for channel in joint.channels:
            keyframe_dict[channel] = keyframe[frame_data_index]
            frame_data_index += 1

        if "Xposition" in keyframe_dict:
            transposition_matrix = make_transposition_matrix(
                keyframe_dict["Xposition"],
                keyframe_dict["Yposition"],
                keyframe_dict["Zposition"])

        if "Xrotation" in keyframe_dict:
            rotate = True
            rotation_matrix = make_rotation_matrix(
                keyframe_dict["Xrotation"],
                keyframe_dict["Yrotation"],
                keyframe_dict["Zrotation"])
            joint.rotation = [keyframe_dict["Xrotation"],
                              keyframe_dict["Yrotation"],
                              keyframe_dict["Zrotation"]]
        else:
            rotate = False
            joint.rotation = None

        if joint.hasparent:
            parent_trtr = joint.parent.trtr
            localtoworld = dot(parent_trtr, joint.transposition_matrix)
        else:
            localtoworld = dot(joint.transposition_matrix, transposition_matrix)

        if rotate:
            trtr = dot(localtoworld, rotation_matrix)
        else:
            trtr = localtoworld
        joint.trtr = trtr

        worldpos = array([
                  localtoworld[0,3],
                  localtoworld[1,3],
                  localtoworld[2,3],
                  localtoworld[3,3] ])
        joint.worldpos = worldpos

        for child in joint.children:
            frame_data_index = self._process_bvhkeyframe(keyframe, child, frame_data_index)
            if(frame_data_index == 0):
                raise Exception("fatal error")

        return frame_data_index



class BvhReader(cgkit.bvh.BVHReader):
    def __init__(self, *args):
        cgkit.bvh.BVHReader.__init__(self, *args)
        self.scale_factor = 1

    def read(self):
        cgkit.bvh.BVHReader.read(self)
        self._joint_index = 0
        hips = self._process_node(self.root)
        self.skeleton = skeleton(
          hips, keyframes = self.keyframes,
          num_frames=self.num_frames, dt=self.dt)
        self.num_joints = self._joint_index

    def get_duration(self):
        return self.skeleton.num_frames * self.skeleton.dt

    def get_hips(self, t):
        frame_index = self._frame_index(t)
        return self.skeleton.get_hips(frame_index)

    def _frame_index(self, t):
        return int(t / self.skeleton.dt) % self.skeleton.num_frames

    def get_skeleton_vertices(self, t):
        frame_index = self._frame_index(t)
        return self.skeleton.get_vertices(frame_index)

    def vertices_to_edges(self, vertices):
        edges = []
        self.skeleton.populate_edges_from_vertices(vertices, edges)
        return edges

    def vertex_to_vector(self, v):
        return array([v.tr[0], v.tr[1], v.tr[2]])

    def vector_to_vertex(self, v):
        return vertex(v[0], v[1], v[2])

    def normalize_vector(self, v):
        return array([
            (v[0] - self.skeleton.minx) / self.scale_factor,
            (v[1] - self.skeleton.miny) / self.scale_factor,
            (v[2] - self.skeleton.minz) / self.scale_factor])

    def skeleton_scale_vector(self, v):
        return array([
            v[0] * self.scale_factor + self.skeleton.minx,
            v[1] * self.scale_factor + self.skeleton.miny,
            v[2] * self.scale_factor + self.skeleton.minz])

    def onHierarchy(self, root):
        self.root = root
        self.keyframes = []

    def onMotion(self, num_frames, dt):
        self.num_frames = num_frames
        self.dt = dt

    def onFrame(self, values):
        self.keyframes.append(values)

    def _process_node(self, node, parentname='hips'):
        name = node.name
        if (name == "End Site") or (name == "end site"):
            name = parentname + "End"
        b1 = joint(name, self._joint_index)
        self._joint_index += 1
        b1.channels = node.channels
        b1.transposition[0] = node.offset[0]
        b1.transposition[1] = node.offset[1]
        b1.transposition[2] = node.offset[2]

        b1.transposition_matrix = make_transposition_matrix(
            b1.transposition[0],
            b1.transposition[1],
            b1.transposition[2])

        for child in node.children:
            b2 = self._process_node(child, name)
            b1.addchild(b2)
        return b1

    def print_pose(self, vertices):
        self._print_joint_recurse(vertices, self.skeleton.hips)
        print

    def _print_joint_recurse(self, vertices, joint):
        if joint.hasparent:
            print "%-3d -> %-3d: %f" % (
                joint.parent.index, joint.index,
                numpy.linalg.norm(
                    self.vertex_to_vector(vertices[joint.parent.index]) -
                    self.vertex_to_vector(vertices[joint.index])))

        for child in joint.children:
            self._print_joint_recurse(vertices, child)
