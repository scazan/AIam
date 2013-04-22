class Behaviour:
    def __init__(self, state_machine, interpreter):
        self._state_machine = state_machine
        self.interpreter = interpreter
        self.MC = state_machine.states["MC"]
