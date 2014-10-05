import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from argparse import ArgumentParser
from storage import *
from bvh_reader import bvh_reader as bvh_reader_module
import imp
from stopwatch import Stopwatch
import threading
from event import Event
from event_listener import EventListener

from connectivity.websocket_server import WebsocketServer, ClientHandler
from connectivity.websocket_client import WebsocketClient
from connectivity.single_process_server import SingleProcessServer
from connectivity.single_process_client import SingleProcessClient

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
        parser.add_argument("-frame-rate", type=float, default=100.0)
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
        parser.add_argument("--show-fps", action="store_true")

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
        if not args.backend_only:
            self._entity_scene_module = imp.load_source("entity", "entities/%s_scene.py" % args.entity)
            self._entity_scene_module.Scene.add_parser_arguments(parser)

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
        self._running = True
        self.stopwatch = Stopwatch()
        self._frame_count = 0
        self._ui_handlers = set()

    def ui_connected(self, handler):
        self._ui_handlers.add(handler)

    def ui_disconnected(self, handler):
        self._ui_handlers.remove(handler)

    def _add_event_handlers(self):
        self.add_event_handler(Event.START, self._start)
        self.add_event_handler(Event.STOP, self._stop)
        self.add_event_handler(
            Event.SET_CURSOR,
            lambda event: self.entity.set_cursor(event.content))

    def run_backend_and_or_ui(self):
        run_backend = not self.args.ui_only
        run_ui = not self.args.backend_only

        if run_ui:
            self._scene_class = self._entity_scene_module.Scene

        if run_backend and run_ui:
            self._create_single_process_server()
            self._set_up_timed_refresh()
            self._start_server_in_new_thread()
            client = SingleProcessClient(self._server)
            self.run_ui(client)
        elif run_backend:
            self._create_websocket_server()
            self._set_up_timed_refresh()
            self._start_server()
        elif run_ui:
            client = WebsocketClient(self.args.backend_host)
            self.run_ui(client)

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

            if self.entity.processed_input is not None:
                self.send_event_to_ui(Event(Event.INPUT, self.entity.processed_input))
            self.send_event_to_ui(Event(Event.OUTPUT, self.entity.processed_output))

        self.previous_frame_time = self.now
        self._frame_count += 1

    def send_event_to_ui(self, event):
        for ui_handler in self._ui_handlers:
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

    def _create_single_process_server(self):
        self._server = SingleProcessServer(SingleProcessUiHandler, experiment=self)

    def _create_websocket_server(self):
        self._server = WebsocketServer(WebsocketUiHandler, {"experiment": self})

    def _set_up_timed_refresh(self):
        self._server.add_periodic_callback(
            self._update_and_refresh_uis, 1000. / self.args.frame_rate)

    def _start_server(self):
        self._server.start()

    def _start_server_in_new_thread(self):
        server_thread = threading.Thread(target=self._start_server)
        server_thread.daemon = True
        server_thread.start()

class SingleProcessUiHandler:
    def __init__(self, client, experiment):
        self._client = client
        self._experiment = experiment
        self._experiment.ui_connected(self)

    def send_event(self, event):
        self._client.received_event(event)

    def received_event(self, event):
        self._experiment.handle_event(event)

class WebsocketUiHandler(ClientHandler):
    def __init__(self, *args, **kwargs):
        print "UI connected"
        self._experiment = kwargs.pop("experiment")
        super(WebsocketUiHandler, self).__init__(*args, **kwargs)

    def open(self):
        self._experiment.ui_connected(self)

    def on_close(self):
        print "UI disconnected"
        self._experiment.ui_disconnected(self)

    def received_event(self, event):
        self._experiment.handle_event(event)
