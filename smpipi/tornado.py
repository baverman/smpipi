from __future__ import absolute_import
import sys
import logging
import socket

from tornado.tcpserver import TCPServer
from tornado.iostream import IOStream, StreamClosedError
from tornado.ioloop import IOLoop
from tornado.gen import coroutine, sleep, Return
from tornado.concurrent import Future

from .proto import BaseConnection, BaseESME
from . import command


class DeliverMixin(object):
    def _deliver(self, req, resp):
        reply = self._make_reply(resp)
        future = self.on_deliver(req, resp, reply)
        self.ioloop.add_future(future, lambda _: reply.called or reply())


class ESME(DeliverMixin, BaseESME):
    def __init__(self, **kwargs):
        BaseESME.__init__(self, **kwargs)
        self.running = False
        self.closed = False

    @coroutine
    def connect(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.ioloop = IOLoop.current()
        self.stream = IOStream(s)
        yield self.stream.connect((host, port))

    def on_send(self, data):
        return self.stream.write(data)

    def on_close(self):
        self.closed = True
        self.stream.close()

    @coroutine
    def readloop(self, future):
        while not self.closed and (not future or not future.done()):
            try:
                data = yield self.stream.read_bytes(1024, partial=True)
            except StreamClosedError:  # pragma: no cover
                break
            else:
                self.feed(data)

    def wait_for(self, response):
        future = Future()
        response.callback = lambda resp: future.set_result(resp.response)
        if self.running:
            return future
        else:
            return self.run(future)

    @coroutine
    def run(self, future=None):
        self.running = True
        try:
            yield self.readloop(future)
        finally:
            self.running = False

        if future and future.done():
            raise Return(future.result())


class Server(TCPServer):  # pragma: no cover
    def __init__(self, ioloop, stream_handler):
        TCPServer.__init__(self, ioloop)
        self.stream_handler = stream_handler

    @coroutine
    def handle_stream(self, stream, address):
        logging.debug('New connection from %s', address)
        handler = self.stream_handler(stream)
        yield handler.run()
        logging.debug('Connection from %s closed', address)


class TestSMSC(DeliverMixin, BaseConnection):  # pragma: no cover
    def __init__(self, stream, **kwargs):
        BaseConnection.__init__(self, **kwargs)
        self.stream = stream
        self.close = False
        self.sleep = False
        self.ioloop = IOLoop.current()

    @coroutine
    def on_deliver(self, request, response, reply):
        reply()
        if isinstance(request, command.SubmitSM):
            if request.short_message.startswith(b'deliver '):
                message = request.short_message.partition(b' ')[2].strip()
                self.send(command.DeliverSM(short_message=message))
            if request.short_message == b'close':
                self.send(command.Unbind())
            if request.short_message == b'disconnect':
                self.close = True
            if request.short_message == b'sleep':
                self.sleep = True

    def on_send(self, data):
        self.stream.write(data)

    @coroutine
    def run(self):
        while not self.close:
            if self.sleep:
                self.sleep = False
                yield sleep(2)

            try:
                data = yield self.stream.read_bytes(1024, partial=True)
            except StreamClosedError:
                break
            else:
                self.feed(data)

        self.stream.close()


if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level='DEBUG')
    ioloop = IOLoop.instance()
    handler = lambda stream: TestSMSC(stream,
                                      logger=logging.getLogger('test.server'))
    server = Server(ioloop, handler)
    server.listen(int(sys.argv[1]))
    ioloop.start()
