import numpy

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
