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

        self._explored_range = 1.0 + self._args.explore_beyond_observations
        self._explored_min = .5 - self._explored_range/2
        self._explored_max = .5 + self._explored_range/2

    def plot(self):
        self._create_observation_region_template()
        self._create_empty_buffer()
        self._add_observation_regions_to_buffer()
        self._convert_buffer_to_bitmap()
        self._save_bitmap_to_file()

    def _create_observation_region_template(self):
        radius = int(self._args.novelty * self._size)
        self._observation_region_size = radius * 2 + 1
        self._observation_region_template = numpy.zeros((
                self._observation_region_size,
                self._observation_region_size))
        for dx in xrange(-radius, radius+1):
            for dy in xrange(-radius, radius+1):
                if (dx*dx + dy*dy) <= radius*radius:
                    self._observation_region_template[dx + radius, dy + radius] = 1
        self._observation_region_radius = radius

    def _create_empty_buffer(self):
        self._output_buffer = numpy.zeros((self._size, self._size))

    def _add_observation_regions_to_buffer(self):
        print "creating plot..."
        for observation in self._experiment.student.normalized_observed_reductions:
            self._add_observation_region_to_buffer(observation)

    def _convert_buffer_to_bitmap(self):
        print "converting plot to bitmap..."
        monochromatic_bitmap = self._output_buffer.flatten()
        monochromatic_normalized_bitmap = monochromatic_bitmap / max(monochromatic_bitmap)
        rgb_normalized_bitmap = numpy.concatenate([[1-value]*3 for value in monochromatic_normalized_bitmap])
        self._rgb_bitmap = [int(value * 255) for value in rgb_normalized_bitmap]

    def _save_bitmap_to_file(self):
        print "saving bitmap..."
        image = Image.fromstring("RGB", (self._size, self._size),
                                 data=self._array_to_string(self._rgb_bitmap))
        image.save(self._args.output)

    def _add_observation_region_to_buffer(self, observation):
        observation_px = self._normalized_reduction_value_to_bitmap_coordinate(observation[0])
        observation_py = self._normalized_reduction_value_to_bitmap_coordinate(observation[1])
        px1 = observation_px - self._observation_region_radius
        px2 = observation_px + self._observation_region_radius + 1
        py1 = observation_py - self._observation_region_radius
        py2 = observation_py + self._observation_region_radius + 1
        if self._within_boundaries(px1, py1) and self._within_boundaries(px2, py2):
            self._output_buffer[px1:px2, py1:py2] += self._observation_region_template
        else:
            print "WARNING: ignoring observation region beyond boundaries: (%s,%s)-(%s,%s)" % (
                px1, py1, px2, py2)

    def _normalized_reduction_value_to_bitmap_coordinate(self, reduction_value):
        return int((reduction_value - self._explored_min) / self._explored_range * self._size)

    def _increase_pixel_value(self, px, py):
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
