#!/bin/sh

#INTERPRETER_VIEWER_ARGS=--with-viewer

cd ~/projects/AIam/dance-cognition
python dim_reduce.py -p valencia_quaternion_7d_friction --mode=improvise --color-scheme=black --no-toolbar --floor-renderer=checkerboard --preferred-location=0.0783783783784,0.315135135135,0.590810810811,0.240540540541,0.392972972973,0.448108108108,0.626486486486 --websockets --fullscreen --fullscreen-display=1 --launch-when-ready="gnome-terminal -e 'python interpret_user_movement.py $INTERPRETER_VIEWER_ARGS --tracker=0,-7 --active-area-center=0,3300'"

# force terminal window to stay open
bash
