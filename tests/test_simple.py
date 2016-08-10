import sys
import time
from subprocess import Popen

import pytest

from smpipi.simple import ESME, Timeout


@pytest.fixture(scope='module')
def smsc(request):
    p = Popen([sys.executable, '-m', 'smpipi.tornado', '30001'])
    time.sleep(5)
    request.addfinalizer(p.kill)


def test_bind(smsc):
    esme = ESME('127.0.0.1', 30001)
    resp = esme.bind_transceiver('system', 'password')
    esme.wait_for(resp, 10)
    assert resp.response.command_status == 0


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
    resp = esme.send_message(short_message='disconnect')
    esme.wait_for(resp, 10)

    resp = esme.send_message(short_message='boo')
    with pytest.raises(Timeout):
        esme.wait_for(resp, 1)
    assert not resp.ready


def test_broken_read(smsc):
    esme = ESME('127.0.0.1', 30001)
    resp = esme.send_message(short_message='disconnect')
    esme.wait_for(resp, 10)

    esme.set_timeout(1)
    result = esme.read()
    assert not result


def test_broken_close(smsc):
    esme = ESME('127.0.0.1', 30001)
    resp = esme.send_message(short_message='disconnect')
    esme.wait_for(resp, 10)

    esme.close()
    assert esme.closed


def test_timeout(smsc):
    esme = ESME('127.0.0.1', 30001)
    resp = esme.send_message(short_message='sleep')
    esme.wait_for(resp, 10)

    resp = esme.send_message(short_message='sleep')
    with pytest.raises(Timeout):
        esme.wait_for(resp, 1)
    assert not resp.ready
