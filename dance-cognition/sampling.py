import numpy

class NeighborhoodSampler:
    @classmethod
    def sample(cls, function, num_inputs, num_neighborhoods, samples_per_neighborhood, neighborhood_size):
        result = []
        for n in range(num_neighborhoods):
            data_index = int(float(n) / num_neighborhoods * num_inputs)
            data = function(data_index)
            result += cls._sample_neighborhood(data, samples_per_neighborhood, neighborhood_size)
        return result

    @classmethod
    def _sample_neighborhood(cls, data, num_samples, neighborhood_size):
        num_dimensions = len(data)
        return [data + cls._random_vector(num_dimensions, magnitude=neighborhood_size)
                for n in range(num_samples)]

    @classmethod
    def _random_vector(cls, num_dimensions, magnitude):
        return (numpy.random.rand(num_dimensions) - 0.5) * magnitude
