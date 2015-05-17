import numpy

def find_mean_quaternion(quaternions):
    return sum([hemispherize(q, quaternions[0]) for q in quaternions]) / len(quaternions)

def hemispherize(q, reference):
    if quaternions_are_close(q, reference):
        return q
    else:
        return -q

def quaternions_are_close(q1, q2):
    return numpy.dot(q1, q2) >= 0
