BACKEND REQUIREMENTS

sudo apt-get install python-numpy python-scikit-learn
sudo pip install tornado==2.4.1

UI REQUIREMENTS

sudo apt-get install python-opengl python-qt4-gl
sudo pip install ws4py==0.3.2

INSTALLATION ON OSX

# use macports
sudo port install py27-pyqt4 py27-numpy py27-scikit-learn py27-opengl
# use /opt/local/bin/python2.7 instead of python when running

sudo port install py27-pip
sudo pip-2.7 install tornado==2.4.1
sudo pip-2.7 install ws4py==0.3.2

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


DIMENSIONALITY REDUCTION WITH PCA: ROTATION AS QUATERNION

python dim_reduce.py -p valencia_quaternion_7d -train
python dim_reduce.py -p valencia_quaternion_7d --camera=-3.020,-0.810,-0.676,-85.500,10.500 -output-y-offset 0.5


DIMENSIONALITY REDUCTION WITH PCA: INCLUDING MOVEMENT ACROSS SPACE

python dim_reduce.py -p valencia_quaternion_translate_7d -train
python dim_reduce.py -p valencia_quaternion_translate_7d

Youtube export with UI:
python dim_reduce.py -p valencia_quaternion_translate_7d --mode=improvise --width=854 --height=480 --no-toolbar --html5-toolbar --websockets --camera=-2.256,-0.800,-2.096,-66.000,19.500

python dim_reduce.py -p HDM_quaternion_translate_7d -train
python dim_reduce.py -p HDM_quaternion_translate_7d


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
python dim_reduce.py -p HDM_quaternion_translate_2d



NAVIGATOR EXPERIMENTS

Random map:

python test_navigator.py


Valencia model (2d):

python dim_reduce.py -p valencia_quaternion_translate_2d -training-data-frame-rate 10 -train
python test_navigator.py -model profiles/dimensionality_reduction/valencia_quaternion_translate_2d.model
