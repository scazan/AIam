import tornado.web
import tornado.ioloop
import tornado.websocket
from tornado.httpserver import HTTPServer
from event import Event
from event_packing import EventPacker

WEBSOCKET_APPLICATION = "/aiam"
WEBSOCKET_PORT = 15001

class ClientHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, server, request, **kwargs):
        print "client connected"
        super(ClientHandler, self).__init__(server, request, **kwargs)
        self._server = server
        self._registered = False
        server.client_handlers.add(self)

    def get_name(self):
        return self._name

    def on_close(self):
        print "client disconnected"
        self._server.client_handlers.remove(self)
        
    def on_message(self, message):
        event = EventPacker.unpack(str(message))
        self._handle_event(message, event)

    def _handle_event(self, message, event):
        if self._registered:
            self._broadcast_to_other_clients(message, event)
        else:
            self._register(event)
        
    def _broadcast_to_other_clients(self, message, event):
        for handler in self._server.client_handlers:
            if handler != self and not (event.source is not None and event.source == handler.get_name()):
                handler.write_message(message)

    def _register(self, event):
        if event.type == Event.REGISTER:
            self._name = event.content
            self._registered = True
            print "registered client with name %r" % self._name
        else:
            print "Expected event type REGISTER but got %r" % event.type

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
