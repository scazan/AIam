import sklearn.decomposition
import numpy

class PCA(sklearn.decomposition.KernelPCA):
    def __init__(self, **kwargs):
        sklearn.decomposition.KernelPCA.__init__(
            self, kernel="poly", fit_inverse_transform=True, gamma=0.5, **kwargs)

    def probe(self, observations):
        reductions = self.transform(observations)
        self.reduction_range = []
        for n in range(self.n_components):
            reductions_n = reductions[:,n]
            self.reduction_range.append({
                "min": min(reductions_n),
                "max": max(reductions_n)
                })
