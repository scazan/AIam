#!/usr/bin/env python

# gnuplot example for 3 components:
# set palette gray
# splot "observations.dat" with points pointsize 0.4 pointtype 7 palette

# export to EPS:
# set terminal postscript eps color
# set out "observations.eps"
# replot

from dimensionality_reduction.dimensionality_reduction_experiment import *

parser = ArgumentParser()
parser.add_argument("--output", "-o")
parser.add_argument("--split-sensitivity", type=float)
parser.add_argument("--segments-output")
parser.add_argument("--plot-type", choices=["gnuplot", "svg"], default="gnuplot")
parser.add_argument("--stroke-width", type=float, default=1)
parser.add_argument("--plot-width", type=float, default=500)
parser.add_argument("--plot-height", type=float, default=500)

class ObservationsPlotter:
    def __init__(self, experiment):
        self._experiment = experiment
        self._args = experiment.args

    def plot(self):
        generator_class = eval("%sGenerator" % self._args.plot_type)

        if self._args.output:
            output_filename = self._args.output
        else:
            output_filename = generator_class.DEFAULT_FILENAME

        segments = self._get_segments_from_bvhs()
        if self._args.split_sensitivity:
            segments = self._split_segments_by_sensitivity(segments)

        out = open(output_filename, "w")
        generator = generator_class(out, self._args)
        generator.generate(segments)
        out.close()

        print "Plotted %d observations in %d segments to file %s" % (
            sum([len(segment) for segment in segments]),
            len(segments), output_filename)

    def _get_segments_from_bvhs(self):
        return [self._get_observations_from_bvh(bvh_reader)
                for bvh_reader in experiment.bvh_reader.get_readers()]

    def _get_observations_from_bvh(self, bvh_reader):
        return self._experiment.student.normalized_observed_reductions[
            bvh_reader.start_index : bvh_reader.end_index]

    def _split_segments_by_sensitivity(self, segments):
        result = []
        for observations in segments:
            result += self._split_observations_by_sensitivity(observations)
        return result

    def _split_observations_by_sensitivity(self, observations):
        segments = []
        segment = []
        previous_observation = None
        for observation in observations:
            if previous_observation is not None and \
                    numpy.linalg.norm(observation - previous_observation) > self._args.split_sensitivity:
                segments.append(segment)
                segment = []
            segment.append(observation)
            previous_observation = observation
        if len(segment) > 0:
            segments.append(segment)
        return segments

class Generator:
    def __init__(self, out, args):
        self._out = out
        self._args = args

    def _write(self, string):
        print >>self._out, string

class gnuplotGenerator(Generator):
    DEFAULT_FILENAME = "observations.dat"

    def generate(self, segments):
        for observations in segments:
            for observation in observations:
                print >>self._out, " ".join([str(value) for value in observation])
            print >>self._out

        if self._args.segments_output:
            n = 0
            for segment in segments:
                out = open(self._args.segments_output % n, "w")
                for observation in segment:
                    print >>out, " ".join([str(value) for value in observation])
                out.close()
                n += 1

class svgGenerator(Generator):
    DEFAULT_FILENAME = "observations.svg"

    def generate(self, segments):
        self._generate_header()
        for segment in segments:
            self._generate_segment(segment)
        self._generate_footer()

    def _generate_header(self):
        self._write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1">\n')
        self._write('<rect width="%f" height="%f" fill="white" />' % (
            self._args.plot_width, self._args.plot_height))

    def _generate_segment(self, segment):
        self._write('<path '''
                    'style="stroke:black;fill:none;stroke-width:%f" '''
                    'd="M %s' % (
                self._args.stroke_width,
                self._path_coordinates(segment[0])))
        for observation in segment[1:]:
            self._write(' L %s' % self._path_coordinates(observation))
        self._write('" />\n')

    def _path_coordinates(self, observation):
        return "%s %s" % (self._args.plot_width * observation[0],
                          self._args.plot_height * observation[1])

    def _generate_footer(self):
        self._write('</svg>\n')


DimensionalityReductionExperiment.add_parser_arguments(parser)
experiment = DimensionalityReductionExperiment(parser)
experiment._load_model()
plotter = ObservationsPlotter(experiment)
plotter.plot()

