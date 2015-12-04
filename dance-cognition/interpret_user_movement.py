import time
import collections
from argparse import ArgumentParser
from PyQt4 import QtGui
import cPickle
import threading
import math
import numpy

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/connectivity")
from osc_receiver import OscReceiver
from websocket_client import WebsocketClient
from event_listener import EventListener
from event import Event
from tracked_users_viewer import TrackedUsersViewer
from transformations import rotation_matrix
from filters import OneEuroFilter

# WAITING_PARAMETERS = {
#     "velocity": 0.6,
#     "novelty": 0.3,
#     "extension": 1.0,
#     "location_preference": 0.5,
# }

PASSIVE_PARAMETERS = {
    "velocity": 0.3,
    "novelty": 0.03,
    "extension": 0.02,
    "location_preference": 1.0,
}

WAITING_PARAMETERS = PASSIVE_PARAMETERS

INTENSE_PARAMETERS = {
    "velocity": 1.0,
    "novelty": 1.0,
    "extension": 2.0,
    "location_preference": 0.0,
}

INTENSITY_THRESHOLD = 5
INTENSITY_CEILING = 80
FPS = 30.0
NUM_JOINTS_IN_SKELETON = 15
JOINTS_DETERMNING_INTENSITY = ["left_hand", "right_hand"]
CONSIDERED_JOINTS = JOINTS_DETERMNING_INTENSITY + ["torso"]

OSC_PORT = 15002
WEBSOCKET_HOST = "localhost"

class Joint:
    def __init__(self, interpreter):
        self._interpreter = interpreter
        self._previous_position = None
        self._buffer_size = max(int(args.intensity_smoothing_factor * FPS), 1)
        self._intensity_buffer = collections.deque(
            [0] * self._buffer_size, maxlen=self._buffer_size)

        if args.enable_1euro_filter:
            self._1euro_filters = [self._create_1euro_filter()
                                   for n in range(3)]

    def _create_1euro_filter(self):
        return OneEuroFilter(
            freq=FPS,
            mincutoff=args.one_euro_mincutoff,
            beta=args.one_euro_beta,
            dcutoff=args.one_euro_dcutoff)

    def get_position(self):
        return self._interpreter.adjust_tracked_position(self._previous_position)

    def get_confidence(self):
        return self._confidence

    def get_intensity(self):
        return sum(self._intensity_buffer) / self._buffer_size

    def set_position(self, *vector):
        if args.enable_1euro_filter:
            vector = [one_euro_filter(value)
                      for one_euro_filter, value in zip(self._1euro_filters, vector)]
            
        new_position = numpy.array(vector)
        if self._previous_position is not None:
            movement = numpy.linalg.norm(new_position - self._previous_position)
            self._intensity_buffer.append(movement)
        self._previous_position = new_position

    def set_confidence(self, confidence):
        self._confidence = confidence

class User:
    def __init__(self, user_id, interpreter):
        self._user_id = user_id
        self._interpreter = interpreter
        self._joints = {}
        self._num_updated_joints = 0
        self._intensity = 0
        self._distance_to_center = None

    def handle_joint_data(self, joint_name, x, y, z, confidence):
        if self._should_consider_joint(joint_name):
            self._process_joint_data(joint_name, x, y, z, confidence)

    def _should_consider_joint(self, joint_name):
        if args.with_viewer:
            return True
        else:
            return joint_name in CONSIDERED_JOINTS

    def _process_joint_data(self, joint_name, x, y, z, confidence):
        self._ensure_joint_exists(joint_name)
        joint = self._joints[joint_name]
        joint.set_position(x, y, z)
        joint.set_confidence(confidence)
        if joint_name == "torso":
            self._distance_to_center = None
        self._last_updated_joint = joint_name
        self._num_updated_joints += 1
        if self._num_updated_joints >= self._interpreter.num_considered_joints:
            self._process_frame()

    def _ensure_joint_exists(self, joint_name):
        if joint_name not in self._joints:
            self._joints[joint_name] = Joint(self._interpreter)

    def _process_frame(self):
        self._intensity = self._measure_intensity()
        self._num_updated_joints = 0

    def _measure_intensity(self):
        return sum([
            self.get_joint(joint_name).get_intensity()
            for joint_name in JOINTS_DETERMNING_INTENSITY]) / \
                len(JOINTS_DETERMNING_INTENSITY)

    def get_intensity(self):
        return self._intensity
    
    def get_id(self):
        return self._user_id

    def get_joint(self, name):
        return self._joints[name]

    def has_complete_joint_data(self):
        return len(self._joints) >= self._interpreter.num_considered_joints

    def get_distance_to_center(self):
        if self._distance_to_center is None:
            self._distance_to_center = self._measure_distance_to_center()
        return self._distance_to_center

    def _measure_distance_to_center(self):
        torso_x, torso_y, torso_z = self.get_joint("torso").get_position()
        dx = torso_x - self._interpreter.active_area_center_x
        dz = torso_z - self._interpreter.active_area_center_z
        return math.sqrt(dx*dx + dz*dz)

