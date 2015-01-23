#!/bin/sh

PEM=~/keys/aws_alex.pem
REMOTE=ubuntu@54.76.236.123

ssh -i $PEM $REMOTE "rm -rf connectivity/"
scp -i $PEM -r connectivity/ $REMOTE:
scp -i $PEM experiments/event.py $REMOTE:connectivity/
ssh -i $PEM $REMOTE "screen -d -m -S ai_am_server python connectivity/run_websocket_server.py"
