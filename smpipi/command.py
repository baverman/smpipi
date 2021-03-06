from . import tlv
from .packet import (Packet, NString, int8, Field, Array, DispatchField,
                     SizeField, int32, AttrDict, String)

commands = {}


class CommandMeta(type):
    def __init__(cls, name, bases, fields):
        if hasattr(cls, 'command_id'):
            commands[cls.command_id] = cls


def command_from_data(data):
    return commands[data.command_id]


class Command(CommandMeta('CommandBase', (AttrDict,), {})):
    is_response = False
    def __init__(self, **kwargs):
        self.update(kwargs)
        self['command_id'] = self.command_id

    def __repr__(self):  # pragma: no cover
        return '{}({})'.format(self.__class__.__name__, dict(self))

    @staticmethod
    def decode(buf):
        size = len(buf)
        result, offset = Header.decode(buf, 0)
        cmd = command_from_data(result)
        if offset < size and hasattr(cmd, 'body'):
            body, offset = cmd.body.decode(buf, offset)
            result.update(body)

            opts, _ = tlv.decode(buf, offset)
            result.update(opts)

        return cmd(**result)

    def encode(self):
        body = b''
        cmd = self.__class__
        if hasattr(cmd, 'body'):
            body = cmd.body.encode(self)

        body += tlv.encode(self)

        self['command_length'] = 16 + len(body)
        header = Header.encode(self)
        return header + body


class CommandResp(Command):
    is_response = True


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
    esm_class = Field(int8)
    protocol_id = Field(int8)
    priority_flag = Field(int8)
    schedule_delivery_time = Field(NString(max=17))
    validity_period = Field(NString(max=17))
    registered_delivery = Field(int8)
    replace_if_present_flag = Field(int8)
    data_coding = Field(int8)
    sm_default_msg_id = Field(int8)
    short_message = SizeField(Field(int8, 'sm_length'), String(max=254))


class SubmitResp(Packet):
    message_id = Field(NString(max=65))


class GenericNack(Command):
    command_id = 0x80000000


class BindReceiverResp(CommandResp):
    command_id = 0x80000001
    body = BindResp


class BindReceiver(Command):
    response = BindReceiverResp
    command_id = 0x00000001
    body = Bind


class BindTransmitterResp(CommandResp):
    command_id = 0x80000002
    body = BindResp


class BindTransmitter(Command):
    response = BindTransmitterResp
    command_id = 0x00000002
    body = Bind


class QuerySMResp(CommandResp):
    command_id = 0x80000003
    class body(Packet):
        message_id = Field(NString(max=65))
        final_date = Field(NString(max=17))
        message_state = Field(int8)
        error_code = Field(int8)


class QuerySM(Command):
    response = QuerySMResp
    command_id = 0x00000003
    class body(Packet):
        message_id = Field(NString(max=65))
        source_addr_ton = Field(int8)
        source_addr_npi = Field(int8)
        source_addr = Field(NString(max=21))


class SubmitSMResp(CommandResp):
    command_id = 0x80000004
    body = SubmitResp


class SubmitSM(Command):
    response = SubmitSMResp
    command_id = 0x00000004
    body = Submit


class DeliverSMResp(CommandResp):
    command_id = 0x80000005
    body = SubmitResp


class DeliverSM(Command):
    response = DeliverSMResp
    command_id = 0x00000005
    body = Submit


class UnbindResp(CommandResp):
    command_id = 0x80000006


class Unbind(Command):
    response = UnbindResp
    command_id = 0x00000006


class ReplaceSMResp(CommandResp):
    command_id = 0x80000007


class ReplaceSM(Command):
    response = ReplaceSMResp
    command_id = 0x00000007
    class body(Packet):
        message_id = Field(NString(max=65))
        source_addr_ton = Field(int8)
        source_addr_npi = Field(int8)
        source_addr = Field(NString(max=21))
        schedule_delivery_time = Field(NString(max=17))
        validity_period = Field(NString(max=17))
        registered_delivery = Field(int8)
        sm_default_msg_id = Field(int8)
        short_message = SizeField(Field(int8, 'sm_length'), String(max=254))


class CancelSMResp(CommandResp):
    command_id = 0x80000008


class CancelSM(Command):
    response = CancelSMResp
    command_id = 0x00000008
    class body(Packet):
        service_type = Field(NString(max=6))
        message_id = Field(NString(max=65))
        source_addr_ton = Field(int8)
        source_addr_npi = Field(int8)
        source_addr = Field(NString(max=21))
        dest_addr_ton = Field(int8)
        dest_addr_npi = Field(int8)
        destination_addr = Field(NString(max=21))


class BindTransceiverResp(CommandResp):
    command_id = 0x80000009
    body = BindResp


class BindTransceiver(Command):
    response = BindTransceiverResp
    command_id = 0x00000009
    body = Bind


class Outbind(Command):
    command_id = 0x0000000B
    class body(Packet):
        system_id = Field(NString(max=16))
        password = Field(NString(max=9))


class EnquireLinkResp(CommandResp):
    command_id = 0x80000015


class EnquireLink(Command):
    response = EnquireLinkResp
    command_id = 0x00000015


class SubmitMultiResp(CommandResp):
    command_id = 0x80000021

    class body(Packet):
        class UnsuccessDelivery(Packet):
            dest_addr_ton = Field(int8)
            dest_addr_npi = Field(int8)
            destination_addr = Field(NString(max=21))
            error_status_code = Field(int32)

        message_id = Field(NString(max=65))
        unsuccess_sme = SizeField(Field(int8, 'no_unsuccess'),
                                  Array(UnsuccessDelivery))


class SubmitMulti(Command):
    response = SubmitMultiResp
    command_id = 0x00000021
    class body(Packet):
        class DestAddr(Packet):
            class SMEAddr(Packet):
                dest_addr_ton = Field(int8)
                dest_addr_npi = Field(int8)
                destination_addr = Field(NString(max=21))

            class DistributionList(Packet):
                dl_name = Field(NString(max=21))

            dest_flag = DispatchField(int8, {
                1: SMEAddr,
                2: DistributionList
            })

        service_type = Field(NString(max=6))
        source_addr_ton = Field(int8)
        source_addr_npi = Field(int8)
        source_addr = Field(NString(max=21))
        dest_address = SizeField(Field(int8, 'number_of_dests'),
                                 Array(DestAddr))
        esm_class = Field(int8)
        protocol_id = Field(int8)
        priority_flag = Field(int8)
        schedule_delivery_time = Field(NString(max=17))
        validity_period = Field(NString(max=17))
        registered_delivery = Field(int8)
        replace_if_present_flag = Field(int8)
        data_coding = Field(int8)
        sm_default_msg_id = Field(int8)
        short_message = SizeField(Field(int8, 'sm_length'), String(max=254))


class DataSMResp(CommandResp):
    command_id = 0x80000103
    body = SubmitResp


class DataSM(Command):
    response = DataSMResp
    command_id = 0x00000103
    class body(Packet):
        service_type = Field(NString(max=6))
        source_addr_ton = Field(int8)
        source_addr_npi = Field(int8)
        source_addr = Field(NString(max=65))
        dest_addr_ton = Field(int8)
        dest_addr_npi = Field(int8)
        destination_addr = Field(NString(max=65))
        esm_class = Field(int8)
        registered_delivery = Field(int8)
        data_coding = Field(int8)
