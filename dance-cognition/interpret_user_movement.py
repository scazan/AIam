import time
import collections
from argparse import ArgumentParser
from PyQt4 import QtGui
import cPickle
import threading

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/connectivity")
from osc_receiver import OscReceiver
from websocket_client import WebsocketClient
from event_listener import EventListener
from event import Event
from vector import Vector3d
from tracked_users_viewer import TrackedUsersViewer

ACTIVITY_THRESHOLD = 5
ACTIVITY_CEILING = 80
MIN_VELOCITY = 0.3
MAX_VELOCITY = 1.0
MIN_NOVELTY = 0.03
MAX_NOVELTY = 1.0
MIN_EXTENSION = 0.02
MAX_EXTENSION = 2.0
MIN_LOCATION_PREFERENCE = 0.0
MAX_LOCATION_PREFERENCE = 1.0
RESPONSE_TIME = 0
JOINT_SMOOTHING_DURATION = 1.0
FPS = 30.0
NUM_JOINTS = 15
SELECTED_JOINTS = ["left_hand", "right_hand"]

OSC_PORT = 15002
WEBSOCKET_HOST = "localhost"

class Joint:
    def __init__(self):
        self._previous_position = None
        self._buffer_size = int(JOINT_SMOOTHING_DURATION * FPS)
        self._activity_buffer = collections.deque(
            [0] * self._buffer_size, maxlen=self._buffer_size)

    def get_position(self):
        return self._previous_position

    def get_confidence(self):
        return self._confidence

    def get_activity(self):
        return sum(self._activity_buffer) / self._buffer_size

    def set_position(self, x, y, z):
        new_position = Vector3d(x, y, z)
        if self._previous_position is not None:
            movement = (new_position - self._previous_position).mag()
            self._activity_buffer.append(movement)
        self._previous_position = new_position

    def set_confidence(self, confidence):
        self._confidence = confidence

class User:
    def __init__(self, user_id, interpreter):
        self._user_id = user_id
        self._interpreter = interpreter
        self._joints = {}
        self._num_updated_joints = 0
        self._num_received_frames = 0
        self._activity = 0

    def handle_joint_data(self, joint_name, x, y, z, confidence):
        if joint_name not in self._joints:
            self._joints[joint_name] = Joint()
        joint = self._joints[joint_name]
        joint.set_position(x, y, z)
        joint.set_confidence(confidence)
        self._last_updated_joint = joint_name
        self._num_updated_joints += 1
        if self._num_updated_joints >= NUM_JOINTS:
            self._num_updated_joints = 0
            self._num_received_frames += 1
            if self._num_received_frames > 1:
                self._activity = sum([
                        self.get_joint(joint_name).get_activity()
                        for joint_name in SELECTED_JOINTS]) / \
                    len(SELECTED_JOINTS)
                self._interpreter.user_has_new_information(self._user_id)

    def get_activity(self):
        return self._activity
    
    def get_id(self):
        return self._user_id

    def get_joint(self, name):
        return self._joints[name]

    def has_complete_joint_data(self):
        return len(self._joints) >= NUM_JOINTS

