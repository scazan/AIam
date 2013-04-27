from states import state_machine, MC, InterStatePosition
from motion_durations import get_duration

SPEED = 1.0
DURATION_FLEXIBILITY = 0.2

IDLE = "idle"
MOVE = "move"
FREE = "free"

class MotionController:
    def __init__(self):
        self.MC = state_machine.states[MC]
        self._resting_state = self.MC
        self._set_mode(IDLE)
        self._desired_mode = IDLE

    def get_mode(self):
        return self._mode

    def _set_mode(self, mode):
        print mode
        self._mode = mode

    def update(self, time_increment):
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
                    self._cursor = self._inter_state_position_in_current_move()
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
            self._move_cursor(-delta)
            if self._desired_mode != FREE and self._cursor.relative_position < 0.001:
                print "reached center"
                self._resting_state = self.MC
                self._set_mode(IDLE)
        elif self._cursor.destination_state == self.MC:
            self._move_cursor(delta)
            if self._desired_mode != FREE and self._cursor.relative_position > 0.999:
                print "reached center"
                self._resting_state = self.MC
                self._set_mode(IDLE)
        else:
            if self._cursor.relative_position < 0.001:
                self._cursor.destination_state = self.MC
            elif self._cursor.relative_position > 0.999:
                self._cursor.source_state = self.MC
            else:
                self._move_along_transition_towards_nearest_state()

    def _move_cursor(self, delta):
        self._cursor.relative_position = self._clamp(
            self._cursor.relative_position + delta, 0.0, 1.0)

    def _move_along_transition_towards_nearest_state(self):
        delta = self._time_increment * SPEED
        if self._cursor.relative_position < 0.5:
            self._move_cursor(-delta)
        else:
            self._move_cursor(delta)

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

    def initiate_movement_to(self, destination_state, desired_duration=None):
        recorded_duration = get_duration(self._resting_state, destination_state)
        if desired_duration is None:
            duration = recorded_duration
        else:
            duration = self._adjusted_duration(recorded_duration, desired_duration)
        self._desired_mode = MOVE
        self._destination_state = destination_state
        self._move_time = 0.0
        self._move_duration = duration

    def _adjusted_duration(self, recorded_duration, desired_duration):
        relative_difference = abs(desired_duration - recorded_duration) / recorded_duration
        if relative_difference < DURATION_FLEXIBILITY:
            print "desired duration %.2f near enough %.2f (relative_difference=%.2f)" % (
                desired_duration, recorded_duration, relative_difference)
            return desired_duration
        else:
            if desired_duration > recorded_duration:
                adjusted_duration = recorded_duration * (1 + DURATION_FLEXIBILITY)
            else:
                adjusted_duration = recorded_duration * (1 - DURATION_FLEXIBILITY)
            print "desired duration %.2f adjusted to %.2f (relative_difference %.2f too high)" % (
                desired_duration, adjusted_duration, relative_difference)
            return adjusted_duration

    def initiate_idle(self):
        self._desired_mode = IDLE

    def initiate_free_movement(self):
        self._desired_mode = FREE

    def can_move_to(self, destination_state):
        return self._mode == IDLE and \
            destination_state in self._resting_state.outputs + self._resting_state.inputs

    def output(self):
        if self._mode == IDLE:
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
