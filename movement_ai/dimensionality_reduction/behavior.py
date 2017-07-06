class Behavior:
    def __init__(self, experiment):
        self._experiment = experiment
        self._target_root_vertical_orientation = None

    def get_reduction(self):
        return self._reduction

    def set_reduction(self, reduction):
        self._reduction = reduction

    def set_target_root_vertical_orientation(self, orientation):
        self._target_root_vertical_orientation = orientation

    def get_root_vertical_orientation(self):
        return None
