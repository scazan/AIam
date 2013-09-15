# adopted from BVHplay (http://sourceforge.net/projects/bvhplay)

from math import radians, cos, sin
import cgkit.bvh
from geo import vertex, edge
from numpy import array, dot

class joint:
  def __init__(self, name):
    self.name = name
    self.children = []
    self.channels = []  # Set later.  Ordered list of channels: each
        # list entry is one of [XYZ]position, [XYZ]rotation
    self.hasparent = 0  # flag
    self.parent = 0  # joint.addchild() sets this
#cgkit#    self.strans = vec3(0,0,0)  # static translation vector (x, y, z)
    self.strans = array([0.,0.,0.])  # I think I could just use   \
                                     # regular Python arrays

    # Transformation matrices:
    self.stransmat = array([ [0.,0.,0.,0.],[0.,0.,0.,0.],    \
                               [0.,0.,0.,0.],[0.,0.,0.,0.] ])

  def addchild(self, childjoint):
    self.children.append(childjoint)
    childjoint.hasparent = 1
    childjoint.parent = self

  # Called by skeleton.create_edges()
  def create_edges_recurse(self, edgelist):
    if self.hasparent:
      temp1 = self.parent.worldpos  # Faster than triple lookup below?
      temp2 = self.worldpos
      v1 = vertex(temp1[0], temp1[1], temp1[2])
      v2 = vertex(temp2[0], temp2[1], temp2[2])
      myedge = edge(v1,v2)
      edgelist.append(myedge)

    for child in self.children:
      child.create_edges_recurse(edgelist)



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



####################
# MAKE_SKELSCREENEDGES: creates and returns an array of screenedge
# that has exactly as many elements as the joint count of skeleton.
#
  def make_skelscreenedges(self):
    self.create_edges_onet(1)

    jointcount = len(self.edges)
    skelscreenedges = []

    for x in range(jointcount):
      sv1 = vertex(0.,0.,0.)
      sv2 = vertex(0.,0.,0.)
      se1 = edge(sv1, sv2)
      skelscreenedges.append(se1)
    return skelscreenedges





#########################################
# CREATE_EDGES_ONET class function

  def create_edges_onet(self, t):
# Before we can compute edge positions, we need to have called
# process_bvhkeyframe for time t, which computes trtr and worldpos
# for the joint hierarchy at time t.  Since we no longer precompute
# this information when we read the BVH file, here's where we do it.
# This is on-demand computation of trtr and worldpos.
    process_bvhkeyframe(self.keyframes[t-1], self.hips, t)

    edgelist = []
    self.hips.create_edges_recurse(edgelist)
    self.edges = edgelist


#################################
# POPULATE_SKELSCREENEDGES
# Given a time t and a precreated array of screenedge, copies values
# from skeleton.edges[] into the screenedge array.
#
# Use this routine whenever slidert (time position on slider) changes.
# This routine is how you get your edge data somewhere that redraw()
# will make use of it.

  def populate_skelscreenedges(self, sse, t):
# First we have to make sure that self.edges exists for slidert=t
    self.create_edges_onet(t)
    counter = 0
    for edge in self.edges:
      # Yes, we copy in the xyz values manually.  This keeps us sane.
      sse[counter].v1.tr[0] = edge.v1.tr[0]
      sse[counter].v1.tr[1] = edge.v1.tr[1]
      sse[counter].v1.tr[2] = edge.v1.tr[2]
      sse[counter].v2.tr[0] = edge.v2.tr[0]
      sse[counter].v2.tr[1] = edge.v2.tr[1]
      sse[counter].v2.tr[2] = edge.v2.tr[2]
      counter +=1



def process_bvhkeyframe(keyframe, joint, t):

  counter = 0
  dotrans = 0
  dorot = 0

# We have to build up drotmat one rotation value at a time so that
# we get the matrix multiplication order correct.
  drotmat = array([ [1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.] ])

  # Suck in as many values off the front of "keyframe" as we need
  # to populate this joint's channels.  The meanings of the keyvals
  # aren't given in the keyframe itself; their meaning is specified
  # by the channel names.
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
#cgkit#      drotmat2 = drotmat2.rotation(radians(xrot), XAXIS)
#cgkit#      drotmat = drotmat * drotmat2  # Build up the full rotation matrix
      theta = radians(xrot)
      mycos = cos(theta)
      mysin = sin(theta)
##      drotmat2 = deepcopy(IDENTITY)
      drotmat2 = array([ [1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],    \
                           [0.,0.,0.,1.] ])
      drotmat2[1,1] = mycos
      drotmat2[1,2] = -mysin
      drotmat2[2,1] = mysin
      drotmat2[2,2] = mycos
      drotmat = dot(drotmat, drotmat2)

    elif(channel == "Yrotation"):
      dorot = 1
      yrot = keyval
