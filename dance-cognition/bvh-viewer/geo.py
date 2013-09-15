# adopted from BVHplay (http://sourceforge.net/projects/bvhplay)
#

from numpy import array, dot


#########################################################
# WORLDVERT class
#########################################################

class worldvert:
    def __init__(self, x=0, y=0, z=0, description='', DEBUG=0):
      self.tr = array([x,y,z,1])  # tr = "translate position"
      self.descr = description
      self.DEBUG = DEBUG

    def __repr__(self):
        mystr = "worldvert " + self.descr + "\n tr: " + self.tr.__repr__()
        return mystr      


##################################################
# WORLDEDGE class
##################################################

class worldedge:
    def __init__(self, wv1, wv2, description='', DEBUG=0):
      self.wv1 = wv1
      self.wv2 = wv2
      self.descr = description
      self.DEBUG = DEBUG
    
    def __repr__(self):
        mystr = "Worldedge " + self.descr +" wv1:\n" + self.wv1.__repr__()   \
            + "\nworldedge " + self.descr + " wv2:\n" +     \
            self.wv2.__repr__() + "\n"
        return mystr


##########################################################
# SCREEENVERT class
##########################################################
# 9/1/08: Way too ugly to have screenvert contain or point to
# a worldvert, so I'm changing this to use a translate array just
# like worldvert.  If you want screenvert to have the values of
# a worldvert, you need to copy those values in by hand or pass
# them in at construction time, just like you would with a worldvert.

class screenvert:
    def __init__(self, x=0., y=0., z=0., description='', DEBUG=0):
        self.tr = array([x,y,z,1])  # tr = "translate position"
        self.screenx = 0
        self.screeny = 0
        self.descr = description
        self.DEBUG = DEBUG




##################################################
# SCREENEDGE class
##################################################

class screenedge:
    def __init__(self, sv1, sv2, width=2, color='black', arrow='none', \
                 description='', circle=0, DEBUG=0):
      self.sv1 = sv1  # screenvert not worldvert
      self.sv2 = sv2
      self.width = width
      self.id = 0  # Tracks canvas ID for line
      self.cid = 0  # canvas ID of circle at joint end, if in use
      self.color = color
      self.arrow = arrow
      self.descr = description
      self.circle = circle  # Set to 1 to draw circle at end of edge
      self.drawme = 1  # Set to 0 to not attempt to draw on screen
      self.DEBUG = DEBUG

    def __repr__(self):
        mystr = "Screenedge " + self.descr +" sv1:\n" + self.sv1.__repr__()   \
            + "\nscreenedge " + self.descr + " sv2:\n" +     \
            self.sv2.__repr__() + "\n"
        return mystr


##################################
# GRID_SETUP
# Creates and returns a populated array of screenedge
# Don't call this until you've set up your skeleton and can
# extract minx, miny, maxx, maxy from it.
#
def grid_setup(minx, minz, maxx, maxz, DEBUG=0):

    if DEBUG:
        print "grid_setup: minx=%s, minz=%s, maxx=%s, maxz=%s" % \
            (minx, minz, maxx, maxz)

    # The input values define a rectangle.  Round them to nearest 10.
    minx2 = 10*int(minx/10) - 10
    maxx2 = 10*int(maxx/10) + 10
    minz2 = 10*int(minz/10) - 10
    maxz2 = 10*int(maxz/10) + 10

    gridedges = []
# Range() won't give us the topmost value of the range, so we have to
# use maxz2+1 as the top of the range.
    for z in range(minz2, maxz2+1, 10):
      sv1 = screenvert(minx2, 0., z)
      sv2 = screenvert(maxx2, 0., z)
      se = screenedge(sv1, sv2, width=1, color='grey', DEBUG=0)
      if DEBUG:
          print "grid_setup: adding screenedge from (%d,%d) to (%d,%d)" \
              % (minx2, z, maxx2, z)
      gridedges.append(se)

    for x in range(minx2, maxx2+1, 10):
      sv1 = screenvert(x, 0., minz2)
      sv2 = screenvert(x, 0., maxz2)
      se = screenedge(sv1, sv2, width=1, color='grey', DEBUG=0)
      if DEBUG:
          print "grid_setup: adding screenedge from (%d,%d) to (%d,%d)" \
              % (x, minz2, x, maxz2)
      gridedges.append(se)

    return gridedges
