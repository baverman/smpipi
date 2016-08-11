from tornado.gen import coroutine
from tornado.ioloop import IOLoop

from smpipi.tornado import ESME


def async_run(func):
    ioloop = IOLoop()
    ioloop.make_current()
    work = coroutine(func)
    ioloop.run_sync(work, timeout=5)


def test_bind(smsc):
    @async_run
    def work():
        esme = ESME()
        yield esme.connect('127.0.0.1', 30001)
        resp = yield esme.wait_for(esme.bind_transceiver('boo', 'foo'))
        assert resp.command_status == 0
        esme.send_message(short_message='close')
        yield esme.run()



def test_delivery(smsc):
    @async_run
    def work():
        @coroutine
        def deliver(request, response, reply):
            assert request.short_message == b'foo'
            reply()
            resp = yield esme.wait_for(esme.send_message(short_message='close'))
            assert resp.command_status == 0

        esme = ESME()
        esme.on_deliver = deliver
        yield esme.connect('127.0.0.1', 30001)
        esme.send_message(short_message='deliver foo')
        yield esme.run()
