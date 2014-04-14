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
args = parser.parse_args()

skeleton = process_bvhfile(args.filename)
camera = Camera(args.camera_x, args.camera_y, args.camera_z)
skelscreenedges = skeleton.make_skelscreenedges()
output = open(args.output, "w")

def export_frame(t):
    global args
    skeleton.populate_skelscreenedges(skelscreenedges, t)
    for screenedge in skelscreenedges:
        screenedge.worldtocam(camera)
        screenedge.camtoscreen(camera, args.frame_width, args.frame_height)
        write_svg('<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke:black;fill:none;stroke-width:%f" />' % (
            screenedge.sv1.screenx,
            screenedge.sv1.screeny,
            screenedge.sv2.screenx,
            screenedge.sv2.screeny,
            args.stroke_width))

def write_svg(string):
    global output
    print >>output, string

write_svg('<svg xmlns="http://www.w3.org/2000/svg" version="1.1">')
write_svg('<rect width="%f" height="%f" fill="white" />' % (
            args.frame_width, args.frame_height))

export_frame(0)

write_svg('</svg>')
