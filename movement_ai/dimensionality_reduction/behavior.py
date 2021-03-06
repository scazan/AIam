class Behavior:
    def __init__(self):
        self._target_root_vertical_orientation = None
        self._observers = set()

    def get_reduction(self):
        return self._reduction

    def set_reduction(self, reduction):
        self._reduction = reduction

    def set_target_root_vertical_orientation(self, orientation):
        self._target_root_vertical_orientation = orientation

    def get_root_vertical_orientation(self):
        return None

    def add_observer(self, observer):
        self._observers.add(observer)
        
    def notify(self, message):
        for observer in self._observers:
            observer(message)

    def sends_output(self):
        return False

    def on_input(self, input_):
        pass
    
    def proceed(self, time_increment):
        pass

    def set_normalized_observed_reductions(self, normalized_observed_reductions):
        pass
    
