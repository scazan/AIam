import sklearn.decomposition
import numpy

class DimensionalityReduction:
    def probe(self, observations):
        observed_reductions = self.transform(observations)
        self.reduction_range = []
        for n in range(self.n_components):
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
                for n in range(self.n_components)])
    
    def unnormalize_reduction(self, reduction):
        return numpy.array([
                self._unnormalize_component(reduction[n], self.reduction_range[n])
                for n in range(self.n_components)])

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

class LinearPCA(DimensionalityReduction, sklearn.decomposition.PCA):
    def __init__(self, n_components, args):
        sklearn.decomposition.PCA.__init__(self, n_components=n_components)

    def analyze_accuracy(self, observations):
        print "explained variance ratio: %s (sum %s)" % (
            self.explained_variance_ratio_, sum(self.explained_variance_ratio_))
        DimensionalityReduction.analyze_accuracy(self, observations)

class KernelPCA(DimensionalityReduction, sklearn.decomposition.KernelPCA):
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("--pca-kernel", default="poly")

    def __init__(self, n_components, args):
        sklearn.decomposition.KernelPCA.__init__(
            self, n_components=n_components,
            kernel=args.pca_kernel, fit_inverse_transform=True, gamma=0.5)
