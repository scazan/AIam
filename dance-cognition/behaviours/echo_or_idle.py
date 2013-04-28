import behaviour
from behaviours import idle
from behaviours import echo
import interpret

PASSIVITY_TIMEOUT = 3.0

class Behaviour(behaviour.Behaviour):
    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self.add_mode(idle, *args)
        self.add_mode(echo, *args)
        self._enable_idle()
        self.interpreter.add_callback(interpret.ACTIVITY, self._enable_echo)
        self.interpreter.add_passivity_callback(PASSIVITY_TIMEOUT, self._enable_idle)

    def _enable_idle(self):
        if self.get_mode() != idle:
            self.set_mode(idle)

    def _enable_echo(self):
        if self.get_mode != echo:
            self.set_mode(echo)
