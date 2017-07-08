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
ENTITY_ARGS = "-r quaternion --friction"

NUM_REDUCED_DIMENSIONS = 7
Z_UP = False
FLOOR = True
MAX_NOVELTY = 1.4

from argparse import ArgumentParser
import sched
import time
import numpy
import random

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from entities.hierarchical import Entity
from bvh.bvh_reader import BvhReader
from stopwatch import Stopwatch
from dimensionality_reduction.behaviors.improvise import ImproviseParameters, Improvise
from dimensionality_reduction.factory import DimensionalityReductionFactory

class Avatar:
    def __init__(self, index, student, entity, behavior):
        self.index = index
        self.student = student
        self.entity = entity
        self.behavior = behavior
        
class Application:
    def __init__(self, avatars, output_sender, args):
        self._avatars = avatars
        self._output_sender = output_sender
        self._args = args
        
    def run(self):
        self._input = None
        self._now = None
        self._stopwatch = Stopwatch()
        self._scheduler = sched.scheduler(time.time, time.sleep)
        self._add_periodic_callback(self._update, 1000. / self._args.frame_rate)
        while True:
            self._scheduler.run()

    def _add_periodic_callback(self, action, delay_msecs):
        delay = float(delay_msecs) / 1000
        callback = PeriodicCallback(self._scheduler, action, delay)
        callback.schedule()

    def _update(self):
        if self._now is None:
            self._now = 0
            self._frame_count = 0
            self._stopwatch.start()
        else:
            self._now = self._stopwatch.get_elapsed_time()
            self._time_increment = self._now - self.previous_frame_time
            for avatar in avatars:
                avatar.behavior.proceed(self._time_increment)
                avatar.entity.update()
                reduction = avatar.behavior.get_reduction(self._input)
                if reduction is not None:
                    output = avatar.student.inverse_transform(numpy.array([reduction]))[0]
                    processed_output = avatar.entity.process_output(output)
                    if self._output_sender is not None:
                        self._send_output(avatar.index, processed_output)

        self.previous_frame_time = self._now
        self._frame_count += 1

    def _send_output(self, avatar_index, processed_output):
        self._output_sender.send("/avatar_begin", avatar_index)
        for index, worldpos in enumerate(processed_output):
            self._output_sender.send(
                "/world", self._frame_count, index,
                worldpos[0], worldpos[1], worldpos[2])
        self._output_sender.send("/avatar_end")

class PeriodicCallback:
    def __init__(self, scheduler, action, delay):
        self.scheduler = scheduler
        self.action = action
        self.delay = delay

    def schedule(self):
        self.scheduler.enter(self.delay, 1, self._fire, [])

    def _fire(self):
        self.action()
        self.schedule()

        
parser = ArgumentParser()
parser.add_argument("--num-avatars", type=int, default=1)
parser.add_argument("--frame-rate", type=float, default=50.0)
parser.add_argument("--output-receiver-host")
parser.add_argument("--output-receiver-port", type=int, default=10000)
parser.add_argument("--random-seed", type=int)
Entity.add_parser_arguments(parser)
ImproviseParameters().add_parser_arguments(parser)
args = parser.parse_args()

if args.random_seed is not None:
    prrandom.seed(args.random_seed)

if args.output_receiver_host:
    from connectivity.simple_osc_sender import OscSender
    output_sender = OscSender(port=args.output_receiver_port, host=args.output_receiver_host)
else:
    output_sender = None
            
bvh_reader = BvhReader(SKELETON_DEFINITION)
bvh_reader.read()
entity_args_strings = ENTITY_ARGS.split()
entity_args = parser.parse_args(entity_args_strings)

student = None

avatars = []
for index in range(args.num_avatars):
    pose = bvh_reader.get_hierarchy().create_pose()
    entity = Entity(bvh_reader, pose, FLOOR, Z_UP, entity_args)
    
    if student is None:
        num_input_dimensions = entity.get_value_length()
        student = DimensionalityReductionFactory.create(
            DIMENSIONALITY_REDUCTION_TYPE, num_input_dimensions, NUM_REDUCED_DIMENSIONS, DIMENSIONALITY_REDUCTION_ARGS)
        student.load(STUDENT_MODEL_PATH)

    improvise_params = ImproviseParameters()
    preferred_location = None
    improvise = Improvise(
        student,
        student.num_reduced_dimensions,
        improvise_params,
        preferred_location,
        MAX_NOVELTY)
    avatar = Avatar(index, student, entity, improvise)
    avatars.append(avatar)

application = Application(avatars, output_sender, args)
application.run()
