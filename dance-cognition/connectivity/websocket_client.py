import ws4py.client.threadedclient
from websocket_server import WEBSOCKET_PORT, WEBSOCKET_APPLICATION
from event import Event
from event_packing import EventPacker
import contextlib
from tornado.stack_context import StackContext

class WebsocketClient(ws4py.client.threadedclient.WebSocketClient):
    def __init__(self, host):
        address = "ws://%s:%s%s" % (host, WEBSOCKET_PORT, WEBSOCKET_APPLICATION)
        ws4py.client.threadedclient.WebSocketClient.__init__(self, address)

    def opened(self):
        print "connected to server"

    def closed(self, code, reason=None):
        print "connection to server was closed (code=%r reason=%r)" % (code, reason)

    @contextlib.contextmanager
    def _print_exception(self):
        try:
            yield
        except Exception as exception:
            print "received_message failed: %s" % exception

    def received_message(self, message):
        with StackContext(self._print_exception):
            event = EventPacker.unpack(str(message))
            self._event_listener.handle_event(event)

    def received_event(self, event):
        pass

    def send_event(self, event):
        self.send(EventPacker.pack(event))

    def set_event_listener(self, event_listener):
        self._event_listener = event_listener
