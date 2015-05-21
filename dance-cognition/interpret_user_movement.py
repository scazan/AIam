import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/connectivity")
from osc_receiver import OscReceiver
from websocket_client import WebsocketClient
from event_listener import EventListener
from event import Event
from leaky_integrator import LeakyIntegrator
from vector import Vector3d
import time

OSC_PORT = 15002
WEBSOCKET_HOST = "localhost"

class Joint:
    def __init__(self):
        self._previous_time = None
        self._activity = LeakyIntegrator(response_factor=.999)

    def get_activity(self):
        return self._activity.value()

    def update(self, x, y, z):
        now = time.time()
        new_position = Vector3d(x, y, z)
        if self._previous_time is not None:
            movement = (new_position - self._previous_position).mag()
            time_increment = now - self._previous_time
            self._activity.integrate(movement, time_increment)
        self._previous_time = now
        self._previous_position = new_position

class User:
    def __init__(self, interpreter):
        self._interpreter = interpreter
        self._joints = {"left_hand": Joint(),
                        "right_hand": Joint()}
        self._num_updated_joints = 0
        self._num_received_frames = 0
        self._activity = 0

    def handle_joint_data(self, joint_name, x, y, z):
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
                self._interpreter.user_has_new_information()

    def get_activity(self):
        return self._activity
    
class UserMovementInterpreter:
    def __init__(self):
        self._users = {}

    def handle_joint_data(self, user_id, joint_name, x, y, z):
        if user_id not in self._users:
            self._users[user_id] = User(self)
        user = self._users[user_id]
        user.handle_joint_data(joint_name, x, y, z)

    def user_has_new_information(self):
        self._interpret_current_state()
        self._send_interpretation()

    def _interpret_current_state(self):
        user_activities = [user.get_activity() for user in self._users.values()]
        self._highest_user_activity = max(user_activities)

    def _send_interpretation(self):
        # preferred_distance = novelty = average_activity * .02
        # websocket_client.send_event(
        #     Event(Event.PARAMETER,
        #           {"name": "preferred_distance",
        #            "value": preferred_distance}))
        # websocket_client.send_event(
        #     Event(Event.PARAMETER,
        #           {"name": "novelty",
        #            "value": novelty}))
        velocity = self._highest_user_activity * .02
        websocket_client.send_event(
            Event(Event.PARAMETER,
                  {"name": "velocity",
                   "value": velocity}))

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
