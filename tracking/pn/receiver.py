#!/usr/bin/env python

# Output Format:
# Displacement should be enabled

# Broadcasting:
# BVH should be enabled, with string format

SERVER_PORT_BVH = 7001

import argparse
import socket

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="localhost")
parser.add_argument("--port", default=SERVER_PORT_BVH)
args = parser.parse_args()

def readlines(sock, buffer_size=4096, delim='\n'):
	buffer = ''
	data = True
	while data:
		data = sock.recv(buffer_size)
		buffer += data

		while buffer.find(delim) != -1:
			line, buffer = buffer.split(delim, 1)
			yield line
	return

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print "connecting..."
s.connect((args.host, args.port))
print "ok"

for line in readlines(s, delim='||'):
	values = line.split(" ")
	print len(values)
