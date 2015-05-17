from dimensionality_reduction.dimensionality_reduction_experiment import *

parser = ArgumentParser()
DimensionalityReductionExperiment.add_parser_arguments(parser)
experiment = DimensionalityReductionExperiment(parser)
experiment.run()
