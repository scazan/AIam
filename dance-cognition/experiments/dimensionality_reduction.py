import sklearn.decomposition
import numpy

class PCA(sklearn.decomposition.PCA):
    def probe(self, observations):
        reductions = numpy.array(
            [self.transform(observation) for observation in observations])
        self.reduction_range = []
        for n in range(self.n_components):
            reductions_n = reductions[:,n]
            self.reduction_range.append({
                "min": min(reductions_n),
                "max": max(reductions_n)
                })
