import time
from simple_osc_sender import OscSender
osc_sender = OscSender(7892)

def move(source, destination):
    for i in range(10):
        osc_sender.send("/position", source, destination, float(i) / 10)
        print "/position", source, destination, float(i) / 10
        time.sleep(0.1)

while True:
    move("mc", "ml")
    move("ml", "mc")
