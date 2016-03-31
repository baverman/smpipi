from struct import Struct
from .packet import int8, int16, int32

tlv_struct = Struct('!HH')

INT_TYPES = {
    1: int8,
    2: int16,
    3: int32
}


class IntField(object):
    def __init__(self, name, size):
        self.name = name
        self.size = size

    def decode(self, size, value):
        return INT_TYPES[size].decode(value, 0)[0]

    def encode(self, value):
        return INT_TYPES[self.size].encode(value)


class StrField(object):
    def __init__(self, name):
        self.name = name

    def decode(self, size, value):
        return value

    def encode(self, value):
        return str(value)


class EmptyField(object):
    def __init__(self, name):
        self.name = name

    def decode(self, size, value):
        return ''

    def encode(self, value):
        return ''


NStrField = StrField


tags = {
    0x0005: IntField('dest_addr_subunit', 1),
    0x0006: IntField('dest_network_type', 1),
    0x0007: IntField('dest_bearer_type', 1),
    0x0008: IntField('dest_telematics_id', 2),
    0x000D: IntField('source_addr_subunit', 1),
    0x000E: IntField('source_network_type', 1),
    0x000F: IntField('source_bearer_type', 1),
    0x0010: IntField('source_telematics_id', 1),
    0x0017: IntField('qos_time_to_live', 4),
    0x0019: IntField('payload_type', 1),
    0x001D: NStrField('additional_status_info_text'),
    0x001E: NStrField('receipted_message_id'),
    0x0030: IntField('ms_msg_wait_facilities', 1),
    0x0201: IntField('privacy_indicator', 1),
    0x0202: StrField('source_subaddress'),
    0x0203: StrField('dest_subaddress'),
    0x0204: IntField('user_message_reference', 2),
    0x0205: IntField('user_response_code', 1),
    0x020A: IntField('source_port', 2),
    0x020B: IntField('destination_port', 2),
    0x020C: IntField('sar_msg_ref_num', 2),
    0x020D: IntField('language_indicator', 1),
    0x020E: IntField('sar_total_segments', 1),
    0x020F: IntField('sar_segment_seqnum', 1),
    0x0210: IntField('sc_interface_version', 1),
    0x0302: IntField('callback_num_pres_ind', 1),
    0x0303: StrField('callback_num_atag'),
    0x0304: IntField('number_of_messages', 1),
    0x0381: StrField('callback_num'),
    0x0420: IntField('dpf_result', 1),
    0x0421: IntField('set_dpf', 1),
    0x0422: IntField('ms_availability_status', 1),
    0x0423: StrField('network_error_code'),
    0x0424: StrField('message_payload'),
    0x0425: IntField('delivery_failure_reason', 1),
    0x0426: IntField('more_messages_to_send', 1),
    0x0427: IntField('message_state', 1),
    0x0501: StrField('ussd_service_op'),
    0x1201: IntField('display_time', 1),
    0x1203: IntField('sms_signal', 1),
    0x1204: IntField('ms_validity', 1),
    0x130C: EmptyField('alert_on_message_delivery'),
    0x1380: IntField('its_reply_type', 1),
    0x1383: StrField('its_session_info'),
}

names = {field.name: (tag, field) for tag, field in tags.items()}


def decode(buf, offset):
    bufsize = len(buf)
    result = {}
    while offset < bufsize:
        tag, size = tlv_struct.unpack_from(buf, offset)
        offset += tlv_struct.size
        value = buf[offset:offset + size]
        offset += size

        field = tags.get(tag)
        if field:
            value = field.decode(size, value)
            name = field.name
        else:
            name = '_tag_{}'.format(hex(tag))

        result[name] = value

    return result, offset


def encode(data):
    result = ''
    for k, v in data.items():
        if k in names:
            tag, field = names[k]
            value = field.encode(v)
            size = len(value)
            result += tlv_struct.pack(tag, size) + value

    return result
