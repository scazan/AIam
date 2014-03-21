import numpy

def find_mean_quaternion(quaternions):
    result = numpy.zeros(4)
    for quaternion in quaternions:
        if not quaternions_are_close(quaternions[0], quaternion):
            quaternion = -quaternion
        result += quaternion
    return result / len(quaternions)

def quaternions_are_close(q1, q2):
    return numpy.dot(q1, q2) >= 0
