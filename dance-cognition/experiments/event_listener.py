class EventListener:
    def __init__(self):
        self._handlers = {}

    def add_event_handler(self, event_type, handler):
        self._handlers[event_type] = handler

    def handle_event(self, event):
        try:
            handler = self._handlers[event.type]
            handler(event)
        except KeyError:
            raise Exception("unknown event type %s" % event.type)
