import logging
import socket

from . import command
from .packet import int32

pdu_log = logging.getLogger('smpipi.pdu')

class ESME(object):
    def __init__(self, host, port, timeout=10, handler=None):
        self.sequence_number = 0
        self._socket = socket.create_connection((host, port), timeout=timeout)
        self.handler = handler

    def next_sequence(self):
        self.sequence_number += 1
        return self.sequence_number

    def read(self):
        try:
            dlen = self._socket.recv(4)
        except socket.timeout:
            return

        if dlen:
            size, _ = int32.decode(dlen, 0)
            body = self._socket.recv(size - 4)
            pdu = dlen + body
            pdu_hex = pdu.encode('hex')
            try:
                cmd = command.Command.decode(pdu)
            except:
                pdu_log.debug('>> %s DecodeError', pdu_hex)
                raise
            else:
                pdu_log.debug('>> %s %r', pdu_hex, cmd)

            return cmd

    def handle(self, cmd):
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
            if self.handler:
                self.handler(cmd, resp)
            self.reply(resp)
        else:
            raise Exception('Unknown command: {}'.format(cmd))

    def listen(self):
        pdu = self.read()
        if pdu:
            self.handle(pdu)

    def send(self, cmd):
        cmd.sequence_number = self.next_sequence()
        self.reply(cmd)
        return self.read()

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
