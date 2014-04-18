#!/usr/bin/env python

from skeleton import process_bvhfile
from camera import Camera
import math
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("filename")
parser.add_argument("--camera-x", "-cx", type=float)
parser.add_argument("--camera-y", "-cy", type=float)
parser.add_argument("--camera-z", "-cz", type=float)
parser.add_argument("--rotation", "-r", type=float)
parser.add_argument("--output", "-o")
parser.add_argument("--frame-width", type=float, default=100)
parser.add_argument("--frame-height", type=float, default=100)
parser.add_argument("--stroke-width", type=float, default=1)
parser.add_argument("--begin", type=int)
parser.add_argument("--end", type=int)
parser.add_argument("--num-frames", type=int)
parser.add_argument("--displacement", type=float, default=0)
parser.add_argument("--min-opacity", type=float, default=0.1)
parser.add_argument("--constrain-floor", action="store_true")
args = parser.parse_args()

if args.output:
    output_path = args.output
else:
    output_path = args.filename.replace(".bvh", ".svg")

skeleton = process_bvhfile(args.filename)
camera = Camera(args.camera_x, args.camera_y, args.camera_z, cfx=20, ppdist=30)
skelscreenedges = skeleton.make_skelscreenedges()
output = open(output_path, "w")

def export_frame(t, opacity, x_offset):
    global args, floor_y

    skeleton.populate_skelscreenedges(skelscreenedges, t)

    if args.constrain_floor:
        frame_bottom_y = min([
                min(screenedge.sv1.tr[1], screenedge.sv2.tr[1])
                for screenedge in skelscreenedges])
        if floor_y is None:
            floor_y = frame_bottom_y
        y_offset = floor_y - frame_bottom_y

        for screenedge in skelscreenedges:
            screenedge.sv1.tr[1] += y_offset
            screenedge.sv2.tr[1] += y_offset

    for screenedge in skelscreenedges:
        screenedge.worldtocam(camera)
        screenedge.camtoscreen(camera, args.frame_width, args.frame_height)
        write_svg('<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke:black;fill:none;stroke-width:%f;stroke-opacity:%f" />' % (
            screenedge.sv1.screenx + x_offset,
            screenedge.sv1.screeny,
            screenedge.sv2.screenx + x_offset,
            screenedge.sv2.screeny,
            args.stroke_width,
            opacity))

def write_svg(string):
    global output
    print >>output, string

if args.begin is None:
    begin = 1
else:
    begin = args.begin

if args.end is None:
    end = skeleton.frames + 1
else:
    end = args.end

if args.num_frames is None:
    num_frames = end - begin
else:
    num_frames = args.num_frames

print "exporting %s frames in the range %s-%s" % (num_frames, begin, end)

write_svg('<svg xmlns="http://www.w3.org/2000/svg" version="1.1">')
write_svg('<rect width="%f" height="%f" fill="white" />' % (
            args.frame_width + args.displacement * num_frames, args.frame_height))

if args.constrain_floor:
    floor_y = None

def opacity(n, relative_frame_index):
    return args.min_opacity + (1 - args.min_opacity) * math.pow(relative_frame_index, 3)
    # if (n-2) % 5 == 0:
    #     return 1
    # else:
    #     return args.min_opacity

for n in range(num_frames):
    relative_frame_index = float(n) / num_frames
    frame_index = begin + int(relative_frame_index * (end - begin))
    print "adding frame %s" % frame_index
    x_offset = args.displacement * n
    export_frame(frame_index, opacity(n, relative_frame_index), x_offset)

write_svg('</svg>')
