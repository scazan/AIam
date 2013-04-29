import input_generator
from states import state_machine, LLF

class Generator(input_generator.Generator):
    def __init__(self, args):
        pass

    def update(self, time_increment):
        pass

    def position(self):
        return state_machine.states[LLF].position
