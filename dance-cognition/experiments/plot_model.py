#!/usr/bin/env python

from dimensionality_reduction.dimensionality_reduction_experiment import *
from PIL import Image

parser = ArgumentParser()
parser.add_argument("--output", "-o", default="model.png")
parser.add_argument("--plot-size", type=int, default=500)
parser.add_argument("--plot-dimensions", help="e.g. 0,3 (x as 1st dimension and y as 4th)")
parser.add_argument("--novelty", type=float, default=0)
parser.add_argument("--radial-resolution", type=int, default=100)

class ModelPlotter:
    def __init__(self, experiment):
        self._experiment = experiment
        self._args = experiment.args
        self._size = self._args.plot_size
        if self._args.plot_dimensions:
            self._dimensions = [int(string) for string in self._args.plot_dimensions.split(",")]
        else:
            self._dimensions = [0, 1]

    def plot(self):
        self._create_empty_buffer()
        self._add_observation_regions_to_buffer()
        self._convert_buffer_to_bitmap()
        self._save_bitmap_to_file()

    def _create_empty_buffer(self):
        self._output_buffer = numpy.zeros((self._size, self._size))

    def _add_observation_regions_to_buffer(self):
        for observation in self._experiment.student.normalized_observed_reductions:
            self._add_observation_region_to_buffer(observation)

    def _convert_buffer_to_bitmap(self):
        monochromatic_bitmap = self._output_buffer.flatten()
        monochromatic_normalized_bitmap = monochromatic_bitmap / max(monochromatic_bitmap)
        rgb_normalized_bitmap = numpy.concatenate([[1-value]*3 for value in monochromatic_normalized_bitmap])
        self._rgb_bitmap = [int(value * 255) for value in rgb_normalized_bitmap]

    def _save_bitmap_to_file(self):
        image = Image.fromstring("RGB", (self._size, self._size),
                                 data=self._array_to_string(self._rgb_bitmap))
        image.save(self._args.output)

    def _add_observation_region_to_buffer(self, observation):
        observation_px = int(observation[self._dimensions[0]] * self._size)
        observation_py = int(observation[self._dimensions[1]] * self._size)
        radius = int(self._args.novelty * self._size)
        for dx in xrange(-radius, radius+1):
            for dy in xrange(-radius, radius+1):
                if (dx*dx + dy*dy) <= radius*radius:
                    self._increase_pixel_value(
                        dx + observation_px,
                        dy + observation_py)

    def _increase_pixel_value(self, px, py):
        if self._within_boundaries(px, py):
            self._output_buffer[px, py] += 1

    def _within_boundaries(self, px, py):
        if px < 0: return False
        if py < 0: return False
        if px >= self._size: return False
        if py >= self._size: return False
        return True

    def _array_to_string(self, xs):
        return "".join([chr(int(x)) for x in xs])
        

DimensionalityReductionExperiment.add_parser_arguments(parser)
experiment = DimensionalityReductionExperiment(parser)
experiment._load_model()
plotter = ModelPlotter(experiment)
plotter.plot()
