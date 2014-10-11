import tornado.web
import tornado.ioloop
import tornado.websocket
from tornado.httpserver import HTTPServer
from event_packing import EventPacker

WEBSOCKET_APPLICATION = "/aiam"
WEBSOCKET_PORT = 15001

class ClientHandler(tornado.websocket.WebSocketHandler):
    def on_message(self, message):
        event = EventPacker.unpack(str(message))
        self.received_event(event, self)
        
    def send_event(self, event):
        self.write_message(EventPacker.pack(event))

class WebsocketServer(tornado.web.Application):
    def __init__(self, client_handler=ClientHandler, settings={}):
        tornado.web.Application.__init__(
            self,
            [(WEBSOCKET_APPLICATION, client_handler, settings)],
            debug=True)
        self._loop = tornado.ioloop.IOLoop.instance()
        self._listen(WEBSOCKET_PORT)

    def _listen(self, port, address="", **kwargs):
        self._server = HTTPServer(self, **kwargs)
        self._server.listen(port, address)

    def start(self):
        self._loop.start()

    def stop(self):
        self._loop.stop()
        self._server.stop()

    def add_periodic_callback(self, callback, callback_time):
        periodic_callback = tornado.ioloop.PeriodicCallback(callback, callback_time, self._loop)
        periodic_callback.start()
