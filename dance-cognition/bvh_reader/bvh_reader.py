# adopted from BVHplay (http://sourceforge.net/projects/bvhplay)

from math import radians, cos, sin
import cgkit.bvh
from geo import vertex, edge
from numpy import array, dot

class joint:
  def __init__(self, name, index):
    self.name = name
    self.index = index
    self.children = []
    self.channels = []
    self.hasparent = 0
    self.parent = 0
    self.strans = array([0.,0.,0.])
    self.stransmat = array([
        [0.,0.,0.,0.],[0.,0.,0.,0.],
        [0.,0.,0.,0.],[0.,0.,0.,0.] ])

  def addchild(self, childjoint):
    self.children.append(childjoint)
    childjoint.hasparent = 1
    childjoint.parent = self

  def get_vertices_recurse(self, vertices):
    vertices.append(vertex(
        self.worldpos[0],
        self.worldpos[1],
        self.worldpos[2]))
    for child in self.children:
      child.get_vertices_recurse(vertices)
    return vertices

  def populate_edges_from_vertices_recurse(self, vertices, edgelist):
    if self.hasparent:
      new_edge = edge(
        vertices[self.parent.index],
        vertices[self.index])
      edgelist.append(new_edge)

    for child in self.children:
      child.populate_edges_from_vertices_recurse(vertices, edgelist)



class skeleton:
  def __init__(self, hips, keyframes, frames=0, dt=.033333333):
    self.hips = hips
    self.keyframes = keyframes  
    self.frames = frames
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
    xcorrect = self.hips.strans[0]
    ycorrect = self.hips.strans[1]
    zcorrect = self.hips.strans[2]

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

  def get_vertices(self, t):
    process_bvhkeyframe(self.keyframes[t-1], self.hips, t)
    result = []
    self.hips.get_vertices_recurse(result)
    return result

  def populate_edges_from_vertices(self, vertices, edges):
    self.hips.populate_edges_from_vertices_recurse(vertices, edges)


def process_bvhkeyframe(keyframe, joint, t):
  counter = 0
  dotrans = 0
  dorot = 0

  drotmat = array([ [1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.] ])

  for channel in joint.channels:
    keyval = keyframe[counter]
    if(channel == "Xposition"):
      dotrans = 1
      xpos = keyval
    elif(channel == "Yposition"):
      dotrans = 1
      ypos = keyval
    elif(channel == "Zposition"):
      dotrans = 1
      zpos = keyval
    elif(channel == "Xrotation"):
      dorot = 1
      xrot = keyval
      theta = radians(xrot)
      mycos = cos(theta)
      mysin = sin(theta)
      drotmat2 = array([
          [1.,     0.,     0.,     0.],
          [0.,     mycos,  -mysin, 0.],
          [0.,     mysin,  mycos,  0.],
          [0.,     0.,     0.,     1.] ])
      drotmat = dot(drotmat, drotmat2)

    elif(channel == "Yrotation"):
      dorot = 1
      yrot = keyval
      theta = radians(yrot)
      mycos = cos(theta)
      mysin = sin(theta)
      drotmat2 = array([
          [mycos,  0.,    mysin, 0.],
          [0.,     1.,    0.,    0.],
          [-mysin, 0.,    mycos, 0.],
          [0.,     0.,    0.,    1.] ])
      drotmat = dot(drotmat, drotmat2)

    elif(channel == "Zrotation"):
      dorot = 1
      zrot = keyval
      theta = radians(zrot)
      mycos = cos(theta)
      mysin = sin(theta)
      drotmat2 = array([
          [mycos,  -mysin, 0.,   0.],
          [mysin,  mycos,  0.,   0.],
          [0.,     0.,     1.,   0.],
          [0.,     0.,     0.,   1.] ])
      drotmat = dot(drotmat, drotmat2)
    else:
      raise Exception("Fatal error in process_bvhkeyframe: illegal channel name ", channel)
    counter += 1

  if dotrans:
    dtransmat = array([
        [1.,    0.,    0.,    xpos],
        [0.,    1.,    0.,    ypos],
        [0.,    0.,    1.,    zpos],
        [0.,    0.,    0.,    1.] ])

  if joint.hasparent:
    parent_trtr = joint.parent.trtr
    localtoworld = dot(parent_trtr,joint.stransmat)
  else:
    localtoworld = dot(joint.stransmat,dtransmat)

  trtr = dot(localtoworld,drotmat)
  joint.trtr = trtr


  worldpos = array([
            localtoworld[0,3],
            localtoworld[1,3],
            localtoworld[2,3],
            localtoworld[3,3] ])
  joint.worldpos = worldpos

  newkeyframe = keyframe[counter:]
  for child in joint.children:
    newkeyframe = process_bvhkeyframe(newkeyframe, child, t)
    if(newkeyframe == 0):
      raise Exception("fatal error")

  return newkeyframe



class BvhReader(cgkit.bvh.BVHReader):
    def read(self):
        cgkit.bvh.BVHReader.read(self)
        self._joint_index = 0
        hips = self._process_node(self.root)
        self.skeleton = skeleton(
            hips, keyframes = self.keyframes,
            frames=self.frames, dt=self.dt)
        self.num_joints = self._joint_index

    def get_skeleton_vertices(self, t):
        frame_index = 1 + int(t / self.skeleton.dt) % self.skeleton.frames
        return self.skeleton.get_vertices(frame_index)

    def vertices_to_edges(self, vertices):
      edges = []
      self.skeleton.populate_edges_from_vertices(vertices, edges)
      return edges

    def onHierarchy(self, root):
        self.root = root
        self.keyframes = []

    def onMotion(self, frames, dt):
        self.frames = frames
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
        b1.strans[0] = node.offset[0]
        b1.strans[1] = node.offset[1]
        b1.strans[2] = node.offset[2]

        b1.stransmat = array([
            [1.,0.,0.,0.],
            [0.,1.,0.,0.],
            [0.,0.,1.,0.],
            [0.,0.,0.,1.] ])

        b1.stransmat[0,3] = b1.strans[0]
        b1.stransmat[1,3] = b1.strans[1]
        b1.stransmat[2,3] = b1.strans[2]

        for child in node.children:
            b2 = self._process_node(child, name)
            b1.addchild(b2)
        return b1
