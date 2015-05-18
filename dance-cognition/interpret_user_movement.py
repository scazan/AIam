import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/connectivity")
from osc_receiver import OscReceiver
from websocket_client import WebsocketClient
from event_listener import EventListener
from event import Event
import time

OSC_PORT = 15002
WEBSOCKET_HOST = "localhost"

def handle_joint_data(path, args, types, src, user_data):
    joint_name, x, y, z = args
    preferred_distance = float(abs(x - 200)) / 300
    websocket_client.send_event(
        Event(Event.PARAMETER,
              {"name": "preferred_distance",
               "value": preferred_distance}))

websocket_client = WebsocketClient(WEBSOCKET_HOST)
websocket_client.set_event_listener(EventListener())
websocket_client.connect()

osc_receiver = OscReceiver(OSC_PORT)
osc_receiver.add_method("/joint", "sfff", handle_joint_data)
osc_receiver.start()

while True:
    time.sleep(1)
