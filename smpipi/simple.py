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

    def wait_for(self, response, timeout):
        oldtimeout = self._socket.gettimeout()
        self.set_timeout(timeout)
        expire = time.time() + timeout
        while not response.ready and expire > time.time():
            try:
                data = self._socket.recv(1024)
            except socket.timeout:
                raise Timeout()
            except IOError:  # pragma: no cover
                raise Timeout()
            else:
                if data:
                    self.feed(data)
                else:
                    break
            finally:
                try:
                    self.set_timeout(oldtimeout)
                except:  # pragma: no cover
                    pass

        if not response.ready:
            raise Timeout()

    def read(self):
        if self.closed:
            return False

        try:
            data = self._socket.recv(1024)
        except socket.timeout:  # pragma: no cover
            pass
        except IOError:  # pragma: no cover
            return False
        else:
            if data:
                self.feed(data)
            else:
                return False

        return True

    def close(self):
        resp = self.unbind()
        try:
            self.wait_for(resp, 1)
        except Timeout:
            self.on_close()

    def listen(self):
        while self.read():
            pass