class UserMovementInterpreter:
    WAITING = "waiting"
    ADAPTING_TO_USER = "adapting to user"

    def __init__(self, output_controller, log_target=None, log_source=None):
        self._output_controller = output_controller
        self.intensity_ceiling = INTENSITY_CEILING
        self.active_area_center_x, self.active_area_center_z = [
            float(s) for s in args.active_area_center.split(",")]
        self.active_area_radius = args.active_area_radius
        self.tracker_y_position, tracker_pitch = map(float, args.tracker.split(","))
        self.set_tracker_pitch(tracker_pitch)
        self._reset()

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
        else:
            self._writing_to_log = False

        if args.with_viewer:
            self.num_considered_joints = NUM_JOINTS_IN_SKELETON
        else:
            self.num_considered_joints = len(CONSIDERED_JOINTS)

    def set_up_osc_receiver(self):
        osc_receiver = OscReceiver(OSC_PORT)
        osc_receiver.add_method("/begin_session", "", self._handle_begin_session)
        osc_receiver.add_method("/begin_frame", "f", self._handle_begin_frame)
        osc_receiver.add_method("/joint", "isffff", self._handle_joint_data)
        osc_receiver.add_method("/state", "is", self._handle_user_state)
        osc_receiver.start()

    def _handle_begin_session(self, path, values, types, src, user_data):
        self._reset()

    def _reset(self):
        self._frame = None
        self._users = {}
        self._selected_user = None
        self._system_state = self.WAITING
        self._previous_system_state = None

    def get_system_state(self):
        return self._system_state

    def get_tracker_pitch(self):
        return self._tracker_pitch

    def set_tracker_pitch(self, pitch):
        self._tracker_pitch = pitch
        self._tracker_rotation_matrix = rotation_matrix(
            math.radians(self._tracker_pitch), [1, 0, 0])

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

    def _handle_begin_frame(self, path, values, types, src, user_data):
        (timestamp,) = values
        if self._frame is not None:
            self._process_frame()
            if self._writing_to_log:
                self._log_frame()
        self._frame = {"timestamp": timestamp,
                       "user_states": [],
                       "joint_data": []}

    def _handle_joint_data(self, path, values, types, src, user_data):
        user_id, joint_name, x, y, z, confidence = values
        if self._frame is not None:
            self._frame["joint_data"].append((user_id, joint_name, x, y, z, confidence))

    def _handle_user_state(self, path, values, types, src, user_data):
        user_id, state = values
        if self._frame is not None:
            self._frame["user_states"].append((user_id, state))

    def _process_frame(self):
        for values in self._frame["user_states"]:
            self._process_user_state(*values)
        for values in self._frame["joint_data"]:
            self._process_joint_data(*values)

        self._select_user()
        system_state_changed = self._update_system_state()

        parameters = self._select_parameters_in_system_state()
        self._output_controller.send_parameters(parameters)

        if system_state_changed:
            self._output_controller.abort_path()
            if args.with_viewer:
                viewer.log(self._frame["timestamp"], "aborting path")
                viewer.log(self._frame["timestamp"], self._system_state)

        if args.with_viewer:
            viewer.process_frame(self._frame)

    def _process_joint_data(self, user_id, joint_name, x, y, z, confidence):
        if user_id not in self._users:
            self._users[user_id] = User(user_id, self)
        user = self._users[user_id]
        user.handle_joint_data(joint_name, x, y, z, confidence)

    def _process_user_state(self, user_id, state):
        if state == "lost":
            try:
                del self._users[user_id]
            except KeyError:
                pass

    def adjust_tracked_position(self, position):
        unadjusted_vector = [position[0], position[1], position[2], 1]
        rotated_vector = numpy.dot(self._tracker_rotation_matrix, unadjusted_vector)
        adjusted_vector = numpy.array([
            rotated_vector[0],
            rotated_vector[1] + self.tracker_y_position,
            rotated_vector[2]])
        return adjusted_vector

    def get_selected_user(self):
        return self._selected_user

    def _select_user(self):
        users_within_active_area = [
            user for user in self.get_users()
            if self._is_within_active_area(user)]
        if len(users_within_active_area) > 0:
            self._selected_user = min(
                users_within_active_area,
                key=lambda user: user.get_distance_to_center())
        else:
            self._selected_user = None

    def _is_within_active_area(self, user):
        return user.get_distance_to_center() < self.active_area_radius

    def _update_system_state(self):
        self._previous_system_state = self._system_state
        if self._selected_user is None:
            self._system_state = self.WAITING
        else:
            self._system_state = self.ADAPTING_TO_USER
        return self._system_state != self._previous_system_state

    def _select_parameters_in_system_state(self):
        if self._system_state == self.WAITING:
            return WAITING_PARAMETERS
        elif self._system_state == self.ADAPTING_TO_USER:
            relative_intensity = self._get_relative_intensity()
            return self._output_controller.intensity_to_output_parameters(relative_intensity)

    def _get_relative_intensity(self):
        return max(0, self._selected_user.get_intensity() - INTENSITY_THRESHOLD) / \
            (self.intensity_ceiling - INTENSITY_THRESHOLD)

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

