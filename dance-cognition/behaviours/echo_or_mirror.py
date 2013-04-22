import behaviour
import behaviours.mirror
import behaviours.echo
import copy
import time

TEMPORAL_THRESHOLD_FOR_ECHO_TO_MIRROR = 5.0

class WaitBehaviour:
    MOVE_DURATION = 3.0

    def set_output(self, output):
        self._output = copy.copy(output)
        self._relative_position_start = output.relative_position
        if output.relative_position == 0.0:
            self._duration_to_center = 0.0
        else:
            distance = (output.source_state.position - output.destination_state.position).mag()
            self._duration_to_center = self.MOVE_DURATION * output.relative_position / distance
        self._t = 0.0

    def process_input(self, input_position, time_increment):
        self._t += time_increment
        self._output.relative_position = max(
            0.0,
            self._relative_position_start * (1 - self._t / self._duration_to_center))

    def output(self):
        return self._output

class Behaviour(behaviour.Behaviour):
    def __init__(self, *args):
        behaviour.Behaviour.__init__(self, *args)
        self._mirror_behaviour = behaviours.mirror.Behaviour(*args)
        self._echo_behaviour = behaviours.echo.Behaviour(*args)
        self._wait_behaviour = WaitBehaviour()
        self._current_behaviour = self._mirror_behaviour
        self._entered_mc_at_time = None

    def process_input(self, input_position, time_increment):
        self._mirror_behaviour.process_input(input_position, time_increment)
        self._echo_behaviour.process_input(input_position, time_increment)

        if self._current_behaviour == self._mirror_behaviour:
            if self._echo_behaviour.observed_state() != self.MC:
                self._switch_from_mirror_to_echo()
        elif self._current_behaviour == self._wait_behaviour:
            self._wait_behaviour.process_input(input_position, time_increment)
            self._try_switch_from_wait_to_echo()
        elif self._current_behaviour == self._echo_behaviour:
            if self._echo_behaviour.observed_state() == self.MC:
                if self._entered_mc_at_time is None:
                    self._entered_mc_at_time = time.time()
                duration_in_mc = time.time() - self._entered_mc_at_time
                if duration_in_mc > TEMPORAL_THRESHOLD_FOR_ECHO_TO_MIRROR:
                    self._switch_to_mirror()
            else:
                self._entered_mc_at_time = None

    def _switch_from_mirror_to_echo(self):
        echo_output = self._echo_behaviour.output()
        if echo_output and \
           echo_output.source_state == self.MC and \
           echo_output.destination_state == self._mirror_behaviour.output().destination_state:
            print "WARNING: jumping from mirror to echo WITHOUT SMOOTH TRANSITION"
            self._current_behaviour = self._echo_behaviour
        elif echo_output:
            print "waiting for opportunity to switch from mirror to echo"
            self._current_behaviour = self._wait_behaviour
            self._wait_behaviour.set_output(self._mirror_behaviour.output())

    def _try_switch_from_wait_to_echo(self):
        echo_output = self._echo_behaviour.output()
        if echo_output and \
           echo_output.source_state == self.MC and \
           self._wait_behaviour.output().relative_position < 0.001:
            print "switching from wait to echo"
            self._current_behaviour = self._echo_behaviour

    def _switch_to_mirror(self):
        print "WARNING: switching to mirror WITHOUT SMOOTH TRANSITION"
        self._current_behaviour = self._mirror_behaviour

    def output(self):
        return self._current_behaviour.output()

    def observed_state(self):
        return self._echo_behaviour.observed_state()
