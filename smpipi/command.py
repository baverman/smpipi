from .pdu import (Packet, NString, int8, Field, VarField,
                  decode_tlv, int32, AttrDict)

commands = {}


class CommandMeta(type):
    def __init__(cls, name, bases, fields):
        if hasattr(cls, 'command_id'):
            commands[cls.command_id] = cls


def command_from_data(data):
    return commands[data.command_id]


class Command(CommandMeta('CommandBase', (AttrDict,), {})):
    def __init__(self, **kwargs):
        self.update(kwargs)
        self['command_id'] = self.command_id

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, dict(self))

    @staticmethod
    def decode(buf):
        size = len(buf)
        result, offset = Header.decode(buf, 0)
        cmd = command_from_data(result)
        if offset < size and hasattr(cmd, 'body'):
            body, offset = cmd.body.decode(buf, offset)
            result.update(body)

            while offset < size:
                tag, value, offset = decode_tlv(buf, offset)
                result['_tag_{}'.format(tag)] = value

        return cmd(**result)

    def encode(self):
        body = ''
        cmd = self.__class__
        if hasattr(cmd, 'body'):
            body = cmd.body.encode(self)

        self['command_length'] = 16 + len(body)
        header = Header.encode(self)
        return header + body


class Header(Packet):
    command_length = Field(int32)
    command_id = Field(int32)
    command_status = Field(int32)
    sequence_number = Field(int32)


class Bind(Packet):
    system_id = Field(NString(max=16))
    password = Field(NString(max=9))
    system_type = Field(NString(max=13))
    interface_version = Field(int8)
    addr_ton = Field(int8)
    addr_npi = Field(int8)
    address_range = Field(NString(max=41))


class BindResp(Packet):
    system_id = Field(NString(max=16))


class Submit(Packet):
    service_type = Field(NString(max=6))
    source_addr_ton = Field(int8)
    source_addr_npi = Field(int8)
    source_addr = Field(NString(max=21))
    dest_addr_ton = Field(int8)
    dest_addr_npi = Field(int8)
    destination_addr = Field(NString(max=21))
    ecm_class = Field(int8)
    protocol_id = Field(int8)
    priority_flag = Field(int8)
    schedule_delivery_time = Field(NString(max=17))
    validity_period = Field(NString(max=17))
    registered_delivery = Field(int8)
    replace_if_present_flag = Field(int8)
    data_coding = Field(int8)
    sm_default_msg_id = Field(int8)
    sm_length = Field(int8)
    short_message = VarField('sm_length', max=254)


class SubmitResp(Packet):
    message_id = Field(NString(max=65))


class GenericNack(Command):
    command_id = 0x80000000


class BindReceiver(Command):
    command_id = 0x00000001
    body = Bind


class BindReceiverResp(Command):
    command_id = 0x80000001
    body = BindResp


class BindTransmitter(Command):
    command_id = 0x00000002
    body = Bind


class BindTransmitterResp(Command):
    command_id = 0x80000002
    body = BindResp


class QuerySM(Command):
    command_id = 0x00000003
    class body(Packet):
        pass


class QuerySMResp(Command):
    command_id = 0x80000003
    class body(Packet):
        pass


class SubmitSM(Command):
    command_id = 0x00000004
    body = Submit


class SubmitSMResp(Command):
    command_id = 0x80000004
    body = SubmitResp


class DeliverSM(Command):
    command_id = 0x00000005
    body = Submit


class DeliverSMResp(Command):
    command_id = 0x80000005
    body = SubmitResp


class Unbind(Command):
    command_id = 0x00000006


class UnbindResp(Command):
    command_id = 0x80000006


class BindTransceiver(Command):
    command_id = 0x00000009
    body = Bind


class BindTransceiverResp(Command):
    command_id = 0x80000009
    body = BindResp


class EnquireLink(Command):
    command_id = 0x00000015


class EnquireLinkResp(Command):
    command_id = 0x80000015
