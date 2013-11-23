from dimensionality_reduction_experiment import *
from dimensionality_reduction import PCA

parser = ArgumentParser()
DimensionalityReductionExperiment.add_parser_arguments(parser)
parser.add_argument("--num-components", "-n", type=int, default=4)

experiment = DimensionalityReductionExperiment(parser)
student = PCA(n_components=experiment.args.num_components)
experiment.run(student)
