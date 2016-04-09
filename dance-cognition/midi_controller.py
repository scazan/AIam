import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/connectivity")

from argparse import ArgumentParser
import rtmidi
from rtmidi.midiutil import open_midiport
import time
from websocket_client import WebsocketClient
from event_listener import EventListener
from event import Event

WEBSOCKET_HOST = "localhost"

class MidiController:
    def __init__(self, command=None, channel=None, midi_port=None, calibrate=False):
        self._tracked_command = command
        self._tracked_channel = channel
        self._calibrate = calibrate
        self._midi_in, port_name = open_midiport(midi_port, "input")
        self._midi_in.set_callback(self._callback)

    def _callback(self, event, data=None):
        message, deltatime = event
        command, channel, value = message
        if self._calibrate:
            print "command=%s channel=%s" % (command, channel)
        if command == self._tracked_command and channel == self._tracked_channel:
            self._process_value(value)

    def _process_value(self, value):
        imitation = float(value) / 127
        event_sender.send_event(
            Event(Event.PARAMETER,
                  {"class": "HybridParameters",
                   "name": "imitation",
                   "value": imitation}))
                
    def main_loop(self):
        print "press ctrl-c to exit"
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        self._midi_in.close_port()

parser = ArgumentParser()
parser.add_argument("--port")
parser.add_argument("--command", type=int)
parser.add_argument("--channel", type=int)
parser.add_argument("--calibrate", action="store_true")
args = parser.parse_args()

event_sender = WebsocketClient(WEBSOCKET_HOST)
event_sender.set_event_listener(EventListener())
event_sender.connect()

controller = MidiController(
    midi_port=args.port,
    command=args.command,
    channel=args.channel,
    calibrate=args.calibrate)
controller.main_loop()
