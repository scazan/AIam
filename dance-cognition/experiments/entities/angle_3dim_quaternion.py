from experiment import *
from transformations import quaternion_from_euler, euler_from_quaternion
from quaternions import *

class QuaternionModel:
    mean_quaternion = None

class QuaternionEntity(BaseEntity):
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("--hemispherize", action="store_true")

    def probe(self, observations):
        if self.args.hemispherize:
            self.model = QuaternionModel()
            self.model.mean_quaternion = find_mean_quaternion(observations)

    def adapt_value_to_model(self, quaternion):
        if self.args.hemispherize:
            return hemispherize(quaternion, self.model.mean_quaternion)
        else:
            return quaternion

class Scene(BaseScene):
    def process_input(self, inp):
        return inp

    def process_output(self, output):
        return self.experiment.entity.adapt_value_to_model(output)

    def draw_input(self, inp):
        glColor3f(0, 1, 0)
        self._draw_3dim_angle(inp)

    def draw_output(self, output):
        glColor3f(0.5, 0.5, 1.0)
        self._draw_3dim_angle(output)

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
