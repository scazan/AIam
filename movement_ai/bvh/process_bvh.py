from argparse import ArgumentParser

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from bvh_reader import BvhReader
from bvh_writer import BvhWriter
from processing import BvhProcessor

parser = ArgumentParser()
parser.add_argument("--input", "-i", required=True)
parser.add_argument("--output", "-o", required=True)
parser.add_argument("--start-frame", type=int, default=0)
parser.add_argument("--end-frame", type=int)
parser.add_argument("--rotation-order", help="Convert to e.g. yxz or xyz")
args = parser.parse_args()

bvh_reader = BvhReader(args.input)
bvh_reader.read()

if args.end_frame is None:
    end_frame = bvh_reader.get_num_frames()
else:
    end_frame = args.end_frame

bvh_processor = BvhProcessor()
input_hierarchy = bvh_reader.get_hierarchy()
output_hierarchy = input_hierarchy.clone()
if args.rotation_order:
    bvh_processor.convert_rotation_order_in_hierarchy(args.rotation_order, output_hierarchy)
    
bvh_writer = BvhWriter(
    output_hierarchy,
    bvh_reader.get_frame_time())
for frame_index in range(args.start_frame, end_frame):
    frame = bvh_reader.get_frame_by_index(frame_index)
    if args.rotation_order:
        frame = bvh_processor.convert_rotation_order_in_frame(
            args.rotation_order, frame, input_hierarchy, output_hierarchy)
    bvh_writer.add_frame(frame)

bvh_writer.write(args.output)
