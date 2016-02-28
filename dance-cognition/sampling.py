import numpy
import sklearn.cluster
import sklearn.neighbors

class NeighborhoodSampler:
    @classmethod
    def sample(cls, data, num_neighborhoods, samples_per_neighborhood, neighborhood_size):
        num_inputs = len(data)
        result = []
        for n in range(num_neighborhoods):
            data_index = int(float(n) / num_neighborhoods * num_inputs)
            datum = data[data_index]
            result += cls._sample_neighborhood(datum, samples_per_neighborhood, neighborhood_size)
        return result

    @classmethod
    def _sample_neighborhood(cls, datum, num_samples, neighborhood_size):
        num_dimensions = len(datum)
        return [datum + cls._random_vector(num_dimensions, magnitude=neighborhood_size)
                for n in range(num_samples)]

    @classmethod
    def _random_vector(cls, num_dimensions, magnitude):
        return (numpy.random.rand(num_dimensions) - 0.5) * magnitude

class KMeansSampler:
    @classmethod
    def sample(cls, data, num_samples):
        kmeans = sklearn.cluster.KMeans(n_clusters=num_samples)
        kmeans.fit(data)
        return kmeans.cluster_centers_

class MiniBatchKMeansSampler:
    @classmethod
    def sample(cls, data, num_samples):
        kmeans = sklearn.cluster.MiniBatchKMeans(n_clusters=num_samples)
        kmeans.fit(data)
        return kmeans.cluster_centers_

class DistanceDistributionEqualizationSampler:
    def sample(self, data, num_samples):
        self._data = data
        self._knn = sklearn.neighbors.KNeighborsClassifier(n_neighbors=2)
        indices = range(len(data))
        self._knn.fit(data, indices)
        indices_sorted_by_nearest_neighbor_distance = sorted(
            indices,
            key=lambda index: self._distance_to_nearest_neighbor(index))
        linear_index_distribution = [
            int(n) for n in numpy.arange(0, len(data), float(len(data))/num_samples)]
        sampled_indices = [
            indices_sorted_by_nearest_neighbor_distance[index]
            for index in linear_index_distribution]
        return [data[index] for index in sampled_indices]

    def _distance_to_nearest_neighbor(self, index):
        observation = self._data[index]
        distances_list, _ = self._knn.kneighbors(observation, return_distance=True)
        distances = distances_list[0]
        return max(distances)

class MinDistanceSampler:
    @classmethod
    def sample(cls, observations, min_distance, num_neighbors_ratio=0.01):
        knn = sklearn.neighbors.KNeighborsClassifier(
            n_neighbors=int(len(observations) * num_neighbors_ratio))
        indices = range(len(observations))
        knn.fit(observations, indices)
        dropped_indices = set()
        for index, observation in zip(indices, observations):
            distances_list, neighbor_indices_list = knn.kneighbors(observation)
            distances = distances_list[0]
            neighbor_indices = neighbor_indices_list[0]
            for neighbor_index, distance in zip(neighbor_indices, distances):
                if (neighbor_index != index and
                    distance < min_distance and
                    neighbor_index not in dropped_indices):
                    dropped_indices.add(index)
                    break
        sampled_indices = set(indices) - dropped_indices
        return [observations[index] for index in sampled_indices]
