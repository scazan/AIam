class Behaviour:
    def __init__(self, state_machine, interpreter):
        self._state_machine = state_machine
        self.interpreter = interpreter
        self.MC = state_machine.states["MC"]

    def process_raw_input(self, raw_input_position, time_increment):
        return raw_input_position
