import time
import pytest

from smpipi import command
from smpipi.proto import Proto, BaseESME, BrokenLink


def test_simple_receive():
    proto = Proto()
    data = proto.send_bytes(command.SubmitSM(short_message='boo'))
    cmd, = list(proto.receive_bytes(data))
    assert cmd.short_message == b'boo'


def test_chunked_receive():
    proto = Proto()
    data = proto.send_bytes(command.SubmitSM(short_message='boo'))
    assert not list(proto.receive_bytes(data[:3]))
    assert not list(proto.receive_bytes(data[3:10]))
    cmd, = list(proto.receive_bytes(data[10:]))
    assert cmd.short_message == b'boo'


def test_multiple_commands():
    proto = Proto()
    data = proto.send_bytes(command.SubmitSM(short_message='boo'),
                            command.SubmitSM(short_message='foo'))
    cmd1, cmd2 = list(proto.receive_bytes(data))
    assert cmd1.short_message == b'boo'
    assert cmd2.short_message == b'foo'


class TestESME(BaseESME):
    def __init__(self, *args, **kwargs):
        BaseESME.__init__(self, *args, **kwargs)
        self.commands_to_send = []
        self.delivered_commands = []

    def on_send(self, data):
        self.commands_to_send.append(command.Command.decode(data))

    def on_close(self):
        self.closed = True

    def on_deliver(self, request, response, reply):
        self.delivered_commands.append(request)

    def feed_cmd(self, *cmds):
        for cmd in cmds:
            self.feed(cmd.encode())


def test_bind():
    for cmd in ('bind_receiver', 'bind_transmitter', 'bind_transceiver'):
        esme = TestESME()
        resp = getattr(esme, cmd)('sys', 'pwd')
        esme.feed_cmd(command.BindReceiverResp(sequence_number=1))
        assert resp.ready
        assert resp.response.command_id == command.BindReceiverResp.command_id
        assert resp.request.sequence_number == resp.response.sequence_number

        req, = esme.commands_to_send
        assert req.system_id == b'sys'
        assert req.password == b'pwd'


def test_unbind_from_smsc():
    esme = TestESME()
    esme.feed_cmd(command.Unbind())

    req, = esme.commands_to_send
    assert req.command_id == command.UnbindResp.command_id
    assert esme.closed


def test_enquire_from_smsc():
    esme = TestESME()
    esme.feed_cmd(command.EnquireLink())

    req, = esme.commands_to_send
    assert req.command_id == command.EnquireLinkResp.command_id


def test_send_message():
    esme = TestESME()
    resp = esme.send_message(short_message='boo')
    esme.feed_cmd(command.SubmitSMResp(sequence_number=1))
    assert resp.response.command_id == command.SubmitSMResp.command_id
    req, = esme.commands_to_send
    assert req.short_message == b'boo'


def test_deliver():
    esme = TestESME()
    esme.feed_cmd(command.DeliverSM(sequence_number=42, short_message='boo'))

    resp, = esme.commands_to_send
    assert resp.command_id == command.DeliverSMResp.command_id
    assert resp.sequence_number == 42

    req, = esme.delivered_commands
    assert req.command_id == command.DeliverSM.command_id
    assert req.sequence_number == 42
    assert req.short_message == b'boo'


def test_deliver_with_post_handler():
    def on_deliver(req, resp, reply):
        reply()
        assert esme.commands_to_send[-1].command_id == command.DeliverSMResp.command_id

    esme = TestESME()
    esme.on_deliver = on_deliver
    esme.feed_cmd(command.DeliverSM(sequence_number=42, short_message='boo'))
    assert len(esme.commands_to_send) == 1


def test_ping():
    esme = TestESME(enquire_timeout=100)

    esme.ping()
    assert not esme.enquire_response

    # success ping
    now = time.time()
    esme.last_enquire = now - 101
    esme.ping(20)
    assert now + 19 < esme.enquire_response.expire < now + 21

    req, = esme.commands_to_send
    assert req.command_id == command.EnquireLink.command_id

    esme.feed_cmd(command.EnquireLinkResp(sequence_number=req.sequence_number))
    assert esme.enquire_response.ready
    esme.ping()
    assert not esme.enquire_response
    assert now -1 < esme.last_enquire < now + 1

    # failed ping
    esme.last_enquire = now - 100
    esme.ping()
    esme.enquire_response.expire = now
    with pytest.raises(BrokenLink):
        esme.ping()
