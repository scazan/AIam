from vector import Vector3d
import collections

MC = "mc"
MLB = "mlb"
ML = "ml"
HB = "hb"
MB = "mb"
MLF = "mlf"
MRF = "mrf"
MRB = "mrb"
LLF = "llf"
HRF = "hrf"

class State:
    def __init__(self, name, output_names):
        self.name = name
        self.output_names = output_names
        self.outputs = []
        self.inputs = []

    def __repr__(self):
        return "State(%r)" % (self.name)

class StateMachine:
    def __init__(self):
        self.states = collections.OrderedDict()
        self.transitions = set()

    def add(self, name, output_names):
        assert name not in self.states
        self.states[name] = State(name, output_names)

    def compile(self):
        for input_name, input_state in self.states.iteritems():
            for output_name in input_state.output_names:
                if output_name == input_name:
                    raise Exception("transition from %s to itself!" % input_name)
                output_state = self.states[output_name]
                input_state.outputs.append(output_state)
                self.transitions.add((input_state, output_state))
                if input_state not in output_state.inputs:
                    output_state.inputs.append(input_state)

    def inter_state_to_euclidian_position(self, inter_state_position):
        pos1 = inter_state_position.source_state.position
        pos2 = inter_state_position.destination_state.position
        return pos1 + (pos2 - pos1) * inter_state_position.relative_position

    def set_config(self, config):
        for name, state in self.states.iteritems():
            state.position = Vector3d(*config.states[name])

class InterStatePosition:
    def __init__(self, source_state, destination_state, relative_position):
        self.source_state = source_state
        self.destination_state = destination_state
        self.relative_position = relative_position
        self.transition_length = (destination_state.position - source_state.position).mag()

    def __repr__(self):
        return "InterStatePosition(%r, %r, %r)" % (
            self.source_state.name, self.destination_state.name, self.relative_position)

state_machine = StateMachine()

state_machine.add(MC,  [MLB, ML , HB, MB, MLF, MRF, MRB, LLF, HRF])
state_machine.add(MLB, [MC,  ML,  HB, MB, MLF, MRF, MRB, LLF, HRF])
state_machine.add(ML,  [MLB, MLB, HB, MB, MLF, MRF, MRB, LLF, HRF])
state_machine.add(HB,  [MC,  MLB, ML, MB, MLF, MRF, MRB, LLF, HRF])
state_machine.add(MB,  [MC,  MLB, ML, HB, MLF, MRF, MRB, LLF, HRF])
state_machine.add(MLF, [MC,  MLB, ML, HB, MB,  MRF, MRB, LLF, HRF])
state_machine.add(MRF, [])
state_machine.add(MRB, [])
state_machine.add(LLF, [])
state_machine.add(HRF, [])
state_machine.compile()

# state_machine.add(MC,  [MLB])
# state_machine.add(MLB, [])
# state_machine.compile()

# state_machine.add(MB,  [MRF])
# state_machine.add(MRF, [])
# state_machine.compile()
