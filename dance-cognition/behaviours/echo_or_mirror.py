import behaviour
import behaviours.mirror
import behaviours.echo
import interpret

MIRROR_THRESHOLD = 3.0

class Behaviour(behaviour.Behaviour):
    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self._modes = {
            "mirror": behaviours.mirror.Behaviour(*args),
            "echo": behaviours.echo.Behaviour(*args),
        }
        self._mode_name = None
        self._enable_mirror()
        self.interpreter.add_callback(interpret.STATE, self._observed_state)
        self.interpreter.add_passivity_callback(
            MIRROR_THRESHOLD, self._enable_mirror)

    def process_input(self, input_position, time_increment):
        self._mode.process_input(input_position, time_increment)

    def _enable_mirror(self):
        if self._mode_name != "mirror":
            self._set_mode("mirror")
            self.motion_controller.initiate_idle()

    def _observed_state(self, state):
        if self._mode != "echo" and state != self.MC:
            self._enable_echo()

    def _enable_echo(self):
        if self._mode_name != "echo":
            self._set_mode("echo")
            self.motion_controller.initiate_idle() # go back to center before echoing

    def _set_mode(self, mode_name):
        if self._mode_name != mode_name:
            print "-> %s" % mode_name
            self._mode = self._modes[mode_name]
            self._mode_name = mode_name
            for mode in self._modes.values():
                mode.enabled = (mode == self._mode)
