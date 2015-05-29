import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/connectivity")
from osc_receiver import OscReceiver
from websocket_client import WebsocketClient
from event_listener import EventListener
from event import Event
from vector import Vector3d
import time
import collections
from argparse import ArgumentParser
from tracked_users_viewer import TrackedUsersViewer
from PyQt4 import QtGui

ACTIVITY_THRESHOLD = 5
ACTIVITY_CEILING = 40
MIN_VELOCITY = 0.3
MAX_VELOCITY = 1.0
MIN_NOVELTY = 0.1
MAX_NOVELTY = 1.0
MIN_PREFERRED_DISTANCE = 0.1
MAX_PREFERRED_DISTANCE = 2.0

OSC_PORT = 15002
WEBSOCKET_HOST = "localhost"
WINDOW_DURATION = 1.0
FPS = 30.0

class Joint:
    def __init__(self):
        self._previous_position = None
        self._buffer_size = int(WINDOW_DURATION * FPS)
        self._activity_buffer = collections.deque(
            [0] * self._buffer_size, maxlen=self._buffer_size)

    def get_activity(self):
        return sum(self._activity_buffer) / self._buffer_size

    def update(self, x, y, z):
        new_position = Vector3d(x, y, z)
        if self._previous_position is not None:
            movement = (new_position - self._previous_position).mag()
            self._activity_buffer.append(movement)
        self._previous_position = new_position

class User:
    def __init__(self, user_id, interpreter):
        self._user_id = user_id
        self._interpreter = interpreter
        self._joints = {"left_hand": Joint(),
                        "right_hand": Joint()}
        self._num_updated_joints = 0
        self._num_received_frames = 0
        self._activity = 0

    def handle_joint_data(self, joint_name, x, y, z):
        if joint_name in self._joints:
            joint = self._joints[joint_name]
            joint.update(x, y, z)
            self._last_updated_joint = joint_name
            self._num_updated_joints += 1
            if self._num_updated_joints == len(self._joints):
                self._num_updated_joints = 0
                self._num_received_frames += 1
                if self._num_received_frames > 1:
                    self._activity = sum([joint.get_activity() for joint in self._joints.values()]) / \
                        len(self._joints)
                    self._interpreter.user_has_new_information(self._user_id)

    def get_activity(self):
        return self._activity
    
    def get_id(self):
        return self._id

class UserMovementInterpreter:
    def __init__(self):
        self._users = {}

    def handle_joint_data(self, user_id, joint_name, x, y, z, confidence):
        if user_id not in self._users:
            self._users[user_id] = User(user_id, self)
        user = self._users[user_id]
        user.handle_joint_data(joint_name, x, y, z)

    def user_has_new_information(self, user):
        self._interpret_current_state()
        self._send_interpretation()

    def _interpret_current_state(self):
        user_activities = [user.get_activity() for user in self._users.values()]
        self._highest_user_activity = max(user_activities)

    def _send_interpretation(self):
        relative_activity = max(0, self._highest_user_activity - ACTIVITY_THRESHOLD) / \
            (ACTIVITY_CEILING - ACTIVITY_THRESHOLD)
        velocity = MIN_VELOCITY + relative_activity * (MAX_VELOCITY - MIN_VELOCITY)
        novelty = MIN_NOVELTY + relative_activity * (MAX_NOVELTY - MIN_NOVELTY)
        preferred_distance = MIN_PREFERRED_DISTANCE + relative_activity * (MAX_PREFERRED_DISTANCE - MIN_PREFERRED_DISTANCE)
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
                  {"name": "preferred_distance",
                   "value": preferred_distance}))

    def get_users(self):
        return self._users

interpreter = UserMovementInterpreter()

parser = ArgumentParser()
TrackedUsersViewer.add_parser_arguments(parser)
parser.add_argument("--with-viewer", action="store_true")
args = parser.parse_args()

if args.with_viewer:
    app = QtGui.QApplication(sys.argv)
    viewer = TrackedUsersViewer(interpreter, args)

def handle_joint_data(path, values, types, src, user_data):
    interpreter.handle_joint_data(*values)
    if args.with_viewer:
        viewer.handle_joint_data(*values)

def handle_state(path, values, types, src, user_data):
    if args.with_viewer:
        viewer.handle_state(*values)

websocket_client = WebsocketClient(WEBSOCKET_HOST)
websocket_client.set_event_listener(EventListener())
websocket_client.connect()

osc_receiver = OscReceiver(OSC_PORT)
osc_receiver.add_method("/joint", "isffff", handle_joint_data)
osc_receiver.add_method("/state", "is", handle_state)
osc_receiver.start()

if args.with_viewer:
    viewer.show()
    app.exec_()
else:
    while True:
        time.sleep(1)
