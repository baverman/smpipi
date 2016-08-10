import time
import logging

from binascii import hexlify
from collections import deque
from weakref import WeakValueDictionary

from . import command
from .packet import int32

pdu_log = logging.getLogger('smpipi.pdu')


class BrokenLink(Exception):
    pass


class Proto(object):
    def __init__(self):
        self.buffer = b''

    def receive_bytes(self, data):
        self.buffer += data

        while len(self.buffer) >= 4:
            size, _ = int32.decode(self.buffer, 0)
            if len(self.buffer) < size:
                break
            pdu = self.buffer[:size]
            self.buffer = self.buffer[size:]
            pdu_hex = hexlify(pdu)
            try:
                cmd = command.Command.decode(pdu)
            except:  # pragma: no cover
                pdu_log.debug('>> %s DecodeError', pdu_hex)
                raise
            else:
                pdu_log.debug('>> %s %r', pdu_hex, cmd)
                yield cmd

    def send_bytes(self, *events):
        result = []
        for pdu in events:
            payload = pdu.encode()
            result.append(payload)
            pdu_log.debug('<< %s %r', hexlify(payload), pdu)

        return b''.join(result)


class Response(object):
    def __init__(self, request, callback):
        self.request = request
        self.callback = callback
        self.ready = False

    def resolve(self, response):
        self.ready = True
        self.response = response
        if self.callback:
            self.callback(self)


class BaseConnection(object):
    def __init__(self, response_queue_size=None, enquire_timeout=None):
        self.proto = Proto()
        self.sequence_number = 0

        self.last_enquire = time.time()
        self.enquire_timeout = enquire_timeout or 300
        self.enquire_response = None

        self.response_queue = deque([], response_queue_size or 1000)
        self.response_map = WeakValueDictionary()

    def next_sequence(self):
        self.sequence_number += 1
        return self.sequence_number

    def reply(self, cmd):
        self.on_send(self.proto.send_bytes(cmd))

    def send(self, cmd, callback=None, notify=True):
        cmd.sequence_number = self.next_sequence()
        resp = Response(cmd, callback)
        if notify:
            self.response_map[cmd.sequence_number] = resp
            self.response_queue.append(resp)
        self.reply(cmd)
        return resp

    def on_send(self, data):  # pragma: no cover
        pass

    def on_close(self):  # pragma: no cover
        pass

    def on_deliver(self, req, resp):  # pragma: no cover
        pass

    def handle(self, cmd):
        self.last_enquire = time.time()
        cmd_type = type(cmd)
        seq = {'sequence_number': cmd.sequence_number}
        if cmd_type is command.EnquireLink:
            self.reply(command.EnquireLinkResp(**seq))
        elif cmd_type is command.Unbind:
            self.reply(command.UnbindResp(**seq))
            self.on_close()
        elif cmd_type.is_response:
            resp = self.response_map.pop(cmd.sequence_number, None)
            if resp:
                resp.resolve(cmd)
        else:
            resp = cmd_type.response(**seq)
            post = self.on_deliver(cmd, resp)
            self.reply(resp)
            if post:
                post()

    def feed(self, data):
        for e in self.proto.receive_bytes(data):
            self.handle(e)

    def ping(self, response_timeout=10):
        now = time.time()
        if self.enquire_response:
            if self.enquire_response.ready:
                self.enquire_response = None
            elif self.enquire_response.expire < now:
                raise BrokenLink('SMPP link broken: no response from SMSC')
        elif self.last_enquire + self.enquire_timeout < now:
            self.enquire_response = self.send(command.EnquireLink())
            self.enquire_response.expire = now + response_timeout

    def unbind(self):
        return self.send(command.Unbind(), lambda resp: self.on_close())


class BaseESME(BaseConnection):
    def bind_transceiver(self, system_id, password, interface_version=0x34, **kwargs):
        return self.send(command.BindTransceiver(system_id=system_id,
                                                 password=password,
                                                 interface_version=interface_version,
                                                 **kwargs))

    def bind_receiver(self, system_id, password, interface_version=0x34, **kwargs):
        return self.send(command.BindReceiver(system_id=system_id,
                                              password=password,
                                              interface_version=interface_version,
                                              **kwargs))

    def bind_transmitter(self, system_id, password, interface_version=0x34, **kwargs):
        return self.send(command.BindTransmitter(system_id=system_id,
                                                 password=password,
                                                 interface_version=interface_version,
                                                 **kwargs))
    def send_message(self, **kwargs):
        cb = kwargs.pop('callback', None)
        return self.send(command.SubmitSM(**kwargs), cb)
