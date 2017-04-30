from dimensionality_reduction import DimensionalityReduction
import sklearn.decomposition
from sklearn.externals import joblib

class PCADimensionalityReduction(DimensionalityReduction):
    def save_model(self, path):
        joblib.dump(self, path)

    def load_model(self, path):
        self = joblib.load(path)
        
class LinearPCA(sklearn.decomposition.PCA, PCADimensionalityReduction):
    def __init__(self, num_input_dimensions, num_reduced_dimensions, args):
        DimensionalityReduction.__init__(self, num_input_dimensions, num_reduced_dimensions, args)
        sklearn.decomposition.PCA.__init__(self, n_components=num_reduced_dimensions)

    def analyze_accuracy(self, observations):
        print "explained variance ratio: %s (sum %s)" % (
            self.explained_variance_ratio_, sum(self.explained_variance_ratio_))
        DimensionalityReduction.analyze_accuracy(self, observations)

class KernelPCA(sklearn.decomposition.KernelPCA, PCADimensionalityReduction):
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("--pca-kernel", default="poly")

    def __init__(self, num_input_dimensions, num_reduced_dimensions, args):
        DimensionalityReduction.__init__(self, num_input_dimensions, num_reduced_dimensions, args)
        sklearn.decomposition.KernelPCA.__init__(
            self, n_components=num_reduced_dimensions,
            kernel=args.pca_kernel, fit_inverse_transform=True, gamma=0.5)
