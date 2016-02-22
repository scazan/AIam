from dimensionality_reduction.dimensionality_reduction_experiment import *

parser = ArgumentParser()
parser.add_argument("--output", "-o", default="samples.dat")

DimensionalityReductionExperiment.add_parser_arguments(parser)
experiment = DimensionalityReductionExperiment(parser)
experiment._load_model()

data = experiment.student.normalized_observed_reductions
samples = sampling.NeighborhoodSampler.sample(
    data,
    num_neighborhoods=100,
    samples_per_neighborhood=10,
    neighborhood_size=0.1)

out = open(experiment.args.output, "w")
for sample in samples:
    print >>out, " ".join([str(value) for value in sample])
out.close()
