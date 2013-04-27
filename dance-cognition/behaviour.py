# TODO:
# add method leave_free_movement. this will be used by echo_or_mirror when detecting that partner is away from center.
# add callback for entering resting state (from free movement). this will be used by echo_or_mirror to potentially start new move.

from states import MC, InterStatePosition
IDLE = "idle"
MOVE = "move"
FREE = "free"

SPEED = 1.0

class Behaviour:
    def __init__(self, state_machine, interpreter):
        self._state_machine = state_machine
        self.interpreter = interpreter
        self.MC = state_machine.states[MC]
        self._resting_state = self.MC
        self._set_mode(IDLE)
        self._desired_mode = IDLE

    def get_mode(self):
        return self._mode

    def _set_mode(self, mode):
        print mode
        self._mode = mode

    def process_input(self, input_position, time_increment):
        self._time_increment = time_increment
        if self._mode == IDLE:
            if self._desired_mode == FREE:
                self._set_mode(FREE)
            elif self._desired_mode == MOVE and self.can_move_to(self._destination_state):
                self._set_mode(MOVE)
        elif self._mode == MOVE:
            if self._desired_mode == MOVE:
                self._move_time += time_increment
                if self._move_time > self._move_duration:
                    print "completed move"
                    self._set_mode(IDLE)
                    self._resting_state = self._destination_state
            else:
                self._move_towards_center()
        elif self._mode == FREE:
            if self._desired_mode == FREE:
                self._move_towards_desired_cursor()
            else:
                self._move_towards_center()

    def _move_towards_center(self):
        delta = self._time_increment * SPEED
        if self._cursor.source_state == self.MC:
            self._cursor.relative_position = max(
                0.0, self._cursor.relative_position - delta)
            if self._desired_mode != FREE and self._cursor.relative_position < 0.001:
                print "reached center"
                self._set_mode(IDLE)
        elif self._cursor.destination_state == self.MC:
            self._cursor.relative_position = min(
                1.0, self._cursor.relative_position + delta)
            if self._desired_mode != FREE and self._cursor.relative_position > 0.999:
                print "reached center"
                self._set_mode(IDLE)
        else:
            raise Exception("don't know how to move towards center from %s" % self._cursor)

    def _move_towards_desired_cursor(self):
        if self._cursor.source_state == self._desired_cursor.source_state and \
           self._cursor.destination_state == self._desired_cursor.destination_state:
            self._move_along_transition_towards_relative_position(
                self._desired_cursor.relative_position)
        elif self._cursor.source_state == self._desired_cursor.source_state and \
             self._cursor.relative_position < 0.001:
            self._cursor.destination_state = self._desired_cursor.destination_state
        else:
            self._move_towards_center()

    def _move_along_transition_towards_relative_position(self, desired_relative_position):
        allowed_relative_distance = self._time_increment * SPEED / self._cursor.transition_length
        actual_relative_distance = abs(
            desired_relative_position - self._cursor.relative_position)
        if allowed_relative_distance >= actual_relative_distance:
            new_relative_position = desired_relative_position
        else:
            if desired_relative_position > self._cursor.relative_position:
                sign = 1
            else:
                sign = -1
            new_relative_position = self._cursor.relative_position + sign * \
                allowed_relative_distance
        new_relative_position = self._clamp(new_relative_position, 0, 1)
        self._cursor.relative_position = new_relative_position

    def initiate_movement_to(self, destination_state, duration):
        self._desired_mode = MOVE
        self._destination_state = destination_state
        self._move_time = 0.0
        self._move_duration = duration

    def initiate_idle(self):
        self._desired_mode = IDLE

    def initiate_free_movement(self):
        self._desired_mode = FREE

    def can_move_to(self, destination_state):
        return self._mode == IDLE and \
            destination_state in self._resting_state.outputs + self._resting_state.inputs

    def output(self):
        if self._mode == MOVE:
            self._cursor = self._inter_state_position_in_current_move()
        elif self._mode == IDLE:
            # TODO: optimize, always choose same output state
            self._cursor = InterStatePosition(
                self._resting_state,
                (self._resting_state.outputs + self._resting_state.inputs)[0],
                0.0)
        return self._cursor

    def _inter_state_position_in_current_move(self):
        return InterStatePosition(
            self._resting_state,
            self._destination_state,
            self._move_time / self._move_duration)

    def set_cursor(self, source_state, destination_state, relative_position):
        self._desired_cursor = InterStatePosition(
            source_state, destination_state, relative_position)

    def _clamp(self, v, v_min, v_max):
        return max(min(v, v_max), v_min)
