# adopted from BVHplay (http://sourceforge.net/projects/bvhplay)
#

from numpy import array


class vertex:
    def __init__(self, x=0, y=0, z=0, description='', DEBUG=0):
      self.tr = array([x,y,z,1])

class edge:
    def __init__(self, v1, v2, description='', DEBUG=0):
      self.v1 = v1
      self.v2 = v2
      self.descr = description
      self.DEBUG = DEBUG
