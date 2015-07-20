import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from argparse import ArgumentParser
from storage import *
from bvh.bvh_reader.bvh_collection import BvhCollection
import imp
from stopwatch import Stopwatch
import threading
from event import Event
from event_listener import EventListener
from bvh.bvh_writer import BvhWriter
import glob
import subprocess

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
        self.pose = experiment.pose

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
        parser.add_argument("--websockets", action="store_true",
                            help="Force websockets support (enabled automatically by --backend-only)")
        parser.add_argument("--no-websockets", action="store_true",
                            help="Force running without websockets support (e.g when combing --ui-only and --event-log-source)")
        parser.add_argument("--launch-when-ready", help="Run command when websocket server ready")
        parser.add_argument("--output-receiver-host")
        parser.add_argument("--output-receiver-port", type=int, default=10000)
        parser.add_argument("--output-receiver-type", choices=["bvh", "world"], default="bvh")

    def __init__(self, parser, event_handlers={}):
        event_handlers.update({
                Event.START: self._start,
                Event.STOP: self._stop,
                Event.START_EXPORT_BVH: self._start_export_bvh,
                Event.STOP_EXPORT_BVH: self._stop_export_bvh,
                Event.SET_CURSOR: self.update_cursor,
                Event.PROCEED_TO_NEXT_FRAME: self._proceed_to_next_frame,
                })
        EventListener.__init__(self, handlers=event_handlers)

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
            self.add_ui_parser_arguments(parser)

        args = parser.parse_args()
        if args.profile:
            args = parser.parse_args(profile_args_strings, namespace=args)

        if args.output_receiver_host:
            from simple_osc_sender import OscSender
            self._output_sender = OscSender(
                port=args.output_receiver_port, host=args.output_receiver_host)
        else:
            self._output_sender = None

        self.args = args
        if args.bvh:
            bvh_filenames = glob.glob(args.bvh)
            self.bvh_reader = BvhCollection(bvh_filenames)
            self.bvh_reader.read()
            self.bvh_writer = BvhWriter(self.bvh_reader.get_hierarchy(), self.bvh_reader.get_frame_time())
            self.pose = self.bvh_reader.get_hierarchy().create_pose()
        else:
            self.bvh_reader = None
            self.pose = None
        self.input = None
        self.output = None
        self.entity = entity_class(self)
        self._running = True
        self.stopwatch = Stopwatch()
        self._frame_count = 0
        self._ui_handlers = set()
        self._ui_handlers_lock = threading.Lock()
        self._exporting_output = False

    def ui_connected(self, handler):
        with self._ui_handlers_lock:
            self._ui_handlers.add(handler)

    def ui_disconnected(self, handler):
        with self._ui_handlers_lock:
            if handler in self._ui_handlers:
                self._ui_handlers.remove(handler)

    def update_cursor(self, event):
        self.entity.set_cursor(event.content)

    def add_ui_parser_arguments(self, parser):
        from ui.ui import MainWindow
        MainWindow.add_parser_arguments(parser)

    def run_backend_and_or_ui(self):
        run_backend = not self.args.ui_only
        run_ui = not self.args.backend_only

        if run_ui:
            self._scene_class = self._entity_scene_module.Scene

        if run_backend and run_ui:
            if self.args.websockets:
                websocket_server = self._create_websocket_server()
                self._start_in_new_thread(websocket_server)

            self._server = self._create_single_process_server()
            self._set_up_timed_refresh()
            self._start_in_new_thread(self._server)
            client = SingleProcessClient(self._server)
            self.run_ui(client)
        elif run_backend:
            self._server = self._create_websocket_server()
            self._set_up_timed_refresh()
            self._server.start()
        elif run_ui:
            if self.args.no_websockets:
                client = None
            else:
                client = WebsocketClient(self.args.backend_host)
            self.run_ui(client)

    def _start(self, event):
        self._running = True

    def _stop(self, event):
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

                if self.output is not None:
                    if (self._server.client_subscribes_to(Event.OUTPUT) or
                        self._output_sender and self.args.output_receiver_type == "world"):
                        self.processed_output = self.entity.process_output(self.output)
                        self.send_event_to_ui(Event(Event.OUTPUT, self.processed_output))

        self.previous_frame_time = self.now
        self._frame_count += 1

        if self._exporting_output:
            self._export_bvh()
        if self._output_sender:
            self._send_output()

    def _proceed_to_next_frame(self, event):
        self.time_increment = 1. / self.args.frame_rate
        self.proceed()

        self.entity.update()
        self.update()

        self.processed_output = self.entity.process_output(self.output)
        self.send_event_to_ui(Event(Event.OUTPUT, self.processed_output))

    def send_event_to_ui(self, event):
        with self._ui_handlers_lock:
            for ui_handler in self._ui_handlers:
                if event.source is None or event.source != ui_handler:
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
        return SingleProcessServer(SingleProcessUiHandler, experiment=self)

    def _create_websocket_server(self):
        server = WebsocketServer(WebsocketUiHandler, {"experiment": self})
        print "websocket server ready"
        self._invoke_potential_launcher_in_args()
        return server

    def _invoke_potential_launcher_in_args(self):
        if self.args.launch_when_ready:
            print "launching %r" % self.args.launch_when_ready
            self._launched_process = subprocess.Popen(self.args.launch_when_ready, shell=True)

    def _set_up_timed_refresh(self):
        self._server.add_periodic_callback(
            self._update_and_refresh_uis, 1000. / self.args.frame_rate)

    def _start_in_new_thread(self, server):
        server_thread = threading.Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()

    def _start_export_bvh(self, event):
        print "exporting BVH"
        self._exporting_output = True

    def _stop_export_bvh(self, event):
        if not os.path.exists(self.args.export_dir):
            os.mkdir(self.args.export_dir)
        export_path = self._get_export_path()
        print "saving export to %s" % export_path
        self.bvh_writer.write(export_path)
        self._exporting_output = False

    def _get_export_path(self):
        i = 1
        while True:
            path = "%s/export%03d.bvh" % (self.args.export_dir, i)
            if not os.path.exists(path):
                return path
            i += 1

    def _export_bvh(self):
        if self.output is not None:
            self.entity.parameters_to_processed_pose(self.output, self.pose)
            frame = self.pose_to_bvh_frame(self.pose)
            self.bvh_writer.add_frame(frame)

    def _send_output(self):
        if self.output is not None:
            self.entity.parameters_to_processed_pose(self.output, self.pose)
            if self.args.output_receiver_type == "bvh":
                self._send_output_bvh_recurse(self.pose.get_root_joint())
            elif self.args.output_receiver_type == "world":
                self._send_output_world()

    def pose_to_bvh_frame(self, pose):
        return self._joint_to_bvh_frame(pose.get_root_joint())

    def _joint_to_bvh_frame(self, joint):
        result = []
        for channel in joint.definition.channels:
            result.append(self._bvh_channel_data(joint, channel))
        for child in joint.children:
            result += self._joint_to_bvh_frame(child)
        return result

    def _bvh_channel_data(self, joint, channel):
        return getattr(joint, channel)()

    def _send_output_bvh_recurse(self, joint):
        if not joint.definition.has_parent and self.args.translate:
            self._send_output_joint_translation(joint)
        if joint.definition.has_rotation:
            self._send_output_joint_orientation(joint)
        for child in joint.children:
            self._send_output_bvh_recurse(child)

    def _send_output_joint_translation(self, joint):
        self._output_sender.send(
            "/translation", self._frame_count, joint.definition.index,
            joint.worldpos[0], joint.worldpos[1], joint.worldpos[2])

    def _send_output_joint_orientation(self, joint):
        self._output_sender.send(
            "/orientation", self._frame_count, joint.definition.index,
            *joint.angles)

    def _send_output_world(self):
        for index, worldpos in enumerate(self.processed_output):
            self._output_sender.send(
                "/world", self._frame_count, index,
                worldpos[0], worldpos[1], worldpos[2])

class SingleProcessUiHandler:
    def __init__(self, client, experiment):
        self._client = client
        self._experiment = experiment
        self._experiment.ui_connected(self)

    def send_event(self, event):
        self._client.received_event(event)

    def received_event(self, event, source):
        event.source = source
        self._experiment.handle_event(event)

class WebsocketUiHandler(ClientHandler):
    def __init__(self, *args, **kwargs):
        print "UI connected"
        self._experiment = kwargs.pop("experiment")
        super(WebsocketUiHandler, self).__init__(*args, **kwargs)

    def registered(self):
        print "UI registered"
        self._experiment.ui_connected(self)

    def on_close(self):
        print "UI disconnected"
        super(WebsocketUiHandler, self).on_close()
        self._experiment.ui_disconnected(self)

    def received_event(self, event, source):
        event.source = source
        self._experiment.handle_event(event)
