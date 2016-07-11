import pytest
from StringIO import StringIO

from smpipi import command
from smpipi.esme import ESME, UnknownCommand, BrokenLink
from smpipi.packet import AttrDict


class DummySocket(object):
    def __init__(self, *packets):
        self.packets = list(packets)
        self.rdata = StringIO('')
        self.input = []
        self.closed = False

    def recv(self, size):
        data = self.rdata.read(size)
        if not data:
            newdata = self.packets.pop(0)
            if isinstance(newdata, command.Command):
                newdata = newdata.encode()
            self.rdata = StringIO(newdata)
            data = self.rdata.read(size)
        return data

    def sendall(self, data):
        self.input.append(data)

    def close(self):
        self.closed = True


def test_bind():
    for cmd in ('bind_receiver', 'bind_transmitter', 'bind_transceiver'):
        esme = ESME(None, None, connection=DummySocket(command.BindReceiverResp(), command.UnbindResp()))
        resp = getattr(esme, cmd)('sys', 'pwd')
        assert resp.command_id == command.BindReceiverResp.command_id
        req = command.Command.decode(esme._socket.input[0])
        assert req.system_id == 'sys'
        assert req.password == 'pwd'
        esme.close()
        assert esme._socket.closed


def test_send_message():
    esme = ESME(None, None, connection=DummySocket(command.SubmitSMResp()))
    resp = esme.send_message(short_message='boo')
    assert resp.command_id == command.SubmitSMResp.command_id
    req = command.Command.decode(esme._socket.input[0])
    assert req.short_message == 'boo'


def test_listen_session():
    def handler(req, res):
        res.command_status = 1
        handler.count += 1
        return 'boo'
    handler.count = 0

    def post_handler(result):
        post_handler.called = True
        assert result == 'boo'

    packets = [
        command.EnquireLink(),
        command.SubmitSMResp(),
        command.DeliverSM(short_message='foo'),
        command.Unbind(),
    ]

    esme = ESME(None, None, handler=handler, post_handler=post_handler,
                connection=DummySocket(*packets))

    esme.listen()
    reply = command.Command.decode(esme._socket.input[0])
    assert type(reply) is command.EnquireLinkResp

    esme.listen()  # submit resp

    esme.listen()
    reply = command.Command.decode(esme._socket.input[1])
    assert type(reply) is command.DeliverSMResp
    assert reply.command_status == 1

    with pytest.raises(StopIteration):
        esme.listen()
    reply = command.Command.decode(esme._socket.input[2])
    assert type(reply) is command.UnbindResp
    assert esme._socket.closed

    assert len(esme._socket.input) == 3
    assert handler.count == 1
    assert post_handler.called


def test_unknown_command():
    esme = ESME(None, None, connection=True)
    with pytest.raises(UnknownCommand):
        esme.handle(AttrDict(sequence_number=1))


def test_empty_read():
    esme = ESME(None, None, connection=DummySocket('', command.EnquireLinkResp(),
                                                   '', '',
                                                   '', command.SubmitSMResp()))

    esme.last_enquire = 0
    esme.listen()
    assert esme.last_enquire

    esme.last_enquire = 0
    with pytest.raises(BrokenLink):
        esme.listen()
    assert not esme.last_enquire

    esme.listen()
    assert esme.last_enquire