class UserMovementInterpreter:
    def __init__(self, send_interpretations=True, log_target=None, log_source=None):
        self._send_interpretations = send_interpretations
        self._frame = None
        self._users = {}
        self._response_buffer_size = max(1, int(RESPONSE_TIME * FPS))
        self._response_buffer = []
        self._selected_user = None
        self.activity_ceiling = ACTIVITY_CEILING
        self.center_x, self.center_z = [float(s) for s in args.center_position.split(",")]

        if log_source:
            self._read_log(log_source)
            self._reading_from_log = True
            self._current_log_time = None
            self.log_replay_speed = 1
        else:
            self._reading_from_log = False

        if log_target:
            self._writing_to_log = True
            if os.path.exists(log_target):
                raise Exception("log target %r already exists" % log_target)
            self._log_target_file = open(log_target, "w")
            self._log_start_time = None
        else:
            self._writing_to_log = False

    def _read_log(self, filename):
        print "reading log file %s..." % filename
        f = open(filename, "r")
        self._log_entries = []
        try:
            while True:
                entry = cPickle.load(f)
                self._log_entries.append(entry)
        except EOFError:
            pass
        f.close()
        print "ok"

    def handle_begin_frame(self, timestamp):
        if self._frame is not None:
            self._process_frame()
            if self._writing_to_log:
                self._log_frame()
        self._frame = {"timestamp": timestamp,
                       "states": [],
                       "joint_data": []}

    def handle_joint_data(self, user_id, joint_name, x, y, z, confidence):
        self._frame["joint_data"].append((user_id, joint_name, x, y, z, confidence))

    def handle_state(self, user_id, state):
        self._frame["states"].append((user_id, state))

    def _process_frame(self):
        for values in self._frame["states"]:
            self._process_state(*values)
        for values in self._frame["joint_data"]:
            self._process_joint_data(*values)
        if args.with_viewer:
            viewer.process_frame(self._frame)

    def _process_joint_data(self, user_id, joint_name, x, y, z, confidence):
        if user_id not in self._users:
            self._users[user_id] = User(user_id, self)
        user = self._users[user_id]
        user.handle_joint_data(joint_name, x, y, z, confidence)

    def _process_state(self, user_id, state):
        if state == "lost":
            try:
                del self._users[user_id]
            except KeyError:
                pass

    def get_selected_user(self):
        return self._selected_user

    def user_has_new_information(self, user):
        self._select_user()
        if self._send_interpretations and self._selected_user is not None:
            self._add_interpretation_to_response_buffer()
            self._send_interpretation_from_response_buffer()

    def _select_user(self):
        users = self.get_users()
        if len(users) > 0:
            self._selected_user = min(
                users, key=lambda user: self._distance_to_center(user))

    def _distance_to_center(self, user):
        torso_x, torso_y, torso_z = user.get_joint("torso").get_position()
        dx = torso_x - self.center_x
        dz = torso_z - self.center_z
        return dx*dx + dz*dz

    def _add_interpretation_to_response_buffer(self):
        relative_activity = max(0, self._selected_user.get_activity() - ACTIVITY_THRESHOLD) / \
            (self.activity_ceiling - ACTIVITY_THRESHOLD)
        velocity = MIN_VELOCITY + relative_activity * (MAX_VELOCITY - MIN_VELOCITY)
        novelty = MIN_NOVELTY + relative_activity * (MAX_NOVELTY - MIN_NOVELTY)
        extension = MIN_EXTENSION + relative_activity * (MAX_EXTENSION - MIN_EXTENSION)
        location_preference = MIN_LOCATION_PREFERENCE + (1-relative_activity) \
            * (MAX_LOCATION_PREFERENCE - MIN_LOCATION_PREFERENCE)
        self._response_buffer.append((velocity, novelty, extension, location_preference))

    def _send_interpretation_from_response_buffer(self):
        while len(self._response_buffer) >= self._response_buffer_size:
            velocity, novelty, extension, location_preference = self._response_buffer.pop(0)
            websocket_client.send_event(
                Event(Event.PARAMETER,
                      {"name": "velocity",
                       "value": velocity}))
            websocket_client.send_event(
                Event(Event.PARAMETER,
                      {"name": "novelty",
                       "value": novelty}))
            websocket_client.send_event(
                Event(Event.PARAMETER,
                      {"name": "extension",
                       "value": extension}))
            websocket_client.send_event(
                Event(Event.PARAMETER,
                      {"name": "location_preference",
                       "value": location_preference}))

    def get_users(self):
        return [user for user in self._users.values()
                if user.has_complete_joint_data()]

    def _log_frame(self):
        self._log_target_file.write(cPickle.dumps(self._frame))

    def process_log_in_new_thread(self):
        thread = threading.Thread(name="process_log", target=self._process_log)
        thread.daemon = True
        thread.start()

    def _process_log(self):
        while True:
            if len(self._log_entries) == 0:
                print "finished processing log"
                return
            self._frame = self._log_entries.pop(0)
            t = self._frame["timestamp"] / 1000
            if self._current_log_time is None:
                self._current_log_time = t
            else:
                self._sleep_until(t)
            self._process_frame()

    def _sleep_until(self, t, max_sleep_duration=1.0):
        while self._current_log_time < t:
            sleep_duration = min(t - self._current_log_time, max_sleep_duration)
            time.sleep(sleep_duration)
            self._current_log_time += sleep_duration * self.log_replay_speed
        

parser = ArgumentParser()
TrackedUsersViewer.add_parser_arguments(parser)
parser.add_argument("--center-position", default="0,3000")
parser.add_argument("--with-viewer", action="store_true")
parser.add_argument("--without-sending", action="store_true")
parser.add_argument("--log-source")
parser.add_argument("--log-target")
args = parser.parse_args()

interpreter = UserMovementInterpreter(
    send_interpretations=not args.without_sending,
    log_target=args.log_target,
    log_source=args.log_source)

if args.with_viewer:
    app = QtGui.QApplication(sys.argv)
    viewer = TrackedUsersViewer(interpreter, args,
                                enable_log_replay=args.log_source)

def handle_begin_frame(path, values, types, src, user_data):
    interpreter.handle_begin_frame(*values)

def handle_joint_data(path, values, types, src, user_data):
    interpreter.handle_joint_data(*values)

def handle_state(path, values, types, src, user_data):
    interpreter.handle_state(*values)

if not args.without_sending:
    websocket_client = WebsocketClient(WEBSOCKET_HOST)
    websocket_client.set_event_listener(EventListener())
    websocket_client.connect()

if args.log_source:
    interpreter.process_log_in_new_thread()
else:
    osc_receiver = OscReceiver(OSC_PORT)
    osc_receiver.add_method("/begin_frame", "f", handle_begin_frame)
    osc_receiver.add_method("/joint", "isffff", handle_joint_data)
    osc_receiver.add_method("/state", "is", handle_state)
    osc_receiver.start()

if args.with_viewer:
    viewer.show()
    app.exec_()
else:
    while True:
        time.sleep(1)
