REQUIREMENTS

sudo apt-get install python-opengl python-qt4-gl python-numpy python-scikit-learn

http://cgkit.sourceforge.net
(requires: sudo apt-get install scons g++ libboost-dev libfreeglut3-dev python-dev libboost-python-dev)



PREDICTION WITH BACKPROP NET

Train:

python predict.py point -train
python predict.py vertices -bvh scenes/valencia_all.bvh -train -training-duration 500
python predict.py hierarchical -bvh scenes/valencia_all.bvh -train -training-duration 500

Use:

python predict.py point -unit-cube
python predict.py vertices -bvh scenes/valencia_all.bvh
python predict.py hierarchical -bvh scenes/valencia_all.bvh -zoom 3 -output-y-offset 1


DIMENSIONALITY REDUCTION WITH PCA

Train:

python dim_reduce.py hierarchical -bvh scenes/valencia_all.bvh -train -training-data-frame-rate 10 -n 7

Mimic:

python dim_reduce.py hierarchical -bvh scenes/valencia_all.bvh -zoom 3 -output-y-offset 1

Explore interactively:

python dim_reduce.py hierarchical -bvh scenes/valencia_all.bvh -zoom 3 -output-y-offset 0.5 -interactive
