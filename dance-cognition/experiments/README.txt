REQUIREMENTS

sudo apt-get install python-opengl python-qt4-gl python-numpy python-scikit-learn

http://cgkit.sourceforge.net
(requires: sudo apt-get install scons g++ libboost-dev libfreeglut3-dev python-dev libboost-python-dev)



PREDICTION WITH BACKPROP NET

python predict_point.py -unit-cube -pretrain 500
python predict_vertices.py -bvh scenes/valencia_all.bvh
python predict_hierarchical.py -bvh scenes/valencia_all.bvh -zoom 3 -output-y-offset 1


DIMENSIONALITY REDUCTION WITH PCA

Train:

python dim_reduce_hierarchical.py -bvh scenes/valencia_all.bvh -train models/valencia.model -training-data-frame-rate 10 -n 7

Use:

python dim_reduce_hierarchical.py -bvh scenes/valencia_all.bvh -model models/valencia.model -zoom 3 -output-y-offset 1
