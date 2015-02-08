#!/usr/bin/env python

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../bvhplay")

from dimensionality_reduction.dimensionality_reduction_experiment import *
from svg_exporter import SvgExporter
import os
import sklearn.neighbors

parser = ArgumentParser()
parser.add_argument("--output", "-o", default="pose_map.svg")
parser.add_argument("--plot-size", type=float, default=500)
parser.add_argument("--camera-x", "-cx", type=float, default=0)
parser.add_argument("--camera-y", "-cy", type=float, default=10)
parser.add_argument("--camera-z", "-cz", type=float, default=1500)
parser.add_argument("--grid-resolution", type=int, default=10)
parser.add_argument("--min-opacity", type=float, default=.02)
parser.add_argument("--opacity-contrast", type=float, default=.5)

class PoseMapRenderer:
    _bvh_tempfile_path = "_temp.bvh"

    def __init__(self, experiment):
        self._experiment = experiment
        self._args = experiment.args
        self._explored_range = 1.0 + self._args.explore_beyond_observations
        self._explored_min = .5 - self._explored_range/2
        self._explored_max = .5 + self._explored_range/2

    def render(self):
        self._experiment.bvh_reader.set_pose_from_time(self._experiment.pose, 0) # hack (should not be needed)
        self._out = open(self._args.output, "w")
        self._cell_size = self._args.plot_size / self._args.grid_resolution
        self._approximate_model_values()
        self._generate_header()
        for grid_y in xrange(self._args.grid_resolution):
            for grid_x in xrange(self._args.grid_resolution):
                self._render_cell(grid_x, grid_y)
        self._generate_footer()
        self._out.close()

    def _approximate_model_values(self):
        self._nearest_neighbor_classifier = sklearn.neighbors.KNeighborsClassifier(
            n_neighbors=1, weights='uniform')
        self._nearest_neighbor_classifier.fit(
            self._experiment.student.normalized_observed_reductions,
            self._experiment.student.normalized_observed_reductions)

        self._model_values = numpy.zeros((self._args.grid_resolution, self._args.grid_resolution))

        for grid_y in xrange(self._args.grid_resolution):
            for grid_x in xrange(self._args.grid_resolution):
                normalized_reduction = self._get_normalized_reduction(grid_x, grid_y)
                self._model_values[grid_x, grid_y] = self._distance_to_nearest_observation(
                    normalized_reduction)

        self._model_values -= numpy.amin(self._model_values)
        self._model_values /= numpy.amax(self._model_values)

    def _distance_to_nearest_observation(self, normalized_reduction):
        nearest_observation = self._nearest_neighbor_classifier.predict(normalized_reduction)[0]
        return numpy.linalg.norm(normalized_reduction - nearest_observation)

    def _render_cell(self, grid_x, grid_y):
        normalized_reduction = self._get_normalized_reduction(grid_x, grid_y)
        px = float(grid_x) / self._args.grid_resolution * self._args.plot_size
        py = float(grid_y) / self._args.grid_resolution * self._args.plot_size
        opacity = self._args.min_opacity + (
            1 - pow(self._model_values[grid_x, grid_y], self._args.opacity_contrast)
            * (1 - self._args.min_opacity))
        self._get_pose(normalized_reduction)
        self._render_pose(px, py, opacity)

    def _get_normalized_reduction(self, grid_x, grid_y):
        normalized_reduction = [0.5] * self._experiment.student.n_components
        normalized_reduction[0] = float(grid_x) / (self._args.grid_resolution - 1) \
            * self._explored_range + self._explored_min
        normalized_reduction[1] = float(grid_y) / (self._args.grid_resolution - 1) \
            * self._explored_range + self._explored_min
        return normalized_reduction
        
    def _get_pose(self, normalized_reduction):
        reduction = self._experiment.student.unnormalize_reduction(normalized_reduction)
        output = self._experiment.student.inverse_transform(numpy.array([reduction]))[0]
        self._experiment.entity.parameters_to_processed_pose(output, self._experiment.pose)

    def _render_pose(self, px, py, opacity):
        self._save_pose_as_temp_bvh()
        self._export_temp_bvh_to_svg(px, py, opacity)
        self._delete_temp_bvh()

    def _save_pose_as_temp_bvh(self):
        bvh_writer = BvhWriter(
            self._experiment.bvh_reader.get_hierarchy(),
            self._experiment.bvh_reader.get_frame_time())
        frame = self._experiment.pose_to_bvh_frame(self._experiment.pose)
        bvh_writer.add_frame(frame)
        bvh_writer.write(self._bvh_tempfile_path)

    def _export_temp_bvh_to_svg(self, px, py, opacity):
        bvh_to_svg_exporter = SvgExporter(
            self._bvh_tempfile_path,
            self._args.camera_x, self._args.camera_y, self._args.camera_z)
        bvh_to_svg_exporter.export_frame(
            self._out,
            t=0,
            x=px,
            y=py,
            width=self._cell_size,
            height=self._cell_size,
            opacity=opacity,
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