class OutputController:
    def __init__(self, event_sender):
        self._event_sender = event_sender

    def intensity_to_output_parameters(self, relative_intensity):
        return self._interpolate_parameters(
            PASSIVE_PARAMETERS, INTENSE_PARAMETERS, relative_intensity)

    def _interpolate_parameters(self, low_parameters, high_parameters, interpolation_value):
        result = {}
        for name in ["velocity", "novelty", "extension", "location_preference"]:
            low_value = low_parameters[name]
            high_value = high_parameters[name]
            value = low_value + (high_value - low_value) * interpolation_value
            result[name] = value
        return result

    def send_parameters(self, parameters):
        for name, value in parameters.iteritems():
            self._event_sender.send_event(
                Event(Event.PARAMETER,
                      {"name": name,
                       "value": value}))

    def abort_path(self):
        self._event_sender.send_event(Event(Event.ABORT_PATH))

class MockEventSender:
    def send_event(self, event):
        pass

parser = ArgumentParser()
TrackedUsersViewer.add_parser_arguments(parser)
parser.add_argument("--tracker", help="posY,pitch", default="0,0")
parser.add_argument("--active-area-center", default="0,2500")
parser.add_argument("--active-area-radius", type=float, default=1500)
parser.add_argument("--with-viewer", action="store_true")
parser.add_argument("--without-sending", action="store_true")
parser.add_argument("--intensity-smoothing-factor", type=float, default=0.5)
parser.add_argument("--enable-1euro-filter", action="store_true", default=True)
parser.add_argument("--1euro-mincutoff", dest="one_euro_mincutoff", type=float, default=0.3)
parser.add_argument("--1euro-beta", dest="one_euro_beta", type=float, default=0.001)
parser.add_argument("--1euro-dcutoff", dest="one_euro_dcutoff", type=float, default=1.0)
parser.add_argument("--log-source")
parser.add_argument("--log-target")
parser.add_argument("--profile", action="store_true")
parser.add_argument("--simulate-via-midi", action="store_true")
parser.add_argument("--midi-port")
parser.add_argument("--midi-command", type=int)
parser.add_argument("--midi-channel", type=int)
parser.add_argument("--calibrate-midi", action="store_true")
args = parser.parse_args()

if args.without_sending:
    event_sender = MockEventSender()
else:
    event_sender = WebsocketClient(WEBSOCKET_HOST)
    event_sender.set_event_listener(EventListener())
    event_sender.connect()

output_controller = OutputController(event_sender)

if args.simulate_via_midi:
    from simulate_input_via_midi import MidiInterpreter
    interpreter = MidiInterpreter(
        output_controller,
        midi_port=args.midi_port,
        command=args.midi_command,
        channel=args.midi_channel,
        calibrate=args.calibrate_midi)
    interpreter.main_loop()
else:
    interpreter = UserMovementInterpreter(
        output_controller,
        log_target=args.log_target,
        log_source=args.log_source)

    if args.with_viewer:
        app = QtGui.QApplication(sys.argv)
        viewer = TrackedUsersViewer(interpreter, args,
                                    enable_log_replay=args.log_source)

    if args.log_source:
        interpreter.process_log_in_new_thread()
    else:
        interpreter.set_up_osc_receiver()

    if args.profile:
        import yappi
        yappi.start()

    if args.with_viewer:
        viewer.show()
        app.exec_()
    else:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    if args.profile:
        yappi.get_func_stats().print_all()
