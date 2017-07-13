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

from argparse import ArgumentParser
import threading
import numpy
import random

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
parser.add_argument("--mirror-weight", type=float, default=1.0)
parser.add_argument("--improvise-weight", type=float, default=1.0)
parser.add_argument("--memory-weight", type=float, default=1.0)
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

    def choose_other_than(self, not_choosable):
        while True:
            candidate = self._get_candidate()
            if candidate != not_choosable:
                return candidate

    def _get_candidate(self):
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
    
    normal_duration = 3.0
    interpolation_duration = 1.0
    
    def __init__(self, improvise):
        Behavior.__init__(self)
        self._improvise = improvise
        self._input = None
        self._output = None
        self._normal_num_frames = int(round(self.normal_duration * args.frame_rate))
        self._interpolation_num_frames = int(round(self.interpolation_duration * args.frame_rate))
        self._memory = Memory()
        self._initialize_state(self.MIRROR)

    def _create_weighted_shuffler(self):
        available_modes = [
            mode for mode in [self.MIRROR, self.IMPROVISE, self.MEMORY]
            if self._mode_is_available(mode)]
        weights = [self._get_weight(mode) for mode in available_modes]
        return WeightedShuffler(available_modes, weights)

    def _mode_is_available(self, mode):
        if mode == self.MEMORY and self._memory.get_num_frames() < self._normal_num_frames:
            return False
        return self._get_weight(mode) > 0
    
    def _get_weight(self, mode):
        weight_arg = "%s_weight" % mode
        return getattr(args, weight_arg)
    
    def _initialize_state(self, state):
        self._current_state = state
        self._state_frames = 0
        self._interpolating = False

    def proceed(self, time_increment):
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

        if set([self._current_state, self._next_state]) == set([self.MIRROR, self.IMPROVISE]):
            if self._current_state == self.MIRROR:
                input_amount = 1 - float(self._state_frames) / self._interpolation_num_frames
            else:
                input_amount = float(self._state_frames) / self._interpolation_num_frames
            improvise_amount = 1 - input_amount
            entity.set_friction(improvise_amount > 0.5)
            self._output = entity.interpolate(self._input, self._get_improvise_output(), improvise_amount)

        elif set([self._current_state, self._next_state]) == set([self.MIRROR, self.MEMORY]):
            if self._current_state == self.MIRROR:
                input_amount = 1 - float(self._state_frames) / self._interpolation_num_frames
            else:
                input_amount = float(self._state_frames) / self._interpolation_num_frames
            memory_amount = 1 - input_amount
            self._output = entity.interpolate(self._input, self._memory.get_output(), memory_amount)

        else:
            raise Exception("interpolation between %s and %s not supported" % (
                self._current_state, self._next_state))
                            
        self._state_frames += frames_to_process
        self._remaining_frames_to_process -= frames_to_process
        
    def _proceed_within_normal_state(self):
        remaining_frames_in_state = self._normal_num_frames - self._state_frames
        if remaining_frames_in_state == 0:
            self._interpolating = True
            self._state_frames = 0
            shuffler = self._create_weighted_shuffler()
            self._next_state = shuffler.choose_other_than(self._current_state)
            if self._next_state == self.MEMORY:
                self._memory.begin_random_recall(self._normal_num_frames + self._interpolation_num_frames)
            return
        frames_to_process = min(self._remaining_frames_to_process, remaining_frames_in_state)
        self._improvise.proceed(float(frames_to_process) / args.frame_rate)
        if self._current_state == self.IMPROVISE:
            entity.set_friction(True)
            self._output = self._get_improvise_output()
        elif self._current_state == self.MIRROR:
            entity.set_friction(False)
            self._output = self._input
        elif self._current_state == self.MEMORY:
            entity.set_friction(False)
            self._memory.proceed(frames_to_process)
            self._output = self._memory.get_output()
        self._state_frames += frames_to_process
        self._remaining_frames_to_process -= frames_to_process

    def sends_output(self):
        return True

    def on_input(self, input_):
        self._input = input_
        self._memory.on_input(input_)
        
    def get_output(self):
        return self._output

    def _get_improvise_output(self):
        reduction = self._improvise.get_reduction()
        return student.inverse_transform(numpy.array([reduction]))[0]
    
improvise_params = ImproviseParameters()
preferred_location = None
improvise = Improvise(
    student,
    student.num_reduced_dimensions,
    improvise_params,
    preferred_location,
    MAX_NOVELTY)
index = 0
avatar = Avatar(index, entity, MetaBehaviour(improvise))

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

application.run()
