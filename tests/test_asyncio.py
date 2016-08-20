from asyncio import coroutine, get_event_loop

from smpipi.asyncio import ESME


def async_run(func):
    ioloop = get_event_loop()
    work = coroutine(func)
    ioloop.run_until_complete(work())


def test_bind(smsc):
    @async_run
    def work():
        esme = ESME()
        yield from esme.connect('127.0.0.1', 30001)
        resp = yield from esme.wait_for(esme.bind_transceiver('boo', 'foo'))
        assert resp.command_status == 0
        esme.send_message(short_message='close')
        yield from esme.run()


def test_delivery(smsc):
    @async_run
    def work():
        @coroutine
        def deliver(request, response, reply):
            assert request.short_message == b'foo'
            reply()
            resp = yield from esme.wait_for(esme.send_message(short_message='close'))
            assert resp.command_status == 0

        esme = ESME()
        esme.on_deliver = deliver
        yield from esme.connect('127.0.0.1', 30001)
        esme.send_message(short_message='deliver foo')
        yield from esme.run()


def test_broken_wait(smsc):
    @async_run
    def work():
        esme = ESME()
        yield from esme.connect('127.0.0.1', 30001)
        yield from esme.wait_for(esme.send_message(short_message='disconnect'))

        resp = esme.send_message(short_message='boo')
        yield from esme.wait_for(resp)
        assert not resp.ready
