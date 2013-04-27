import behaviour
import behaviours.mirror
import behaviours.echo
import interpret
import time

MIRROR_THRESHOLD = 3.0

class Behaviour(behaviour.Behaviour):
    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self._mirror = behaviours.mirror.Behaviour(*args)
        self._echo = behaviours.echo.Behaviour(*args)
        self._mode = self._mirror
        self.interpreter.add_callback(interpret.STATE, self._observed_state)
        self._observed_MC_at_time = None

    def process_input(self, input_position, time_increment):
        if self._mode == self._echo and self._observed_MC_at_time and \
           (time.time() - self._observed_MC_at_time) > MIRROR_THRESHOLD:
            print "-> mirror"
            self._echo.enabled = False
            self._mode = self._mirror
            self._mirror.enabled = True
            self.motion_controller.initiate_idle()
        self._mode.process_input(input_position, time_increment)

    def _observed_state(self, state):
        if state == self.MC:
            self._observed_MC_at_time = time.time()
        else:
            self._observed_MC_at_time = None

        if self._mode == self._mirror and state != self.MC:
            print "-> echo"
            self._mirror.enabled = False
            self._mode = self._echo
            self._echo.enabled = True
            self.motion_controller.initiate_idle() # go back to center before echoing
