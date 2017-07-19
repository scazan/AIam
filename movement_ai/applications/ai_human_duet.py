#!/usr/bin/env python

# STUDENT_MODEL_PATH = "profiles/dimensionality_reduction/valencia_pn_autoencoder.model"
# SKELETON_DEFINITION = "scenes/pn-01.22_skeleton.bvh"
# DIMENSIONALITY_REDUCTION_TYPE = "AutoEncoder"
# DIMENSIONALITY_REDUCTION_ARGS = "--num-hidden-nodes=0 --learning-rate=0.005"
# ENTITY_ARGS = "-r quaternion --friction --translate"

STUDENT_MODEL_PATH = "profiles/dimensionality_reduction/valencia_pn.model"
SKELETON_DEFINITION = "scenes/pn-01.22_skeleton.bvh"
DIMENSIONALITY_REDUCTION_TYPE = "KernelPCA"
DIMENSIONALITY_REDUCTION_ARGS = ""
ENTITY_ARGS = "-r quaternion --friction --translate"

NUM_REDUCED_DIMENSIONS = 7
Z_UP = False
FLOOR = True
MAX_NOVELTY = 1.4
SLIDER_PRECISION = 1000
MAX_DELAY_SECONDS = 10

from argparse import ArgumentParser
import threading
import numpy
import random
import collections
from PyQt4 import QtGui, QtCore

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")
from application import Application, Avatar
from entities.hierarchical import Entity
from bvh.bvh_reader import BvhReader
from dimensionality_reduction.behavior import Behavior
from dimensionality_reduction.behaviors.improvise import ImproviseParameters, Improvise
from dimensionality_reduction.factory import DimensionalityReductionFactory
import tracking.pn.receiver

parser = ArgumentParser()
parser.add_argument("--pn-host", default="localhost")
parser.add_argument("--pn-port", type=int, default=tracking.pn.receiver.SERVER_PORT_BVH)
parser.add_argument("--with-ui", action="store_true")
parser.add_argument("--mirror-weight", type=float, default=1.0)
parser.add_argument("--improvise-weight", type=float, default=1.0)
parser.add_argument("--memory-weight", type=float, default=1.0)
parser.add_argument("--mirror-duration", type=float, default=3)
parser.add_argument("--improvise-duration", type=float, default=3)
parser.add_argument("--memory-duration", type=float, default=3)
Application.add_parser_arguments(parser)
ImproviseParameters().add_parser_arguments(parser)
args = parser.parse_args()
            
bvh_reader = BvhReader(SKELETON_DEFINITION)
bvh_reader.read()
entity_args_strings = ENTITY_ARGS.split()
entity_args = parser.parse_args(entity_args_strings)

pose = bvh_reader.get_hierarchy().create_pose()
entity = Entity(bvh_reader, pose, FLOOR, Z_UP, entity_args)

num_input_dimensions = entity.get_value_length()
student = DimensionalityReductionFactory.create(
    DIMENSIONALITY_REDUCTION_TYPE, num_input_dimensions, NUM_REDUCED_DIMENSIONS, DIMENSIONALITY_REDUCTION_ARGS)
student.load(STUDENT_MODEL_PATH)

class WeightedShuffler:
    def __init__(self, options, weights):
        self._options = options
        self._weights = weights
        self._weights_sum = sum(weights)

    def choice(self):
        r = random.random() * self._weights_sum
        for index, weight in enumerate(self._weights):
            r -= weight
            if r < 0:
                return self._options[index]

class Memory:
    def __init__(self):
        self._frames = []

    def on_input(self, input_):
        self._frames.append(input_)

    def get_num_frames(self):
        return len(self._frames)

    def begin_random_recall(self, num_frames_to_recall):
        max_cursor = self.get_num_frames() - num_frames_to_recall
        self._cursor = int(random.random() * max_cursor)

    def proceed(self, num_frames):
        self._cursor += num_frames

    def get_output(self):
        return self._frames[self._cursor]
    
