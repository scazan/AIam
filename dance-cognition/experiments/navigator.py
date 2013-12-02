class Navigator:
    def __init__(self, knowns):
        self.knowns = knowns

    def generate_path(self, departure, destination, resolution):
        self._departure = departure
        self._destination = destination
        self._resolution = resolution
        return [self._interpolate(n) for n in range(resolution)]

    def _interpolate(self, n):
        return self._departure + \
            (self._destination - self._departure) * n / (self._resolution - 1)
