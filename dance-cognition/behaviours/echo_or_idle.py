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
        self.interpreter.add_callback(interpret.STATE, self._observed_state)
        self.interpreter.add_passivity_callback(
            PASSIVITY_TIMEOUT, self._enable_idle)

    def _enable_idle(self):
        if self.get_mode() != idle:
            self.set_mode(idle)
            self.motion_controller.initiate_idle()

    def _observed_state(self, state):
        if self.get_mode() != echo and state != self.MC:
            self._enable_echo()

    def _enable_echo(self):
        if self.get_mode != echo:
            self.set_mode(echo)
            self.motion_controller.initiate_idle() # go back to center before echoing
