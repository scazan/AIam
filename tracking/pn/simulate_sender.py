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
        previous_frame_index = None
        start_time = time.time()
        while True:
            frame_index = int((time.time() - start_time) / bvh_reader.get_frame_time()) % \
                          bvh_reader.get_num_frames()
            if frame_index != previous_frame_index:
                frame = bvh_reader.get_frame_by_index(frame_index)
                line = "mock_ID mock_name " + " ".join([str(value) for value in frame])
                self.request.sendall("%s||\n" % line)
                previous_frame_index = frame
            else:
                time.sleep(bvh_reader.get_frame_time() / 10)
        
server = SocketServer.TCPServer(("localhost", args.port), PnSimulatorHandler)
server.serve_forever()
