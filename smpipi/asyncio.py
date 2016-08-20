import asyncio

from .proto import BaseESME


class ESME(BaseESME):
    def __init__(self, **kwargs):
        BaseESME.__init__(self, **kwargs)
        self.closed = False
        self.running = False

    @asyncio.coroutine
    def connect(self, host, port):
        self.reader, self.writer = yield from asyncio.open_connection(host, port)

    def on_send(self, data):
        self.writer.write(data)

    def on_close(self):
        self.closed = True
        self.writer.close()

    def _deliver(self, req, resp):
        reply = self._make_reply(resp)
        future = asyncio.ensure_future(self.on_deliver(req, resp, reply))
        future.add_done_callback(lambda _: reply.called or reply())

    def wait_for(self, response):
        if self.running:
            future = asyncio.Future()
            response.callback = lambda resp: future.set_result(resp.response)
            return future
        else:
            return self.run(response)

    @asyncio.coroutine
    def run(self, response=None):
        self.running = True
        try:
            while not self.closed and (not response or not response.ready):
                data = yield from self.reader.read(1024)
                if not data:
                    break
                self.feed(data)
        finally:
            self.running = False

        if response and response.ready:
            return response.response
