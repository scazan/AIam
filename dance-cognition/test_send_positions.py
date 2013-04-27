import time
from simple_osc_sender import OscSender
osc_sender = OscSender(7892)

def move(source, destination):
    for i in range(100):
        osc_sender.send("/position", source, destination, float(i) / 100)
        time.sleep(0.01)

while True:
    move("mc", "ml")
    move("ml", "mc")
