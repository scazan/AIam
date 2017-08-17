#!/usr/bin/env python

STUDENT_MODEL_PATH = "profiles/dimensionality_reduction/valencia_pn_autoencoder.model"
SKELETON_DEFINITION = "scenes/pn-01.22_skeleton.bvh"
DIMENSIONALITY_REDUCTION_TYPE = "AutoEncoder"
DIMENSIONALITY_REDUCTION_ARGS = "--num-hidden-nodes=0 --learning-rate=0.006 --tied-weights"
ENTITY_ARGS = "-r quaternion --translate --translation-weight=0"

NUM_REDUCED_DIMENSIONS = 7
Z_UP = False
FLOOR = True

from argparse import ArgumentParser
import numpy

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/..")
from entities.hierarchical import Entity
from bvh.bvh_reader import BvhReader
from dimensionality_reduction.factory import DimensionalityReductionFactory

parser = ArgumentParser()
parser.add_argument("--num-iterations", type=int, default=1000)
Entity.add_parser_arguments(parser)
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

normalized_reduction = [.5] * NUM_REDUCED_DIMENSIONS

for i in range(args.num_iterations):
    reduction = student.unnormalize_reduction(normalized_reduction)
    output = student.inverse_transform(numpy.array([reduction]))[0]
    vertices = entity.process_output(output)
