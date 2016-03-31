import socket

from . import command
from .pdu import int32


class ESME(object):
    def __init__(self, host, port, timeout=10):
        self.sequence_number = 0
        self._socket = socket.create_connection((host, port), timeout=timeout)

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
            print '<<', (dlen + body).encode('hex')
            return command.Command.decode(dlen + body)

    def handle(self, cmd):
        if type(cmd) == command.EnquireLink:
            self.reply(command.EnquireLinkResp(sequence_number=cmd.sequence_number))

    def send(self, cmd):
        cmd.sequence_number = self.next_sequence()
        self.reply(cmd)
        return self.read()

    def send_message(self, **kwargs):
        return self.send(command.SubmitSM(**kwargs))

    def reply(self, cmd):
        payload = cmd.encode()
        print '>>', cmd.__class__.__name__, payload.encode('hex')
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

    def close(self):
        self.unbind()
        self._socket.close()
