class SingleProcessClient:
    def __init__(self, server):
        self._server = server

    def connect(self):
        self._remote_handler = self._server.accept_connection(self)

    def send_event(self, event):
        self._remote_handler.received_event(event)

    def set_event_listener(self, event_listener):
        self._event_listener = event_listener

    def received_event(self, event):
        self._event_listener.received_event(event)
