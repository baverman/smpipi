from __future__ import absolute_import
import sys
import logging

from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError
from tornado.ioloop import IOLoop
from tornado.gen import coroutine, sleep

from .proto import BaseConnection
from . import command


class TestServer(TCPServer):  # pragma: no cover
    @coroutine
    def handle_stream(self, stream, address):
        logging.debug('New connection from %s', address)
        smsc = TestSMSC(stream)
        yield smsc.run()
        logging.debug('Connection from %s closed', address)


class TestSMSC(BaseConnection):  # pragma: no cover
    def __init__(self, stream, **kwargs):
        BaseConnection.__init__(self, **kwargs)
        self.stream = stream
        self.close = False
        self.sleep = False

    def on_deliver(self, request, response):
        if isinstance(request, command.SubmitSM):
            if request.short_message.startswith(b'deliver '):
                message = request.short_message.partition(' ')[2].strip()
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

        yield self.stream.close()


if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level='DEBUG')
    ioloop = IOLoop.instance()
    server = TestServer(ioloop)
    server.listen(int(sys.argv[1]))
    ioloop.start()
