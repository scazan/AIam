from experiment import *
from transformations import quaternion_from_euler
from quaternions import *

class QuaternionModel:
    mean_quaternion = None

class QuaternionEntity(BaseEntity):
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("--hemispherize", action="store_true")

    def probe(self, observations):
        if self.args.hemispherize:
            self.model = QuaternionModel()
            self.model.mean_quaternion = find_mean_quaternion(observations)

    def adapt_value_to_model(self, quaternion):
        if self.args.hemispherize:
            return hemispherize(quaternion, self.model.mean_quaternion)
        else:
            return quaternion

    def process_output(self, output):
        return self.adapt_value_to_model(output)
