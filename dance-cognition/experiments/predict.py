from prediction_experiment import *

parser = ArgumentParser()
PredictionExperiment.add_parser_arguments(parser)
experiment = PredictionExperiment(parser)
experiment.run()
