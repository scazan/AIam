class Behavior:
    def __init__(self, experiment):
        self._experiment = experiment

    def get_reduction(self):
        return self._reduction

    def set_reduction(self, reduction):
        self._reduction = reduction
