import time
from simple_osc_sender import OscSender
osc_sender = OscSender(7892)

def move(source, destination):
    for i in range(100):
        osc_sender.send("/position", source, destination, float(i) / 100)
        time.sleep(0.01)

while True:
    move("mc", "mlb")
    move("mlb", "mc")

    # move("mc", "ml")
    # move("ml", "mc")

    # move("mc", "hb") # bad BVH
    # move("hb", "mc") # bad BVH

    # move("mc", "mb") # nothing
    # move("mb", "mc") # nothing

    # move("mc", "mlf")
    # move("mlf", "mc")

    # move("mlb", "ml")
    # move("ml", "mlb")

    # move("mlb", "hb")
    # move("hb", "mlb") # bad BVH

