#!/usr/bin/env python

#PROFILE_ARGS = "-entity hierarchical --incremental -r quaternion -bvh scenes/pn-01.22_skeleton.bvh -n 7 --num-hidden-nodes=0 --learning-rate=0.005 --friction --floor --max-novelty=1.4 --translate"

STUDENT_MODEL_PATH = "profiles/dimensionality_reduction/valencia_pn_autoencoder.model"
ENTITY_ARGS = "-r quaternion --friction --translate"
SKELETON_DEFINITION = "scenes/pn-01.22_skeleton.bvh"
DIMENSIONALITY_REDUCTION_TYPE = "AutoEncoder"
NUM_REDUCED_DIMENSIONS = 7
DIMENSIONALITY_REDUCTION_ARGS = "--num-hidden-nodes=0 --learning-rate=0.005"
Z_UP = False
FLOOR = True
MAX_NOVELTY = 1.4

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")

from argparse import ArgumentParser
import sched
import time
import numpy

from entities.hierarchical import Entity
from bvh.bvh_reader import BvhReader
from stopwatch import Stopwatch
from dimensionality_reduction.behaviors.improvise import ImproviseParameters, Improvise
from dimensionality_reduction.factory import DimensionalityReductionFactory

class Application:
    def __init__(self, student, entity, behavior, output_sender, args):
        self._student = student
        self._entity = entity
        self._behaviour = behavior
        self._output_sender = output_sender
        self._args = args
        
    def run(self):
        self._input = None
        self._output = None
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
            self._proceed_and_update()
            if self._output is not None:
                processed_output = self._entity.process_output(self._output)
                if self._output_sender is not None:
                    self._send_output(processed_output)

        self.previous_frame_time = self._now
        self._frame_count += 1
            
    def _proceed_and_update(self):
        self._behaviour.proceed(self._time_increment)
        self._entity.update()
        reduction = self._behaviour.get_reduction(self._input)
        if reduction is not None:
            self._output = self._student.inverse_transform(numpy.array([reduction]))[0]

    def _send_output(self, processed_output):
        for index, worldpos in enumerate(processed_output):
            self._output_sender.send(
                "/world", self._frame_count, index,
                worldpos[0], worldpos[1], worldpos[2])

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
parser.add_argument("--frame-rate", type=float, default=50.0)
parser.add_argument("--output-receiver-host")
parser.add_argument("--output-receiver-port", type=int, default=10000)
Entity.add_parser_arguments(parser)
ImproviseParameters().add_parser_arguments(parser)
args = parser.parse_args()

if args.output_receiver_host:
    from connectivity.simple_osc_sender import OscSender
    output_sender = OscSender(port=args.output_receiver_port, host=args.output_receiver_host)
else:
    output_sender = None
            
bvh_reader = BvhReader(SKELETON_DEFINITION)
bvh_reader.read()
pose = bvh_reader.get_hierarchy().create_pose()
entity_args_strings = ENTITY_ARGS.split()
entity_args = parser.parse_args(entity_args_strings)
entity = Entity(bvh_reader, pose, FLOOR, Z_UP, entity_args)

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
    
application = Application(student, entity, improvise, output_sender, args)
application.run()
