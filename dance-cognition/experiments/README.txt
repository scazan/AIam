REQUIREMENTS

sudo apt-get install python-opengl python-qt4-gl python-numpy python-scikit-learn

http://cgkit.sourceforge.net
(requires: sudo apt-get install scons g++ libboost-dev libfreeglut3-dev python-dev libboost-python-dev)



PREDICTION WITH BACKPROP NET

Train:

python predict.py point -train prediction_models/point_circular.model 
python predict.py vertices -bvh scenes/valencia_all.bvh -train prediction_models/valencia_vertices.model -training-duration 500
python predict.py hierarchical -bvh scenes/valencia_all.bvh -train prediction_models/valencia_hierarchical.model -training-duration 500

Use:

python predict.py point -model prediction_models/point_circular.model -unit-cube
python predict.py vertices -bvh scenes/valencia_all.bvh -model prediction_models/valencia_vertices.model
python predict.py hierarchical -bvh scenes/valencia_all.bvh -zoom 3 -output-y-offset 1 -model prediction_models/valencia_hierarchical.model


DIMENSIONALITY REDUCTION WITH PCA

Train:

python dim_reduce.py hierarchical -bvh scenes/valencia_all.bvh -train dimensionality_reduction_models/valencia.model -training-data-frame-rate 10 -n 7

Mimic:

python dim_reduce.py hierarchical -bvh scenes/valencia_all.bvh -model dimensionality_reduction_models/valencia.model -zoom 3 -output-y-offset 1

Explore interactively:

python dim_reduce.py hierarchical -bvh scenes/valencia_all.bvh -model dimensionality_reduction_models/valencia.model -zoom 3 -output-y-offset 0.5 -interactive
