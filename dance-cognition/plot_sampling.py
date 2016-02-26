from dimensionality_reduction.dimensionality_reduction_experiment import *

parser = ArgumentParser()
parser.add_argument("--output", "-o", default="samples.dat")
parser.add_argument("--plot-dimensions", help="e.g. 0,3 (x as 1st dimension and y as 4th)")

DimensionalityReductionExperiment.add_parser_arguments(parser)
experiment = DimensionalityReductionExperiment(parser)
experiment._load_model()

data = experiment.student.normalized_observed_reductions
samples = sampling.NeighborhoodSampler.sample(
    data,
    num_neighborhoods=100,
    samples_per_neighborhood=10,
    neighborhood_size=0.1)

args = experiment.args
if args.plot_dimensions:
    dimensions = [int(string) for string in args.plot_dimensions.split(",")]
else:
    dimensions = [0, 1]

out = open(args.output, "w")
for sample in samples:
    print >>out, " ".join([str(sample[n]) for n in dimensions])
out.close()
