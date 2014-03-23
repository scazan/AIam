REQUIREMENTS

sudo apt-get install python-opengl python-qt4-gl python-numpy python-scikit-learn

http://cgkit.sourceforge.net
(requires: sudo apt-get install scons g++ libboost-dev libfreeglut3-dev python-dev libboost-python-dev)



PREDICTION WITH BACKPROP NET

python predict.py -p point_circle -train -training-duration 100
python predict.py -p point_circle -unit-cube

python predict.py -p valencia_point_joint -train -training-duration 100
python predict.py -p valencia_point_joint -unit-cube

python predict.py -p valencia_vertices -train -training-duration 500
python predict.py -p valencia_vertices

python predict.py -p valencia_hierarchical -train -training-duration 500
python predict.py -p valencia_hierarchical -zoom 3


DIMENSIONALITY REDUCTION WITH PCA: ROTATION AS VECTORS

python dim_reduce.py -p valencia_vectors_7d -train
python dim_reduce.py -p valencia_vectors_7d -zoom 3


DIMENSIONALITY REDUCTION WITH PCA: ROTATION AS QUATERNION

python dim_reduce.py -p valencia_quaternion_7d -train
python dim_reduce.py -p valencia_quaternion_7d -zoom 3


DIMENSIONALITY REDUCTION WITH PCA: INCLUDING MOVEMENT ACROSS SPACE

python dim_reduce.py -p valencia_quaternion_translate_7d -train
python dim_reduce.py -p valencia_quaternion_translate_7d -zoom 1.8

python dim_reduce.py -p HDM_quaternion_translate_7d -train
python dim_reduce.py -p HDM_quaternion_translate_7d -zoom 1.4


QUATERNION EXPERIMENTS

Artificial case with discontinuity problem:
python dim_reduce.py -p angle_quaternion_spiral -train
python dim_reduce.py -p angle_quaternion_spiral -unit-cube

Real case with discontinuity problem:
python dim_reduce.py -p angle_quaternion_HDM_joint -train
python dim_reduce.py -p angle_quaternion_HDM_joint -unit-cube -bvh-speed 5

Real case without discontinuity problem (one out of countless others):
python dim_reduce.py -p angle_quaternion_valencia_joint -train
python dim_reduce.py -p angle_quaternion_valencia_joint -unit-cube

Full body real case with discontinuity problem?
python dim_reduce.py -p HDM_quaternion_translate_2d -train
python dim_reduce.py -p HDM_quaternion_translate_2d -zoom 1.4



NAVIGATOR EXPERIMENTS

Random map:

python test_navigator.py


Valencia model (2d):

python dim_reduce.py -p valencia_quaternion_translate_2d -training-data-frame-rate 10 -train
python test_navigator.py -model profiles/dimensionality_reduction/valencia_quaternion_translate_2d.model
