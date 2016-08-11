import pytest

from smpipi.simple import ESME, Timeout


def test_bind(smsc):
    esme = ESME('127.0.0.1', 30001)
    resp = esme.wait_for(esme.bind_transceiver('system', 'password'), 10)
    assert resp.command_status == 0


def test_on_close(smsc):
    esme = ESME('127.0.0.1', 30001)
    esme.send_message(short_message='close')
    esme.listen()
    assert esme.closed


def test_close(smsc):
    esme = ESME('127.0.0.1', 30001)
    esme.close()
    assert esme.closed


def test_broken_wait(smsc):
    esme = ESME('127.0.0.1', 30001)
    esme.wait_for(esme.send_message(short_message='disconnect'), 10)

    resp = esme.send_message(short_message='boo')
    with pytest.raises(Timeout):
        esme.wait_for(resp, 1)
    assert not resp.ready


def test_broken_read(smsc):
    esme = ESME('127.0.0.1', 30001)
    esme.wait_for(esme.send_message(short_message='disconnect'), 10)

    esme.set_timeout(1)
    result = esme.read()
    assert not result


def test_broken_close(smsc):
    esme = ESME('127.0.0.1', 30001)
    esme.wait_for(esme.send_message(short_message='disconnect'), 10)

    esme.close()
    assert esme.closed


def test_timeout(smsc):
    esme = ESME('127.0.0.1', 30001)
    esme.wait_for(esme.send_message(short_message='sleep'), 10)

    resp = esme.send_message(short_message='sleep')
    with pytest.raises(Timeout):
        esme.wait_for(resp, 1)
    assert not resp.ready
