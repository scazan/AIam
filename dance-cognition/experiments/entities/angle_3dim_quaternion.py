from experiment import *
from transformations import quaternion_from_euler, euler_from_quaternion
from quaternions import *

class Entity(BaseEntity):
    def __init__(self, *args, **kwargs):
        BaseEntity.__init__(self, *args, **kwargs)
        self._mean_quaternion = numpy.zeros(4)

    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("--hemispherize", action="store_true")

    def probe(self, observations):
        if self.args.hemispherize:
            self._mean_quaternion = find_mean_quaternion(observations)

    def adapt_value_to_model(self, quaternion):
        if self.args.hemispherize:
            if quaternions_are_close(self._mean_quaternion, quaternion):
                return quaternion
            else:
                return -quaternion
        else:
            return quaternion

class joint(BaseStimulus):
    def get_value(self):
        joint = self.bvh_reader.get_joint(
            self.args.joint, self._t * self.args.bvh_speed)
        return quaternion_from_euler(
            *joint.rotation.angles,
             axes=joint.rotation.axes)

    def get_duration(self):
        return self.bvh_reader.get_duration() / self.args.bvh_speed

class spiral(BaseStimulus):
    def get_value(self):
        x = (self._t / 1) % (2*math.pi)
        y = (self._t / 2) % (2*math.pi)
        z = (self._t / 4) % (2*math.pi)
        return quaternion_from_euler(x, y, z)

    def get_duration(self):
        return 2 * math.pi * 4

class Scene(BaseScene):
    def draw_input(self, inp):
        glColor3f(0, 1, 0)
        self._draw_3dim_angle(inp)

    def draw_output(self, output):
        glColor3f(0.5, 0.5, 1.0)
        self._draw_3dim_angle(self.experiment.entity.adapt_value_to_model(output))

    def _draw_3dim_angle(self, quaternion):
        x, y, z = euler_from_quaternion(quaternion, "rxyz")
        glRotatef(math.degrees(x), 1., 0., 0.)
        glRotatef(math.degrees(y), 0., 1., 0.)
        glRotatef(math.degrees(z), 0., 0., 1.)
        glScale(.5, .5, .5)
        glBegin(GL_LINE_STRIP)
        glVertex3f(0, 0, 0)
        glVertex3f(1, 0, 0)
        glVertex3f(1, 1, 0)
        glEnd()
