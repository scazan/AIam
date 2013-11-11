REQUIREMENTS

sudo apt-get install python-opengl python-qt4-gl python-numpy python-scikit-learn

http://cgkit.sourceforge.net
(requires: sudo apt-get install scons g++ libboost-dev libfreeglut3-dev python-dev libboost-python-dev)



PREDICTION WITH BACKPROP NET

Train:

python predict_vertices.py -bvh scenes/valencia_all.bvh -train prediction_models/valencia_vertices.model -training-duration 500
python predict_hierarchical.py -bvh scenes/valencia_all.bvh -train prediction_models/valencia_hierarchical.model -training-duration 500

Use:

python predict_point.py -unit-cube
python predict_vertices.py -bvh scenes/valencia_all.bvh -model prediction_models/valencia_vertices.model
python predict_hierarchical.py -bvh scenes/valencia_all.bvh -zoom 3 -output-y-offset 1 -model prediction_models/valencia_hierarchical.model


DIMENSIONALITY REDUCTION WITH PCA

Train:

python dim_reduce_hierarchical.py -bvh scenes/valencia_all.bvh -train dimensionality_reduction_models/valencia.model -training-data-frame-rate 10 -n 7

Use:

python dim_reduce_hierarchical.py -bvh scenes/valencia_all.bvh -model dimensionality_reduction_models/valencia.model -zoom 3 -output-y-offset 1
