import sched
import time

class SingleProcessServer:
    def __init__(self, handler_class, **handler_kwargs):
        self._handler_class = handler_class
        self._handler_kwargs = handler_kwargs
        self._scheduler = sched.scheduler(time.time, time.sleep)

    def accept_connection(self, client):
        return self._handler_class(client, **self._handler_kwargs)

    def start(self):
        while True:
            self._scheduler.run()

    def add_periodic_callback(self, action, delay_msecs):
        delay = float(delay_msecs) / 1000
        callback = PeriodicCallback(self._scheduler, action, delay)
        callback.schedule()

    def client_subscribes_to(self, event_type):
        return True

class PeriodicCallback:
    def __init__(self, scheduler, action, delay):
        self.scheduler = scheduler
        self.action = action
        self.delay = delay

    def schedule(self):
        self.scheduler.enter(self.delay, 1, self._fire, [])

    def _fire(self):
        self.action()
        self.schedule()
