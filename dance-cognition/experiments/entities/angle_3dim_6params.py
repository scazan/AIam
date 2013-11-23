from experiment import *
from angle_parameters import euler_to_vector6d, vector6d_to_euler

class joint(BaseStimulus):
    def get_value(self):
        joint = self.bvh_reader.get_joint(
            self.args.joint, self._t * self.args.bvh_speed)
        angles_xyz = self._transform_to_xyz(joint.rotation)
        return euler_to_vector6d(*angles_xyz)

    def _transform_to_xyz(self, euler):
        if euler.axes[1:] == "xyz":
            return euler.angles
        else:
            return euler_from_matrix(euler_matrix(
                    *euler.angles, axes=euler.axes))

    def get_duration(self):
        return self.bvh_reader.get_duration() / self.args.bvh_speed

    def filename(self):
        return "%s.point_%s" % (self.bvh_reader.filename, self.args.joint)

class spiral(BaseStimulus):
    def get_value(self):
        x = (self._t / 1) % (2*math.pi)
        y = (self._t / 2) % (2*math.pi)
        z = (self._t / 4) % (2*math.pi)
        return euler_to_vector6d(x, y, z)

    def get_duration(self):
        return 2 * math.pi * 4

class Scene(BaseScene):
    def draw_input(self, inp):
        glColor3f(0, 1, 0)
        self._draw_3dim_angle(inp)

    def draw_output(self, output):
        glColor3f(0.5, 0.5, 1.0)
        self._draw_3dim_angle(output)

    def _draw_3dim_angle(self, vector6d):
        x, y, z = vector6d_to_euler(vector6d)
        glRotatef(math.degrees(x), 1., 0., 0.)
        glRotatef(math.degrees(y), 0., 1., 0.)
        glRotatef(math.degrees(z), 0., 0., 1.)
        glScale(.5, .5, .5)
        glBegin(GL_LINE_STRIP)
        glVertex3f(0, 0, 0)
        glVertex3f(1, 0, 0)
        glVertex3f(1, 1, 0)
        glEnd()
