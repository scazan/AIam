from receiver import SERVER_PORT_BVH
import argparse
import SocketServer
import time

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../../dance-cognition")
from bvh.bvh_reader import BvhReader

parser = argparse.ArgumentParser()
parser.add_argument("bvh")
parser.add_argument("--port", type=int, default=SERVER_PORT_BVH)
args = parser.parse_args()

bvh_reader = BvhReader(args.bvh)
bvh_reader.read()

class PnSimulatorHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        frame_index = 0
        while True:
            frame = bvh_reader.get_frame_by_index(frame_index)
            line = "mock_ID mock_name " + " ".join([str(value) for value in frame])
            self.request.sendall("%s||\n" % line)
            frame_index = (frame_index + 1) % bvh_reader.get_num_frames()
            time.sleep(bvh_reader.get_frame_time())
        
server = SocketServer.TCPServer(("localhost", args.port), PnSimulatorHandler)
server.serve_forever()
