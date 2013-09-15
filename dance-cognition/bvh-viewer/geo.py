# adopted from BVHplay (http://sourceforge.net/projects/bvhplay)
#

class vertex:
    def __init__(self, x=0, y=0, z=0):
      self.tr = [x,y,z,1]

class edge:
    def __init__(self, v1, v2):
      self.v1 = v1
      self.v2 = v2
