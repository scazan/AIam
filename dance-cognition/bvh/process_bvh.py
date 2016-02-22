from argparse import ArgumentParser
from bvh_reader import BvhReader
from bvh_writer import BvhWriter

parser = ArgumentParser()
parser.add_argument("--input", "-i", required=True)
parser.add_argument("--output", "-o", required=True)
parser.add_argument("--delete-joints", help="Comma separated list of joints to delete")
args = parser.parse_args()

if args.delete_joints:
    joints_to_delete = args.delete_joints.split(",")

bvh_reader = BvhReader(args.input)
bvh_reader.read()

bvh_writer = BvhWriter(
    bvh_reader.get_hierarchy(),
    bvh_reader.get_frame_time())
for frame_index in range(bvh_reader.get_num_frames()):
    frame = bvh_reader.get_frame_by_index(frame_index)
    if args.delete_joints:
        frame = bvh_reader.delete_joints_from_frame(joints_to_delete, frame)
    bvh_writer.add_frame(frame)

if args.delete_joints:
    bvh_reader.delete_joints_from_hierarchy(joints_to_delete)
bvh_writer.write(args.output)
