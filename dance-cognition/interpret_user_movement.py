import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/connectivity")
from osc_receiver import OscReceiver
from websocket_client import WebsocketClient
from event_listener import EventListener
from event import Event
from leaky_integrator import LeakyIntegrator
import time

OSC_PORT = 15002
WEBSOCKET_HOST = "localhost"

class Joint:
    def __init__(self):
        self._previous_time = None
        self._activity = LeakyIntegrator(response_factor=.98)

    def get_activity(self):
        return self._activity.value()

    def update(self, value):
        now = time.time()
        if self._previous_time is None:
            self._activity.set_value(value)
        else:
            time_increment = now - self._previous_time
            self._activity.integrate(value, time_increment)
        self._previous_time = now

class UserMovementInterpreter:
    def __init__(self):
        self._joints = {"left_hand": Joint()}

    def handle_joint_data(self, user_id, joint_name, x, y, z):
        joint = self._joints[joint_name]
        value = float(abs(x - 200)) / 300
        joint.update(value)
        preferred_distance = novelty = joint.get_activity()
        websocket_client.send_event(
            Event(Event.PARAMETER,
                  {"name": "preferred_distance",
                   "value": preferred_distance}))
        websocket_client.send_event(
            Event(Event.PARAMETER,
                  {"name": "novelty",
                   "value": novelty}))

interpreter = UserMovementInterpreter()

def handle_joint_data(path, args, types, src, user_data):
    interpreter.handle_joint_data(*args)

websocket_client = WebsocketClient(WEBSOCKET_HOST)
websocket_client.set_event_listener(EventListener())
websocket_client.connect()

osc_receiver = OscReceiver(OSC_PORT)
osc_receiver.add_method("/joint", "isfff", handle_joint_data)
osc_receiver.start()

while True:
    time.sleep(1)
