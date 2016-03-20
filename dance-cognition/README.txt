BACKEND REQUIREMENTS

sudo apt-get install python-numpy python-sklearn
sudo pip install tornado==2.4.1

UI REQUIREMENTS

sudo apt-get install python-opengl python-qt4-gl python-imaging
sudo pip install ws4py==0.3.2

INSTALLATION ON OSX

# use macports
sudo port install py27-pyqt4
# use /opt/local/bin/python2.7 instead of python when running

sudo port install py27-pip
sudo pip-2.7 install PyOpenGL
sudo pip-2.7 install tornado==2.4.1
sudo pip-2.7 install ws4py==0.3.2
sudo pip-2.7 install yappi
sudo pip-2.7 install scikit-learn==0.14
sudo pip-2.7 install numpy
sudo pip-2.7 install scipy

# install xquartz from http://www.xquartz.org/ on OS X > 10.7

# for osc
sudo port install liblo
pip-2.7 install cython
# download liblo from http://das.nasophon.de/pyliblo/
python2.7 setup.py build
sudo python2.7 setup.py install

PREDICTION WITH BACKPROP NET

python predict.py -p point_circle -train -training-duration 100
python predict.py -p point_circle -unit-cube

python predict.py -p valencia_point_joint -train -training-duration 100
python predict.py -p valencia_point_joint -unit-cube

python predict.py -p valencia_vertices -train -training-duration 500
python predict.py -p valencia_vertices

python predict.py -p valencia_hierarchical -train -training-duration 500
python predict.py -p valencia_hierarchical --camera=-3.020,-0.810,-0.676,-85.500,10.500 -output-y-offset 0.5


DIMENSIONALITY REDUCTION WITH PCA: ROTATION AS VECTORS

python dim_reduce.py -p valencia_vectors_7d -train
python dim_reduce.py -p valencia_vectors_7d --camera=-3.020,-0.810,-0.676,-85.500,10.500 -output-y-offset 0.5


DIMENSIONALITY REDUCTION WITH PCA: ROTATION AS QUATERNION + MOVEMENT ACROSS SPACE

python dim_reduce.py -p valencia_quaternion_translate_7d -train
python dim_reduce.py -p valencia_quaternion_translate_7d

python dim_reduce.py -p HDM_quaternion_translate_7d -train
python dim_reduce.py -p HDM_quaternion_translate_7d


DIMENSIONALITY REDUCTION WITH PCA: ROTATION AS QUATERNION + FRICTION

python dim_reduce.py -p valencia_quaternion_7d_friction -train
python dim_reduce.py -p valencia_quaternion_7d_friction

Youtube export with UI:
python dim_reduce.py -p valencia_quaternion_7d_friction --mode=improvise --width=854 --height=480 --no-toolbar --html5-toolbar --websockets --camera=-2.256,-0.800,-2.096,-66.000,19.500


QUATERNION EXPERIMENTS

Artificial case with discontinuity problem:
python dim_reduce.py -p angle_quaternion_spiral -train
python dim_reduce.py -p angle_quaternion_spiral -unit-cube

Real case with discontinuity problem:
python dim_reduce.py -p angle_quaternion_HDM_joint -train
python dim_reduce.py -p angle_quaternion_HDM_joint -output-y-offset -1.5 -input-y-offset 0.7 -bvh-speed 5

Real case without discontinuity problem (one out of countless others):
python dim_reduce.py -p angle_quaternion_valencia_joint -train
python dim_reduce.py -p angle_quaternion_valencia_joint -output-y-offset -1.5 -input-y-offset 0.7

Full body real case with discontinuity problem?
python dim_reduce.py -p HDM_quaternion_translate_2d -train
python dim_reduce.py -p HDM_quaternion_translate_2d


EXPONENTIAL MAP EXPERIMENTS

Artificial case with discontinuity problem:
python dim_reduce.py -p expmap_spiral -train
python dim_reduce.py -p expmap_spiral -output-y-offset -1.5 -input-y-offset 0.7

Real case with discontinuity problem:
python dim_reduce.py -p expmap_HDM_joint -train
python dim_reduce.py -p expmap_HDM_joint -output-y-offset -1.5 -input-y-offset 0.7 -bvh-speed 5


NAVIGATOR EXPERIMENTS

Random map:

python test_navigator.py


Valencia model (2d):

python dim_reduce.py -p valencia_quaternion_translate_2d -training-data-frame-rate 10 -train
python test_navigator.py -model profiles/dimensionality_reduction/valencia_quaternion_translate_2d.model


IJCAI / KINETIC DIALOGUES

Preferred location for Alex' ubuntu 12.04:

python dim_reduce.py -p valencia_quaternion_7d_friction --mode=improvise --websockets --velocity=0.3 --novelty=0.03 --extension=0.02 --location_preference=1 --preferred-location=0.873942873678,0.700499395398,0.595342711165,0.225725946789,0.452013014739,0.546188528849,0.532588731088
