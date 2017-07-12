import copy
import random

class Memory:
    def __init__(self):
        self._memories = []
        self._memorizing = False
        self._recalling = False
        
    def begin_memorizing(self):
        if self._memorizing:
            raise Exception("begin_memorizing invoked when already memorizing")
        self._new_sequence = []
        self._memorizing = True

    def end_memorizing(self):
        if not self._memorizing:
            raise Exception("end_memorizing invoked when not memorizing")
        self._add_new_sequence_to_memory()
        self._memorizing = False

    def _add_new_sequence_to_memory(self):
        self._memories.append(self._new_sequence)

    def on_input(self, input_):
        if self._memorizing:
            self._new_sequence.append(input_)

    def get_output(self):
        if self._recalling:
            if len(self._sequence_being_recalled) == 0:
                self._recalling = False
            else:
                return self._sequence_being_recalled.pop(0)

    def begin_recalling(self):
        self._sequence_being_recalled = copy.copy(random.choice(self._memories))
        self._recalling = True
