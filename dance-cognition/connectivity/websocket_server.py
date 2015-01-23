import tornado.web
import tornado.ioloop
import tornado.websocket
from tornado.httpserver import HTTPServer

WEBSOCKET_APPLICATION = "/aiam"
WEBSOCKET_PORT = 15001

class ClientHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, server, request, **kwargs):
        super(ClientHandler, self).__init__(server, request, **kwargs)
        self._server = server
        server.client_handlers.add(self)

    def on_close(self):
        self._server.client_handlers.remove(self)
        
    def on_message(self, message):
        self._broadcast_to_other_clients(message)
        
    def _broadcast_to_other_clients(self, message):
        for handler in self._server.client_handlers:
            if handler != self:
                handler.write_message(message)

    def check_origin(self, origin):
        return True

    def allow_draft76(self):
        return True

class WebsocketServer(tornado.web.Application):
    def __init__(self, client_handler=ClientHandler, settings={}):
        tornado.web.Application.__init__(
            self,
            [(WEBSOCKET_APPLICATION, client_handler, settings)],
            debug=True)
        self._loop = tornado.ioloop.IOLoop.instance()
        self._listen(WEBSOCKET_PORT)
        self.client_handlers = set()

    def set_event_listener(self, event_listener):
        self._event_listener = event_listener

    def _listen(self, port, address="", **kwargs):
        self._server = HTTPServer(self, **kwargs)
        self._server.listen(port, address)

    def start(self):
        self._loop.start()

    def stop(self):
        self._loop.stop()
        self._server.stop()
