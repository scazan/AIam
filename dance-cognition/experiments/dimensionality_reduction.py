import sklearn.decomposition
import numpy

class PCA(sklearn.decomposition.PCA):
    def probe(self, observations):
        reductions = self.transform(observations)
        self.reduction_range = []
        for n in range(self.n_components):
            reductions_n = reductions[:,n]
            self.reduction_range.append({
                "min": min(reductions_n),
                "max": max(reductions_n)
                })

    def fit(self, *args):
        sklearn.decomposition.PCA.fit(self, *args)
        print "explained variance ratio: %s (sum %s)" % (
            self.explained_variance_ratio_, sum(self.explained_variance_ratio_))
