import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../experiments")

from websocket_server import WebsocketServer

server = WebsocketServer()
server.start()
