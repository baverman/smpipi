import time
import socket
from .proto import BaseESME


class Timeout(Exception):
    pass


class ESME(BaseESME):
    def __init__(self, host, port, timeout=60, conn_timeout=10, **kwargs):
        BaseESME.__init__(self, **kwargs)
        self._socket = socket.create_connection((host, port), timeout=conn_timeout)
        self.set_timeout(timeout)
        self.closed = False

    def set_timeout(self, timeout):
        self._socket.settimeout(timeout)

    def on_send(self, data):
        self._socket.sendall(data)

    def on_close(self):
        self.closed = True
        self._socket.close()

    def wait_for(self, response, timeout=None):
        timeout and self.set_timeout(timeout)
        expire = time.time() + self._socket.gettimeout()
        while not response.ready and expire > time.time():
            if not self.read(False):
                break

        if not response.ready:
            raise Timeout()

    def read(self, timeout_result=True):
        if self.closed:
            return False

        try:
            data = self._socket.recv(1024)
        except socket.timeout:
            return timeout_result
        except IOError:  # pragma: no cover
            return False

        if not data:
            return False

        self.feed(data)
        return True

    def close(self):
        resp = self.unbind()
        try:
            self.wait_for(resp)
        except Timeout:
            self.on_close()

    def listen(self, timeout=None):
        timeout and self.set_timeout(timeout)
        while self.read():
            pass
