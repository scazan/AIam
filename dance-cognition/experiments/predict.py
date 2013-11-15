from prediction_experiment import *
import imp

parser = ArgumentParser()
PredictionExperiment.add_parser_arguments(parser)
args = parser.parse_args()

entity_module = imp.load_source("entity", "entities/%s.py" % args.entity)
experiment = PredictionExperiment(entity_module.Scene, args)

## Point:
# if args.bvh:
#     stimulus = BvhStimulus(experiment.bvh_reader)
# else:
#     stimulus = CircularStimulus()

stimulus = entity_module.Stimulus(experiment)
num_parameters = len(stimulus.get_value())

student = BackpropNet(
    num_parameters,
    num_parameters * 2,
    num_parameters)

experiment.run(student, stimulus)