#cgkit#      drotmat2 = drotmat2.rotation(radians(yrot), YAXIS)
#cgkit#      drotmat = drotmat * drotmat2
      theta = radians(yrot)
      mycos = cos(theta)
      mysin = sin(theta)
##      drotmat2 = deepcopy(IDENTITY)
      drotmat2 = array([ [1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],    \
                           [0.,0.,0.,1.] ])
      drotmat2[0,0] = mycos
      drotmat2[0,2] = mysin
      drotmat2[2,0] = -mysin
      drotmat2[2,2] = mycos
      drotmat = dot(drotmat, drotmat2)

    elif(channel == "Zrotation"):
      dorot = 1
      zrot = keyval
      theta = radians(zrot)
      mycos = cos(theta)
      mysin = sin(theta)
##      drotmat2 = deepcopy(IDENTITY)
      drotmat2 = array([ [1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],     \
                           [0.,0.,0.,1.] ])
      drotmat2[0,0] = mycos
      drotmat2[0,1] = -mysin
      drotmat2[1,0] = mysin
      drotmat2[1,1] = mycos
      drotmat = dot(drotmat, drotmat2)
    else:
      print "Fatal error in process_bvhkeyframe: illegal channel name ", \
                                                               channel
      return(0)
##      sys.exit()
    counter += 1
  # End "for channel..."

  if dotrans:  # If we are the hips...
    # Build a translation matrix for this keyframe
    dtransmat = array([ [1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],    \
                          [0.,0.,0.,1.] ])
    dtransmat[0,3] = xpos
    dtransmat[1,3] = ypos
    dtransmat[2,3] = zpos

    # End of IF dotrans

  # At this point we should have computed:
  #  stransmat  (computed previously in process_bvhnode subroutine)
  #  dtransmat (only if we're the hips)
  #  drotmat
  # We now have enough to compute joint.trtr and also to convert
  # the position of this joint (vertex) to worldspace.
  # 
  # Worldpos of the current joint is localtoworld = TRTR...T*[0,0,0,1]
  #   which equals parent_trtr * T*[0,0,0,1]
  # In other words, the rotation value of a joint has no impact on
  # that joint's position in space, so drotmat doesn't get used to
  # compute worldpos in this routine.
  # 
  # However we don't pass localtoworld down to our child -- what
  # our child needs is trtr = TRTRTR...TR
  # 
  # The code below attempts to optimize the computations so that we
  # compute localtoworld first, then trtr.

  if joint.hasparent:  # Not hips
    parent_trtr = joint.parent.trtr

# 8/31/2008: dtransmat now excluded from non-hips computation since
# it's just identity anyway.
##    localtoworld = dot(parent_trtr,dot(joint.stransmat,dtransmat))
    localtoworld = dot(parent_trtr,joint.stransmat)

  else:  # Hips
#cgkit#    localtoworld = joint.stransmat * dtransmat
    localtoworld = dot(joint.stransmat,dtransmat)

#cgkit#  trtr = localtoworld * drotmat
  trtr = dot(localtoworld,drotmat)

  joint.trtr = trtr


#cgkit#  worldpos = localtoworld * ORIGIN  # worldpos should be a vec4
#
# numpy conversion: eliminate the matrix multiplication entirely,
# since all we're doing is extracting the last column of worldpos.
  worldpos = array([ localtoworld[0,3],localtoworld[1,3],        \
                      localtoworld[2,3], localtoworld[3,3] ])
  joint.worldpos = worldpos

  newkeyframe = keyframe[counter:]  # Slices from counter+1 to end
  for child in joint.children:
    # Here's the recursion call.  Each time we call process_bvhkeyframe,
    # the returned value "newkeyframe" should shrink due to the slicing
    # process
    newkeyframe = process_bvhkeyframe(newkeyframe, child, t)
    if(newkeyframe == 0):  # If retval = 0
      print "Passing up fatal error in process_bvhkeyframe"
      return(0)
  return newkeyframe



class BvhReader(cgkit.bvh.BVHReader):
    def read(self):
        cgkit.bvh.BVHReader.read(self)
        hips = self._process_node(self.root)
        self.skeleton = skeleton(
            hips, keyframes = self.keyframes,
            frames=self.frames, dt=self.dt)

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
        b1 = joint(name)
        b1.channels = node.channels
        b1.strans[0] = node.offset[0]
        b1.strans[1] = node.offset[1]
        b1.strans[2] = node.offset[2]

        b1.stransmat = array([ [1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.] ])

        b1.stransmat[0,3] = b1.strans[0]
        b1.stransmat[1,3] = b1.strans[1]
        b1.stransmat[2,3] = b1.strans[2]

        for child in node.children:
            b2 = self._process_node(child, name)
            b1.addchild(b2)
        return b1
