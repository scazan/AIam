#!/usr/bin/env python

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../bvhplay")

from dimensionality_reduction.dimensionality_reduction_experiment import *
from svg_exporter import SvgExporter
import os

parser = ArgumentParser()
parser.add_argument("--output", "-o", default="pose_map.svg")
parser.add_argument("--plot-size", type=float, default=500)
parser.add_argument("--camera-x", "-cx", type=float, default=0)
parser.add_argument("--camera-y", "-cy", type=float, default=10)
parser.add_argument("--camera-z", "-cz", type=float, default=220)

class PoseMapRenderer:
    _bvh_tempfile_path = "_temp.bvh"

    def __init__(self, experiment):
        self._experiment = experiment
        self._args = experiment.args

    def render(self):
        self._experiment.bvh_reader.set_pose_from_time(self._experiment.pose, 0) # hack (should not be needed)
        self._out = open(self._args.output, "w")
        self._generate_header()
        normalized_reduction = [0.5] * self._experiment.student.n_components
        reduction = self._experiment.student.unnormalize_reduction(normalized_reduction)
        output = self._experiment.student.inverse_transform(numpy.array([reduction]))[0]
        self._experiment.entity.parameters_to_processed_pose(output, self._experiment.pose)
        self._render_pose(self._experiment.pose, self._args.plot_size/2, self._args.plot_size/2)
        self._generate_footer()
        self._out.close()

    def _render_pose(self, pose, cx, cy):
        self._save_pose_as_temp_bvh(pose)
        self._export_temp_bvh_to_svg(cx, cy)
        self._delete_temp_bvh()

    def _save_pose_as_temp_bvh(self, pose):
        bvh_writer = BvhWriter(
            self._experiment.bvh_reader.get_hierarchy(),
            self._experiment.bvh_reader.get_frame_time())
        frame = self._experiment.pose_to_bvh_frame(pose)
        bvh_writer.add_frame(frame)
        bvh_writer.write(self._bvh_tempfile_path)

    def _export_temp_bvh_to_svg(self, cx, cy):
        bvh_to_svg_exporter = SvgExporter(
            self._bvh_tempfile_path,
            self._args.camera_x, self._args.camera_y, self._args.camera_z)
        bvh_to_svg_exporter.export_frame(
            self._out,
            t=0,
            width=self._args.plot_size,
            height=self._args.plot_size,
            auto_crop=True)

    def _delete_temp_bvh(self):
        os.unlink(self._bvh_tempfile_path)
        
    def _generate_header(self):
        self._write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1">\n')
        self._write('<rect width="%f" height="%f" fill="white" />' % (
            self._args.plot_size, self._args.plot_size))

    def _generate_footer(self):
        self._write('</svg>\n')

    def _write(self, string):
        print >>self._out, string


DimensionalityReductionExperiment.add_parser_arguments(parser)
experiment = DimensionalityReductionExperiment(parser)
experiment._load_model()
renderer = PoseMapRenderer(experiment)
renderer.render()

