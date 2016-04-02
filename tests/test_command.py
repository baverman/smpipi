from smpipi.command import Command, EnquireLink, SubmitSM


def test_simple_command_decode():
    payload = ('0000006b0000000500000000024a3a40555353445f000101373'
               '730373436313635363400010132303100000000000000000000'
               '000381001201010634303137373030323730373833333402030'
               '002a02a1383000200000202000ca03737303730313030303033'
               '0501000101').decode('hex')

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
    cmd = SubmitSM(its_session_info='boo', ussd_service_op='16')
    cmd = Command.decode(cmd.encode())

    assert cmd.its_session_info == 'boo'
    assert cmd.ussd_service_op == '16'


def test_size_field_encode():
    cmd = SubmitSM(short_message='boo')
    cmd = Command.decode(cmd.encode())
    assert cmd.sm_length == 3
    assert cmd.short_message == 'boo'
