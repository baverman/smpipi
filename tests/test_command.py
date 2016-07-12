from binascii import unhexlify
from smpipi.command import Command, EnquireLink, SubmitSM
from smpipi import tlv


def test_simple_command_decode():
    payload = unhexlify(
        '0000006b0000000500000000024a3a40555353445f000101373'
        '730373436313635363400010132303100000000000000000000'
        '000381001201010634303137373030323730373833333402030'
        '002a02a1383000200000202000ca03737303730313030303033'
        '0501000101'
    )

    result = Command.decode(payload)
    assert result


def test_simple_encode():
    payload = EnquireLink().encode()
    result = Command.decode(payload)
    assert result == {'command_status': 0,
                      'command_length': 16,
                      'sequence_number': 0,
                      'command_id': 21}


def test_tlv_encode():
    cmd = SubmitSM(its_session_info='boo', ussd_service_op='16',
                   dest_addr_subunit='1', alert_on_message_delivery=True)
    cmd = Command.decode(cmd.encode())

    assert cmd.its_session_info == b'boo'
    assert cmd.ussd_service_op == b'16'
    assert cmd.dest_addr_subunit == 1
    assert cmd.alert_on_message_delivery == ''


def test_unknown_tlv():
    data = tlv.encode({'dest_addr_subunit': '1'})
    data = b'\x42\x42' + data[2:]
    result, _ = tlv.decode(data, 0)
    assert result == {'_tag_0x4242': b'\x01'}


def test_size_field_encode():
    cmd = SubmitSM(short_message='boo')
    cmd = Command.decode(cmd.encode())
    assert cmd.sm_length == 3
    assert cmd.short_message == b'boo'