class MetaBehaviour(Behavior):
    MIRROR = "mirror"
    IMPROVISE = "improvise"
    MEMORY = "memory"
    
    interpolation_duration = 1.0
    
    def __init__(self, improvise):
        Behavior.__init__(self)
        self._improvise = improvise
        self._input = None
        self._delayed_input = None
        self._output = None
        self._mirror_num_frames = int(round(args.mirror_duration * args.frame_rate))
        self._improvise_num_frames = int(round(args.improvise_duration * args.frame_rate))
        self._memory_num_frames = int(round(args.memory_duration * args.frame_rate))
        self._interpolation_num_frames = int(round(self.interpolation_duration * args.frame_rate))
        self._memory = Memory()
        initial_state = self._choose_initial_state()
        self._prepare_state(initial_state)
        self._initialize_state(initial_state)
        self._input_buffer_num_frames = int(MAX_DELAY_SECONDS * args.frame_rate)
        self._input_buffer = collections.deque(
            [None] * self._input_buffer_num_frames, maxlen=self._input_buffer_num_frames)
        self.set_mirror_delay_seconds(0)

    def _choose_initial_state(self):
        if args.mirror_weight > 0:
            return self.MIRROR
        elif args.improvise_weight > 0:
            return self.IMPROVISE
        elif args.memory_weight > 0:
            return self.MEMORY
        else:
            raise Exception("couldn't choose initial state")
        
    def set_mirror_delay_seconds(self, seconds):
        self._input_buffer_read_cursor = self._input_buffer_num_frames - 1 - int(seconds * args.frame_rate)
        
    def _create_weighted_shuffler(self):
        non_current_modes = set([self.MIRROR, self.IMPROVISE, self.MEMORY]) - set([self._current_state])
        available_modes = [
            mode for mode in non_current_modes
            if self._mode_is_available(mode)]
        print "available modes:", available_modes
        weights = [self._get_weight(mode) for mode in available_modes]
        return WeightedShuffler(available_modes, weights)

    def _mode_is_available(self, mode):
        if mode == self.MEMORY:
            return self._memory.get_num_frames() >= self._memory_num_frames
        return self._get_weight(mode) > 0
    
    def _get_weight(self, mode):
        weight_arg = "%s_weight" % mode
        return getattr(args, weight_arg)
    
    def _initialize_state(self, state):
        self._current_state = state
        self._state_frames = 0
        self._interpolating = False
            
    def proceed(self, time_increment):
        self._delayed_input = self._get_delayed_input()
        if self._delayed_input is None:
            return
        self._remaining_frames_to_process = int(round(time_increment * args.frame_rate))
        while self._remaining_frames_to_process > 0:
            self._proceed_within_state()

    def _proceed_within_state(self):
        if self._interpolating:
            return self._proceed_within_interpolation()
        else:
            return self._proceed_within_normal_state()
        
    def _proceed_within_interpolation(self):
        remaining_frames_in_state = self._interpolation_num_frames - self._state_frames
        if remaining_frames_in_state == 0:
            self._initialize_state(self._next_state)
            return
        frames_to_process = min(self._remaining_frames_to_process, remaining_frames_in_state)
        self._improvise.proceed(float(frames_to_process) / args.frame_rate)
        current_and_next_state = set([self._current_state, self._next_state])
        
        if current_and_next_state == set([self.MIRROR, self.IMPROVISE]):
            if self._current_state == self.MIRROR:
                input_amount = 1 - float(self._state_frames) / self._interpolation_num_frames
            else:
                input_amount = float(self._state_frames) / self._interpolation_num_frames
            improvise_amount = 1 - input_amount
            entity.set_friction(improvise_amount > 0.5)
            self._output = entity.interpolate(
                self._delayed_input, self._get_improvise_output(), improvise_amount)
            
        elif current_and_next_state == set([self.MIRROR, self.MEMORY]):
            if self._current_state == self.MIRROR:
                input_amount = 1 - float(self._state_frames) / self._interpolation_num_frames
            else:
                input_amount = float(self._state_frames) / self._interpolation_num_frames
            memory_amount = 1 - input_amount
            self._output = entity.interpolate(
                self._delayed_input, self._memory.get_output(), memory_amount)

        elif current_and_next_state == set([self.IMPROVISE, self.MEMORY]):
            if self._current_state == self.MEMORY:
                memory_amount = 1 - float(self._state_frames) / self._interpolation_num_frames
            else:
                memory_amount = float(self._state_frames) / self._interpolation_num_frames
            improvise_amount = 1 - memory_amount
            entity.set_friction(improvise_amount > 0.5)
            self._output = entity.interpolate(
                self._memory.get_output(), self._get_improvise_output(), improvise_amount)
            
        else:
            raise Exception("interpolation between %s and %s not supported" % (
                self._current_state, self._next_state))
                            
        self._state_frames += frames_to_process
        self._remaining_frames_to_process -= frames_to_process

    def _get_delayed_input(self):
        return self._input_buffer[self._input_buffer_read_cursor]
            
    def _proceed_within_normal_state(self):        
        remaining_frames_in_state = self._state_num_frames(self._current_state) - self._state_frames
        if remaining_frames_in_state == 0:
            self._interpolating = True
            self._state_frames = 0
            shuffler = self._create_weighted_shuffler()
            self._next_state = shuffler.choice()
            print "%s => %s" % (self._current_state, self._next_state)
            self._prepare_state(self._next_state)
            return
        frames_to_process = min(self._remaining_frames_to_process, remaining_frames_in_state)
        self._improvise.proceed(float(frames_to_process) / args.frame_rate)
        if self._current_state == self.IMPROVISE:
            entity.set_friction(True)
            self._output = self._get_improvise_output()
        elif self._current_state == self.MIRROR:
            entity.set_friction(False)
            self._output = self._delayed_input
        elif self._current_state == self.MEMORY:
            entity.set_friction(False)
            self._memory.proceed(frames_to_process)
            self._output = self._memory.get_output()
        self._state_frames += frames_to_process
        self._remaining_frames_to_process -= frames_to_process

    def _prepare_state(self, state):
        if state == self.MEMORY:
            self._memory.begin_random_recall(self._state_num_frames(state) + self._interpolation_num_frames)
        elif state == self.IMPROVISE:
            if self._delayed_input is None:
                self._translation_offset = [0,0,0]
            else:
                self._translation_offset = self._delayed_input[0:3]

    def _state_num_frames(self, state):
        if state == self.MIRROR:
            return self._mirror_num_frames
        elif state == self.IMPROVISE:
            return self._improvise_num_frames
        elif state == self.MEMORY:
            return self._memory_num_frames
        
    def sends_output(self):
        return True

    def on_input(self, input_):
        self._input = input_
        self._input_buffer.append(input_)
        self._memory.on_input(input_)
        
    def get_output(self):
        return self._output

    def _get_improvise_output(self):
        reduction = self._improvise.get_reduction()
        output = student.inverse_transform(numpy.array([reduction]))[0]
        output[0:3] += self._translation_offset
        return output
    
