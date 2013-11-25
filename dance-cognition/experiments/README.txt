REQUIREMENTS

sudo apt-get install python-opengl python-qt4-gl python-numpy python-scikit-learn

http://cgkit.sourceforge.net
(requires: sudo apt-get install scons g++ libboost-dev libfreeglut3-dev python-dev libboost-python-dev)



PREDICTION WITH BACKPROP NET

python predict.py point -stimulus circle -train -training-duration 100
python predict.py point -stimulus circle -unit-cube

python predict.py point -stimulus joint -bvh scenes/valencia_all.bvh -train -training-duration 100
python predict.py point -stimulus joint -bvh scenes/valencia_all.bvh -unit-cube

python predict.py vertices -bvh scenes/valencia_all.bvh -train -training-duration 500
python predict.py vertices -bvh scenes/valencia_all.bvh

python predict.py hierarchical -bvh scenes/valencia_all.bvh -train -training-duration 500
python predict.py hierarchical -bvh scenes/valencia_all.bvh -zoom 3 -output-y-offset 1


DIMENSIONALITY REDUCTION WITH PCA: ROTATION AS VECTORS

Train / mimic / explore interactively:

python dim_reduce.py hierarchical -r vectors -bvh scenes/valencia_all.bvh -train -training-data-frame-rate 10 -n 7
python dim_reduce.py hierarchical -r vectors -bvh scenes/valencia_all.bvh -zoom 3 -output-y-offset 1


DIMENSIONALITY REDUCTION WITH PCA: ROTATION AS QUATERNION

python dim_reduce.py hierarchical -r quaternion -bvh scenes/valencia_all.bvh -train -training-data-frame-rate 10 -n 7
python dim_reduce.py hierarchical -r quaternion -bvh scenes/valencia_all.bvh -zoom 3 -output-y-offset 1


DIMENSIONALITY REDUCTION WITH PCA: INCLUDING MOVEMENT ACROSS SPACE

python dim_reduce.py hierarchical -r quaternion -bvh scenes/valencia_all.bvh -train -training-data-frame-rate 10 -n 7 --translate --translation-weight 5
python dim_reduce.py hierarchical -r quaternion -bvh scenes/valencia_all.bvh --translate --translation-weight 5 -zoom 1 -output-y-offset 1


VECTOR6D EXPERIMENTS (Euler angle components as vectors)

python dim_reduce.py angle_3dim_6params -stimulus spiral -train -n 5
python dim_reduce.py angle_3dim_6params -stimulus spiral -unit-cube

python dim_reduce.py angle_3dim_6params -stimulus joint -bvh scenes/valencia_all.bvh -joint RShoulder -train -n 5
python dim_reduce.py angle_3dim_6params -stimulus joint -bvh scenes/valencia_all.bvh -joint RShoulder -unit-cube


QUATERNION EXPERIMENTS

Artificial case with discontinuity problem:
python dim_reduce.py angle_3dim_quaternion -stimulus spiral -train -n 3
python dim_reduce.py angle_3dim_quaternion -stimulus spiral -unit-cube

Real case without discontinuity problem:
python dim_reduce.py angle_3dim_quaternion -stimulus joint -bvh scenes/valencia_all.bvh -joint RShoulder -train -n 3
python dim_reduce.py angle_3dim_quaternion -stimulus joint -bvh scenes/valencia_all.bvh -joint RShoulder -unit-cube
