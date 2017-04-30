import numpy
import cPickle

class DimensionalityReduction:
    def __init__(self, num_input_dimensions, num_reduced_dimensions, args):
        self.num_input_dimensions = num_input_dimensions
        self.num_reduced_dimensions = num_reduced_dimensions
        self.args = args

    def probe(self, observations):
        observed_reductions = self.transform(observations)
        self.reduction_range = []
        for n in range(self.num_reduced_dimensions):
            reductions_n = observed_reductions[:,n]
            self.reduction_range.append({
                "min": min(reductions_n),
                "max": max(reductions_n)
                })
        self.normalized_observed_reductions = numpy.array([
                self.normalize_reduction(observed_reduction)
                for observed_reduction in observed_reductions])

    def normalize_reduction(self, normalized_reduction):
        return numpy.array([
                self._normalize_component(normalized_reduction[n], self.reduction_range[n])
                for n in range(self.num_reduced_dimensions)])
    
    def unnormalize_reduction(self, reduction):
        return numpy.array([
                self._unnormalize_component(reduction[n], self.reduction_range[n])
                for n in range(self.num_reduced_dimensions)])

    def _normalize_component(self, component, reduction_range):
        return (component - reduction_range["min"]) / (
            reduction_range["max"] - reduction_range["min"])

    def _unnormalize_component(self, normalized_component, reduction_range):
        return normalized_component * (
            reduction_range["max"] - reduction_range["min"]) + reduction_range["min"]

    def analyze_accuracy(self, observations):
        reductions = self.transform(observations)
        reconstructions = self.inverse_transform(reductions)
        mean_squared_error = ((observations - reconstructions) ** 2).mean(axis=None)
        print "mean squared error: %s" % mean_squared_error

    def transform(self, observations):
        raise NotImplementedError()

    def inverse_transform(self, reductions):
        raise NotImplementedError()

    def save(self, path):
        self.save_model(path)
        self.save_persistent_state(path)

    def load(self, path):
        self.load_model(path)
        self.load_persistant_state(path)
        
    def save_persistent_state(self, model_path):
        f = open(self._persistant_state_path(model_path), "w")
        cPickle.dump((self.reduction_range, self.normalized_observed_reductions), f)
        f.close()

    def load_persistant_state(self, model_path):
        f = open(self._persistant_state_path(model_path))
        self.reduction_range, self.normalized_observed_reductions = cPickle.load(f)
        f.close()

    def _persistant_state_path(self, model_path):
        return model_path + ".state"
