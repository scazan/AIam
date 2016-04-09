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
PARAMETERS = [
    "imitation",
    "flaneur_translational_speed"]

class MidiController:
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("--port")
        parser.add_argument("--calibrate", action="store_true")
        for parameter_name in PARAMETERS:
            parser.add_argument("--%s" % parameter_name, help="command,channel")

    def __init__(self, args):
        self._args = args
        self._midi_in, port_name = open_midiport(args.port, "input")
        self._midi_in.set_callback(self._callback)
        self._create_parameter_lookup_table()

    def _create_parameter_lookup_table(self):
        self._parameter_lookup_table = {}
        for parameter_name in PARAMETERS:
            command_comma_channel = getattr(self._args, parameter_name)
            if command_comma_channel:
                self._parameter_lookup_table[command_comma_channel] = parameter_name

    def _callback(self, event, data=None):
        message, deltatime = event
        command, channel, value = message
        command_comma_channel = "%s,%s" % (command, channel)
        if self._args.calibrate:
            print command_comma_channel
        if command_comma_channel in self._parameter_lookup_table:
            parameter_name = self._parameter_lookup_table[command_comma_channel]
            self._process_value(parameter_name, value)

    def _process_value(self, parameter_name, midi_value):
        float_value = float(midi_value) / 127
        event_sender.send_event(
            Event(Event.PARAMETER,
                  {"class": "HybridParameters",
                   "name": parameter_name,
                   "value": float_value}))
                
    def main_loop(self):
        print "press ctrl-c to exit"
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        self._midi_in.close_port()

parser = ArgumentParser()
MidiController.add_parser_arguments(parser)
args = parser.parse_args()

event_sender = WebsocketClient(WEBSOCKET_HOST)
event_sender.set_event_listener(EventListener())
event_sender.connect()

controller = MidiController(args)
controller.main_loop()
