import logging
import socket
import time

from . import command
from .packet import int32

pdu_log = logging.getLogger('smpipi.pdu')


class UnknownCommand(Exception):
    pass


class BrokenLink(Exception):
    pass


class ESME(object):
    def __init__(self, host, port, timeout=60, handler=None,
                 enquire_timeout=300, conn_timeout=10,
                 post_handler=None, connection=None):
        self.sequence_number = 0
        if connection:
            self._socket = connection
        else:  # pragma: no cover
            self._socket = socket.create_connection((host, port), timeout=conn_timeout)
            self._socket.settimeout(timeout)
        self.handler = handler
        self.post_handler = post_handler
        self.enquire_timeout = 300
        self.last_enquire = time.time()

    def next_sequence(self):
        self.sequence_number += 1
        return self.sequence_number

    def read(self):
        try:
            dlen = self._socket.recv(4)
        except socket.timeout:  # pragma: no cover
            return

        if dlen:
            size, _ = int32.decode(dlen, 0)
            body = self._socket.recv(size - 4)
            pdu = dlen + body
            pdu_hex = pdu.encode('hex')
            try:
                cmd = command.Command.decode(pdu)
            except:  # pragma: no cover
                pdu_log.debug('>> %s DecodeError', pdu_hex)
                raise
            else:
                pdu_log.debug('>> %s %r', pdu_hex, cmd)

            return cmd

    def handle(self, cmd):
        self.last_enquire = time.time()
        cmd_type = type(cmd)
        seq = {'sequence_number': cmd.sequence_number}
        if cmd_type is command.EnquireLink:
            self.reply(command.EnquireLinkResp(**seq))
        elif cmd_type is command.Unbind:
            self.reply(command.UnbindResp(**seq))
            self.close(False)
            raise StopIteration()
        elif cmd_type is command.DeliverSM:
            resp = command.DeliverSMResp(**seq)
            result = self.handler and self.handler(cmd, resp)
            self.reply(resp)
            if self.post_handler:
                self.post_handler(result)
        elif cmd_type is command.SubmitSMResp:
            pass
        else:
            raise UnknownCommand(repr(cmd))

    def listen(self):
        pdu = self.read()
        if pdu:
            self.handle(pdu)
        else:
            if self.last_enquire + self.enquire_timeout < time.time():
                pdu = self.send(command.EnquireLink())
                if pdu:
                    self.last_enquire = time.time()
                    if type(pdu) is not command.EnquireLinkResp:
                        self.handle(pdu)
                else:
                    raise BrokenLink('SMPP link broken: no response from SMSC')

    def send(self, cmd):
        self.send_async(cmd)
        return self.read()

    def send_async(self, cmd):
        cmd.sequence_number = self.next_sequence()
        self.reply(cmd)
        return cmd.sequence_number

    def send_message(self, **kwargs):
        return self.send(command.SubmitSM(**kwargs))

    def reply(self, cmd):
        payload = cmd.encode()
        pdu_log.debug('<< %s %r', payload.encode('hex'), cmd)
        self._socket.sendall(payload)

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

    def unbind(self):
        return self.send(command.Unbind())

    def close(self, unbind=True):
        if unbind:
            self.unbind()
        self._socket.close()
