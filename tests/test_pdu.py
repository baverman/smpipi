from smpipi.pdu import NString, int8, int16, int32, String


def test_nstring():
    buf = '123\x003456\x00'
    result, offset = NString(max=4).decode(buf, 0)
    assert result == '123'

    result, offset = NString(max=5).decode(buf, offset)
    assert result == '3456'
    assert offset == 9

    assert NString(max=10).encode('boo') == 'boo\x00'


def test_string():
    buf = '1233456'
    result, offset = String(3).decode(buf, 0)
    assert result == '123'

    result, offset = String(4).decode(buf, offset)
    assert result == '3456'
    assert offset == 7


def test_integer():
    buf = int8.encode(100) + int16.encode(16300) + int32.encode(666666)
    assert len(buf) == 7

    result, offset = int8.decode(buf, 0)
    assert result == 100

    result, offset = int16.decode(buf, offset)
    assert result == 16300

    result, offset = int32.decode(buf, offset)
    assert result == 666666
