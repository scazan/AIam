class SingleProcessClient:
    def connect(self, server):
        self._server = server
        self._remote_handler = server.accept_connection(self)

    def received_event(self, event):
        pass

    def send_event(self, event):
        self._remote_handler.received_event(event)
