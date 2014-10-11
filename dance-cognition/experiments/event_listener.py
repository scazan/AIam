class EventListener:
    def __init__(self):
        self._handlers = {}

    def add_event_handler(self, event_type, handler):
        self._handlers[event_type] = handler

    def handle_event(self, event):
        try:
            handler = self._handlers[event.type]
        except KeyError:
            raise Exception("Unknown event type %r. Handlers added for %r." % (
                    event.type, self._handlers.keys()))
        handler(event)
