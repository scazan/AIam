from experiment import *
from bvh_reader.geo import *
from transformations import quaternion_from_matrix, quaternion_matrix, quaternion_from_euler

class joint(BaseStimulus):
    def get_value(self):
        joint = self.bvh_reader.get_joint(
            self.args.joint, self._t * self.args.bvh_speed)
        return quaternion_from_euler(*joint.rotation_as_euler_angles())

    def get_duration(self):
        return self.bvh_reader.get_duration() / self.args.bvh_speed

    def filename(self):
        return "%s.point_%s" % (self.bvh_reader.filename, self.args.joint)

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
        self._draw_3dim_angle(output)

    def _draw_3dim_angle(self, quaternion):
        rotation_matrix = quaternion_matrix(quaternion)
        transposition_matrix = make_transposition_matrix(1., 0., 0.)
        localtoworld = numpy.dot(rotation_matrix, transposition_matrix)
        worldpos = array([
                  localtoworld[0,3],
                  localtoworld[1,3],
                  localtoworld[2,3],
                  localtoworld[3,3] ])

        glPointSize(3)
        glBegin(GL_POINTS)
        glVertex3f(worldpos[0], worldpos[1], worldpos[2])
        glEnd()
