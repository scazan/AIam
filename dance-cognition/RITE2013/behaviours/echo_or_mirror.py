import behaviour
from behaviours import mirror
from behaviours import echo
import interpret

PASSIVITY_TIMEOUT = 3.0

class Behaviour(behaviour.Behaviour):
    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self.add_mode(mirror, *args)
        self.add_mode(echo, *args)
        self._enable_mirror()
        self.interpreter.add_callback(interpret.STATE, self._observed_state)
        self.interpreter.add_passivity_callback(
            PASSIVITY_TIMEOUT, self._enable_mirror)

    def _enable_mirror(self):
        if self.get_mode() != mirror:
            self.set_mode(mirror)

    def _observed_state(self, state):
        if self.get_mode() != echo and state != self.MC:
            self._enable_echo()

    def _enable_echo(self):
        if self.get_mode != echo:
            self.set_mode(echo)
