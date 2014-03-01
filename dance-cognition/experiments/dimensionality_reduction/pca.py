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


class LinearPCA(DimensionalityReduction, sklearn.decomposition.PCA):
    def fit(self, *args):
        sklearn.decomposition.PCA.fit(self, *args)
        print "explained variance ratio: %s (sum %s)" % (
            self.explained_variance_ratio_, sum(self.explained_variance_ratio_))


class KernelPCA(DimensionalityReduction, sklearn.decomposition.KernelPCA):
    def __init__(self, **kwargs):
        sklearn.decomposition.KernelPCA.__init__(
            self, kernel="poly", fit_inverse_transform=True, gamma=0.5, **kwargs)
