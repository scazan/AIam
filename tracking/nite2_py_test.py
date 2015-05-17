# requires OpenNi-2.2 and Nite-2.0

from primesense import openni2
from primesense import nite2

openni2.initialize()
device = openni2.Device.open_any()
nite2.initialize()

user_tracker = nite2.UserTracker(device)

while True:
    frame = user_tracker.read_frame()    
    for user in frame.users:
        if user.is_new():
            user_tracker.start_skeleton_tracking(user.id)
            print "New %s" % user.id
        if user_tracker.is_tracking(user.id):
            # this never seems to be reached
            print "Tracking %s" % user.id
