from dimensionality_reduction_experiment import *
import imp
from dimensionality_reduction import PCA

parser = ArgumentParser()
DimensionalityReductionExperiment.add_parser_arguments(parser)
parser.add_argument("--num-components", "-n", type=int, default=4)
args = parser.parse_args()

entity_module = imp.load_source("entity", "entities/%s.py" % args.entity)
experiment = DimensionalityReductionExperiment(entity_module.Scene, args)
stimulus = entity_module.Stimulus(experiment)

student = PCA(n_components=args.num_components)
experiment.run(student, stimulus)
