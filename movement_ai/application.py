import time
import numpy
import random
import collections

from entities.hierarchical import Entity
from fps_meter import FpsMeter

class Avatar:
    def __init__(self, index, entity, behavior):
        self.index = index
        self.entity = entity
        self.behavior = behavior
        
class Application:
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("--frame-rate", type=float, default=50.0)
        parser.add_argument("--show-fps", action="store_true")
        parser.add_argument("--output-receiver-host")
        parser.add_argument("--output-receiver-port", type=int, default=10000)
        parser.add_argument("--output-receiver-type", choices=["bvh", "world"], default="bvh")
        parser.add_argument("--random-seed", type=int)
        parser.add_argument("--memory-size", type=int, default=1000)
        Entity.add_parser_arguments(parser)
        
    def __init__(self, student, avatars, args):
        self._student = student
        self._avatars = avatars
        self._args = args

        if args.random_seed is not None:
            random.seed(args.random_seed)

        if args.output_receiver_host:
            from connectivity import avatar_osc_sender
            if args.output_receiver_type == "world":
                self._output_sender = avatar_osc_sender.AvatarOscWorldSender(
                    args.output_receiver_port, args.output_receiver_host)
            elif args.output_receiver_type == "bvh":
                self._output_sender = avatar_osc_sender.AvatarOscBvhSender(
                    args.output_receiver_port, args.output_receiver_host)
        else:
            self._output_sender = None
            
        self._training_data = collections.deque([], maxlen=args.memory_size)
        self._input = None
        self._desired_frame_duration = 1.0 / self._args.frame_rate
        self._frame_count = 0
        self._previous_frame_time = None
        if self._args.show_fps:
            self._fps_meter = FpsMeter()
            
    def run(self):
        while True:
            self._frame_start_time = time.time()
            self.update()
            self._wait_until_next_frame_is_timely()

    def set_input(self, input_):
        self._input = input_

    def set_student(self, student):
        self._student = student

    def update_if_timely(self):
        self._now = time.time()
        if self._previous_frame_time is None or \
           self._now - self._previous_frame_time >= self._desired_frame_duration:
            self.update()
        
    def update(self):
        if self._input is not None and self._student.supports_incremental_learning():
            self._student.train([self._input])
            self._training_data.append(self._input)
            self._student.probe(self._training_data)
                
        for avatar in self._avatars:
            if self._input is not None and self._student.supports_incremental_learning():
                avatar.behavior.set_normalized_observed_reductions(self._student.normalized_observed_reductions)
            avatar.behavior.proceed(self._desired_frame_duration)
            avatar.entity.update()
            if self._input is not None:
                avatar.behavior.on_input(self._input)
            output = None
            if avatar.behavior.sends_output():
                output = avatar.behavior.get_output()
            else:
                reduction = avatar.behavior.get_reduction()
                if reduction is not None:
                    output = self._student.inverse_transform(numpy.array([reduction]))[0]
            if output is not None:
                if self._output_sender is not None:
                    self._send_output(avatar, output)

        self._previous_frame_time = self._now
        self._frame_count += 1
        if self._args.show_fps:
            self._fps_meter.update()

    def _send_output(self, avatar, output):
        self._output_sender.send_frame(avatar.index, output, avatar.entity)

    def _wait_until_next_frame_is_timely(self):
        frame_duration = time.time() - self._frame_start_time
        if frame_duration < self._desired_frame_duration:
            time.sleep(self._desired_frame_duration - frame_duration)
        
