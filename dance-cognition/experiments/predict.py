from prediction_experiment import *

parser = ArgumentParser()
PredictionExperiment.add_parser_arguments(parser)
args = parser.parse_args()

experiment = PredictionExperiment(args)
num_parameters = len(experiment.stimulus.get_value())

student = BackpropNet(
    num_parameters,
    num_parameters * 2,
    num_parameters)

experiment.run(student)
