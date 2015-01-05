import transformations
import so3
import vectorops

def expmap_from_euler(ai, aj, ak, axes="sxyz"):
    matrix = transformations.euler_matrix(ai, aj, ak, axes)
    R = so3.from_matrix(matrix)
    moment = so3.moment(R)
    axis_angle_parameters = vectorops.unit(moment) + [vectorops.norm(moment)]
    return axis_angle_parameters

def euler_from_expmap(axis_angle_parameters, axes="sxyz"):
    axis_angle = (axis_angle_parameters[0:3], axis_angle_parameters[3])
    R = so3.from_axis_angle(axis_angle)
    matrix = so3.matrix(R)
    x, y, z = transformations.euler_from_matrix(matrix, axes)
    return x, y, z
