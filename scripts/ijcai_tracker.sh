#!/bin/bash

killall -9 Tracker

cd ~/projects/AIam/tracking
./Bin/x64-Release/Tracker -smooth 0.6

# force terminal window to stay open
bash
