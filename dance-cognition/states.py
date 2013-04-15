from vector import Vector3d

MC = "MC"
MLB = "MLB"
ML = "ML"
HB = "HB"
MB = "MB"
MLF = "MLF"
MRF = "MRF"
MRB = "MRB"
LLF = "LLF"
HRF = "HRF"

class State:
    def __init__(self, name, position, output_names):
        self.name = name
        self.position = Vector3d(*position)
        self.output_names = output_names
        self.outputs = set()

    def __repr__(self):
        return "State(%r, %r, %r)" % (self.name, self.position, self.output_names)

class StateMachine:
    def __init__(self):
        self.states = {}

    def add(self, name, position, output_names):
        assert name not in self.states
        self.states[name] = State(name, position, output_names)

    # def compile(self):
    #     for state in self.states:

state_machine = StateMachine()
state_machine.add(MC,  (0,0,0),   [MLB, ML , HB, MB, MLF, MRF, MRB, LLF, HRF])
state_machine.add(MLB, (0,-1,-1), [MC,  ML,  HB, MB, MLF, MRF, MRB, LLF, HRF])
state_machine.add(ML,  (0,-1,0),  [MLB, MLB, HB, MB, MLF, MRF, MRB, LLF, HRF])
state_machine.add(HB,  (1,0,-1),  [MC,  ML,  HB, MB, MLF, MRF, MRB, LLF, HRF])
state_machine.add(MB,  (0,0,-1),  [MC,  MLB, ML, HB, MLF, MRF, MRB, LLF, HRF])
state_machine.add(MLF, (0,-1,1),  [MC,  MLB, ML, HB, MB,  MRF, MRB, LLF, HRF])
state_machine.add(MRF, (0,1,-1),  [MC])
state_machine.add(MRB, (0,1,1),   [MC])
state_machine.add(LLF, (-1,1,-1), [MC])
state_machine.add(HRF, (1,1,-1),  [MC])

# states.compile()
# print states.states
