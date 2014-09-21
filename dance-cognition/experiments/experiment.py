import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from argparse import ArgumentParser
from storage import *
from bvh_reader import bvh_reader as bvh_reader_module
import imp
from server import WebsocketServer, ClientHandler
from stopwatch import Stopwatch
import threading
from event import Event
from event_listener import EventListener

class BaseEntity:
    @staticmethod
    def add_parser_arguments(parser):
        pass

    def __init__(self, experiment):
        self._t = 0
        self.experiment = experiment
        self.bvh_reader = experiment.bvh_reader
        self.args = experiment.args
        self.model = None

    def adapt_value_to_model(self, value):
        return value

    def proceed(self, time_increment):
        self._t += time_increment

    def process_input(self, value):
        return self.process_io(value)

    def process_output(self, value):
        return self.process_io(value)

    def process_io(self, value):
        return value

    def update(self):
        if self.experiment.input is None:
            self.processed_input = None
        else:
            self.processed_input = self.process_input(self.experiment.input)

        if self.experiment.output is None:
            self.processed_output = None
        else:
            self.processed_output = self.process_output(self.experiment.output)

    def get_cursor(self):
        if hasattr(self, "get_duration"):
            return self._t % self.get_duration()
        else:
            return self._t

    def set_cursor(self, t):
        self._t = t

class Experiment(EventListener):
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("-profile", "-p")
        parser.add_argument("-entity", type=str)
        parser.add_argument("-train", action="store_true")
        parser.add_argument("-training-duration", type=float)
        parser.add_argument("-training-data-frame-rate", type=int, default=50)
        parser.add_argument("-bvh", type=str)
        parser.add_argument("-bvh-speed", type=float, default=1.0)
        parser.add_argument("-joint")
        parser.add_argument("-frame-rate", type=float, default=50.0)
        parser.add_argument("-unit-cube", action="store_true")
        parser.add_argument("-input-y-offset", type=float, default=.0)
        parser.add_argument("-output-y-offset", type=float, default=.0)
        parser.add_argument("-export-dir", default="export")
        parser.add_argument("--camera", help="posX,posY,posZ,orientY,orientX",
                            default="-3.767,-1.400,-3.485,-55.500,18.500")
        parser.add_argument("--floor", action="store_true")
        parser.add_argument("--backend-only", action="store_true")
        parser.add_argument("--ui-only", action="store_true")
        parser.add_argument("--backend-host", default="localhost")

    def __init__(self, parser):
        EventListener.__init__(self)
        self._add_event_handlers()

        args, _remaining_args = parser.parse_known_args()
        if args.profile:
            profile_path = "%s/%s.profile" % (self.profiles_dir, args.profile)
            profile_args_string = open(profile_path).read()
            profile_args_strings = profile_args_string.split()
            args, _remaining_args = parser.parse_known_args(profile_args_strings, namespace=args)
            self._model_path = "%s/%s.model" % (self.profiles_dir, args.profile)
            self._training_data_path = "%s/%s.data" % (self.profiles_dir, args.profile)

        entity_module = imp.load_source("entity", "entities/%s.py" % args.entity)
        if hasattr(entity_module, "Entity"):
            entity_class = entity_module.Entity
        else:
            entity_class = BaseEntity
        entity_class.add_parser_arguments(parser)
        entity_module.Scene.add_parser_arguments(parser)

        args = parser.parse_args()
        if args.profile:
            args = parser.parse_args(profile_args_strings, namespace=args)

        self.args = args
        if args.bvh:
            self.bvh_reader = bvh_reader_module.BvhReader(args.bvh)
            self.bvh_reader.read()
        else:
            self.bvh_reader = None
        self.input = None
        self.output = None
        self.entity = entity_class(self)
        self._scene_class = entity_module.Scene
        self._running = True
        self.stopwatch = Stopwatch()
        self._frame_count = 0
        self.ui_handlers = set()

    def _add_event_handlers(self):
        self.add_event_handler(Event.START, self._start)
        self.add_event_handler(Event.STOP, self._stop)
        self.add_event_handler(
            Event.SET_CURSOR,
            lambda event: self.entity.set_cursor(event.content))

    def run_backend_and_or_ui(self):
        run_backend = not self.args.ui_only
        run_ui = not self.args.backend_only
        if run_backend:
            self._setup_websocket_server()
            if run_ui:
                self._start_websocket_server_in_new_thread()
                self.run_ui()
            else:
                self._start_websocket_server()
        elif run_ui:
            self.run_ui()

    def _start(self):
        self._running = True

    def _stop(self):
        self._running = False

    def is_running(self):
        return self._running

    def update(self):
        pass

    def _update_and_refresh_uis(self):
        self.now = self.current_time()
        if self._frame_count == 0:
            self.stopwatch.start()
        else:
            if self.is_running():
                self.time_increment = self.now - self.previous_frame_time
                self.proceed()

            self.entity.update()
            self.update()
            self.send_event_to_ui(Event(Event.REDUCTION, self.reduction))
            self.send_event_to_ui(Event(Event.OUTPUT, self.entity.processed_output))

        self.previous_frame_time = self.now
        self._frame_count += 1

    def send_event_to_ui(self, event):
        for ui_handler in self.ui_handlers:
            ui_handler.send_event(event)

    def current_time(self):
        return self.stopwatch.get_elapsed_time()

    def _training_duration(self):
        if self.args.training_duration:
            return self.args.training_duration
        elif hasattr(self.entity, "get_duration"):
            return self.entity.get_duration()
        else:
            raise Exception(
                "training duration specified in neither arguments nor the %s class" % \
                    self.entity.__class__.__name__)

    def _setup_websocket_server(self):
        self._server = WebsocketServer(UiHandler, {"experiment": self})
        self._set_up_timed_refresh()

    def _set_up_timed_refresh(self):
        self._server.add_periodic_callback(
            self._update_and_refresh_uis, 1000. / self.args.frame_rate)

    def _start_websocket_server(self):
        self._server.start()

    def _start_websocket_server_in_new_thread(self):
        server_thread = threading.Thread(target=self._start_websocket_server)
        server_thread.daemon = True
        server_thread.start()

class UiHandler(ClientHandler):
    def __init__(self, *args, **kwargs):
        print "UI connected"
        self._experiment = kwargs.pop("experiment")
        self._experiment.ui_handlers.add(self)
        super(UiHandler, self).__init__(*args, **kwargs)

    def on_close(self):
        print "UI disconnected"
        self._experiment.ui_handlers.remove(self)

    def received_event(self, event):
        self._experiment.handle_event(event)
