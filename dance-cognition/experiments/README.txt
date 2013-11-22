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


DIMENSIONALITY REDUCTION WITH PCA

Train:

python dim_reduce.py hierarchical -bvh scenes/valencia_all.bvh -train -training-data-frame-rate 10 -n 7

Mimic:

python dim_reduce.py hierarchical -bvh scenes/valencia_all.bvh -zoom 3 -output-y-offset 1

Explore interactively:

python dim_reduce.py hierarchical -bvh scenes/valencia_all.bvh -zoom 3 -output-y-offset 0.5 -interactive


QUATERNION EXPERIMENTS

python dim_reduce.py angle_3dim_quaternion -stimulus joint -bvh scenes/valencia_all.bvh -joint RShoulder -train -n 3
python dim_reduce.py angle_3dim_quaternion -stimulus joint -bvh scenes/valencia_all.bvh -joint RShoulder -unit-cube
