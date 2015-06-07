import liblo
import cPickle
import threading
import traceback_printer
import time

class OscReceiver(liblo.Server):
    def __init__(self, port=None, log_source=None, log_target=None, proto=liblo.UDP, name=None):
        if name:
            self._name = name
        else:
            self._name = self.__class__.__name__

        liblo.Server.__init__(self, port, proto)
        self._running = False
        self._freed = False
        self._queue = []
        self._lock = threading.Lock()

        if log_source:
            self._read_log(log_source)
            self._reading_from_log = True
            self._last_log_time = None
            self._sender = liblo.Address("localhost", self.port, liblo.UDP)
        else:
            self._reading_from_log = False

        if log_target:
            self._writing_to_log = True
            self._log_target_file = open(log_target, "w")
            self._log_start_time = None
        else:
            self._writing_to_log = False

    def add_method(self, path, typespec, callback_func, user_data=None):
        liblo.Server.add_method(self, path, typespec, self._callback,
                                (callback_func, user_data))

    def _callback(self, path, args, types, src, (callback_func, user_data)):
        if self._writing_to_log:
            self._write_to_log(path, args)
        with self._lock:
            self._queue.append((path, args, types, src, callback_func, user_data))

    def _write_to_log(self, path, args):
        if self._log_start_time is None:
            self._log_start_time = time.time()
        t = time.time() - self._log_start_time
        self._log_target_file.write(cPickle.dumps((t, path, args)))

    def start(self):
        if self._freed:
            raise Exception("Cannot call OscReceiver.start a second time. You need to create a new OscReceiver instance.")
        self._running = True
        serve_thread = threading.Thread(name="%s.server_thread" % self._name,
                                        target=self._serve_loop)
        serve_thread.daemon = True
        serve_thread.start()

        if self._reading_from_log:
            send_thread = threading.Thread(name="%s.send_thread" % self._name,
                                           target=self._send_from_log)
            send_thread.daemon = True
            send_thread.start()

    def _serve_loop(self):
        while self._running:
            self.recv()
            self._serve_from_queue()
            time.sleep(0.001)
        self.free()
        self._freed = True

    def _serve_from_queue(self):
        with self._lock:
            for path, args, types, src, callback_func, user_data in self._queue:
                self._fire_callback_with_exception_handler(
                    path, args, types, src, callback_func, user_data)
            self._queue = []

    def _read_log(self, filename):
        print "reading log file %s..." % filename
        f = open(filename, "r")
        self._log_entries = []
        try:
            while True:
                entry = cPickle.load(f)
                self._log_entries.append(entry)
        except EOFError:
            pass
        f.close()
        print "ok"

    def _send_from_log(self):
        while True:
            if len(self._log_entries) == 0:
                print "finished processing log"
                return
            (t, path, args) = self._log_entries.pop(0)
            if self._last_log_time is not None:
                time.sleep(t - self._last_log_time)
            liblo.send(self._sender, path, *args)
            self._last_log_time = t

    def _fire_callback_with_exception_handler(self, path, args, types, src, callback, user_data):
        try:
            callback(path, args, types, src, user_data)
        except Exception as err:
            traceback_printer.print_traceback()
            raise err

    def stop(self):
        self._running = False
