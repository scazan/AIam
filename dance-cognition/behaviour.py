class Behaviour:
    def __init__(self, state_machine):
        self._state_machine = state_machine

    def process_raw_input(self, raw_input_position, time_increment):
        return raw_input_position

    def observed_state(self):
        return None
