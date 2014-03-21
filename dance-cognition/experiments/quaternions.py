import numpy

def find_mean_quaternion(quaternions):
    result = numpy.zeros(4)
    for quaternion in quaternions:
        quaternion = hemispherize(quaternion, quaternions[0])
        result += quaternion
    return result / len(quaternions)

def hemispherize(q, reference):
    if quaternions_are_close(q, reference):
        return q
    else:
        return -q

def quaternions_are_close(q1, q2):
    return numpy.dot(q1, q2) >= 0
