#!/usr/bin/env python

from skeleton import process_bvhfile
from camera import Camera
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("filename")
parser.add_argument("--camera-x", "-cx", type=float)
parser.add_argument("--camera-y", "-cy", type=float)
parser.add_argument("--camera-z", "-cz", type=float)
parser.add_argument("--rotation", "-r", type=float)
parser.add_argument("--output", "-o", default="export.svg")
parser.add_argument("--frame-width", type=float, default=100)
parser.add_argument("--frame-height", type=float, default=100)
parser.add_argument("--stroke-width", type=float, default=1)
parser.add_argument("--begin", type=int)
parser.add_argument("--end", type=int)
parser.add_argument("--num-frames", type=int)
parser.add_argument("--displacement", type=float, default=0)
args = parser.parse_args()

skeleton = process_bvhfile(args.filename)
camera = Camera(args.camera_x, args.camera_y, args.camera_z, cfx=20, ppdist=30)
skelscreenedges = skeleton.make_skelscreenedges()
output = open(args.output, "w")

def export_frame(t, opacity, x_offset):
    global args
    skeleton.populate_skelscreenedges(skelscreenedges, t)
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

for n in range(num_frames):
    relative_frame_index = float(n) / num_frames
    frame_index = begin + int(relative_frame_index * (end - begin))
    print "adding frame %s" % frame_index
    x_offset = args.displacement * n
    export_frame(frame_index, relative_frame_index, x_offset)

write_svg('</svg>')
