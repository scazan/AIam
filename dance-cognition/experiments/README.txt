REQUIREMENTS

sudo apt-get install python-opengl python-qt4-gl python-numpy python-scikit-learn

http://cgkit.sourceforge.net
(requires: sudo apt-get install scons g++ libboost-dev libfreeglut3-dev python-dev libboost-python-dev)



PREDICTION WITH BACKPROP NET

python predict_point.py -pretrain 500
python predict_vertices.py -bvh scenes/valencia_all.bvh -bvh-scale 300 -pretrain 500
python predict_hierarchical.py -bvh scenes/valencia_all.bvh -bvh-scale 300 -pretrain 500


DIMENSIONALITY REDUCTION WITH PCA

python dim_reduce_hierarchical.py -bvh scenes/valencia_all.bvh -model models/valencia.model 