class UiWindow(QtGui.QWidget):
    def __init__(self, meta_behavior):
        QtGui.QWidget.__init__(self)
        self._meta_behavior = meta_behavior
        self._layout = QtGui.QVBoxLayout()
        self.setLayout(self._layout)

        delay_layout = self._create_delay_layout()
        self._layout.addLayout(delay_layout)
        
        timer = QtCore.QTimer(self)
        timer.setInterval(1000. / args.frame_rate)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), application.update)
        timer.start()

    def _create_delay_layout(self):
        layout = QtGui.QHBoxLayout()
        self._delay_slider = self._create_delay_slider()
        layout.addWidget(self._delay_slider)
        self._delay_label = QtGui.QLabel("")
        layout.addWidget(self._delay_label)
        self._on_changed_delay_slider()
        return layout

    def _create_delay_slider(self):
        slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, SLIDER_PRECISION)
        slider.setSingleStep(1)
        slider.setValue(0.0)
        slider.valueChanged.connect(lambda value: self._on_changed_delay_slider())
        return slider

    def _on_changed_delay_slider(self):
        delay_seconds = float(self._delay_slider.value()) / SLIDER_PRECISION * MAX_DELAY_SECONDS
        self._delay_label.setText("%.1f" % delay_seconds)
        self._meta_behavior.set_mirror_delay_seconds(delay_seconds)

improvise_params = ImproviseParameters()
preferred_location = None
improvise = Improvise(
    student,
    student.num_reduced_dimensions,
    improvise_params,
    preferred_location,
    MAX_NOVELTY)
index = 0
meta_behavior = MetaBehaviour(improvise)
avatar = Avatar(index, entity, meta_behavior)

avatars = [avatar]

application = Application(student, avatars, args)

def receive_from_pn(pn_entity):
    for frame in pn_receiver.get_frames():
        input_from_pn = pn_entity.get_value_from_frame(frame)
        application.set_input(input_from_pn)
        
pn_receiver = tracking.pn.receiver.PnReceiver()
print "connecting to PN server..."
pn_receiver.connect(args.pn_host, args.pn_port)
print "ok"
pn_pose = bvh_reader.get_hierarchy().create_pose()
pn_entity = Entity(bvh_reader, pn_pose, FLOOR, Z_UP, entity_args)
pn_receiver_thread = threading.Thread(target=lambda: receive_from_pn(pn_entity))
pn_receiver_thread.daemon = True
pn_receiver_thread.start()

if args.with_ui:
    qt_app = QtGui.QApplication(sys.argv)
    ui_window = UiWindow(meta_behavior)
    ui_window.show()
    qt_app.exec_()
else:
    application.run()
