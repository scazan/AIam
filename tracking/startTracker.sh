#!/bin/bash

MIN_AREA=220000
MAX_AREA=1000800
OSC_HOST=192.168.48.97
TEMPORAL_SMOOTHING=1

./opencv/Tracker -zt 2800 -min-area $MIN_AREA -max-area $MAX_AREA -ts $TEMPORAL_SMOOTHING -device 1d27/0601@1/64 -camera-id 0 -osc-host $OSC_HOST &
./opencv/Tracker -zt 2800 -min-area $MIN_AREA -max-area $MAX_AREA -ts $TEMPORAL_SMOOTHING -device 1d27/0601@1/67 -camera-id 3 -osc-host $OSC_HOST &
./opencv/Tracker -zt 2800 -min-area $MIN_AREA -max-area $MAX_AREA -ts $TEMPORAL_SMOOTHING -device 1d27/0601@1/70 -camera-id 1 -osc-host $OSC_HOST &
./opencv/Tracker -zt 2800 -min-area $MIN_AREA -max-area $MAX_AREA -ts $TEMPORAL_SMOOTHING -device 1d27/0601@1/72 -camera-id 2 -osc-host $OSC_HOST &
