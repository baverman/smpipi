from smpipi.packet import (NString, int8, int16, int32, String,
                           Packet, SizeField, Field, Array, DispatchField)


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
    result, offset = String(10).decode(buf, 0, 3)
    assert result == '123'

    result, offset = String(10).decode(buf, offset, 4)
    assert result == '3456'
    assert offset == 7


def test_integer():
    buf = int8.encode(100) + int16.encode(16300) + int32.encode(666666)
    assert len(buf) == 7

    result, offset = int8.decode(buf, 0)
    assert result == 100

    result, offset = int16.decode(buf, offset)
    assert result == 16300

    result, _ = int32.decode(buf, offset)
    assert result == 666666


def test_size_field():
    class Body(Packet):
        boo = SizeField(Field(int8, 'boo_len'), String(max=10))

    payload = Body.encode({'boo': 'bar'})
    data, _ = Body.decode(payload)
    assert data == {
        'boo': 'bar',
        'boo_len': 3
    }


def test_array():
    class Bar(Packet):
        bar = Field(int16)

    class Body(Packet):
        boo = SizeField(Field(int8, 'boo_len'), Array(Bar))

    payload = Body.encode({'boo': [{'bar': 10}, {'bar': 15}]})
    data, _ = Body.decode(payload)
    assert data == {
        'boo': [{'bar': 10}, {'bar': 15}],
        'boo_len': 2
    }


def test_dispatch():
    class Bar(Packet):
        bar = Field(int16)

    class Boo(Packet):
        boo = Field(NString(max=10))

    class Body(Packet):
        flag = DispatchField(int8, {
            1: Bar,
            2: Boo
        })

    payload = Body.encode({'flag': 1, 'bar': 10})
    data, _ = Body.decode(payload)
    assert data == {'flag': 1, 'bar': 10}

    payload = Body.encode({'flag': 2, 'boo': 'foobar'})
    data, _ = Body.decode(payload)
    assert data == {'flag': 2, 'boo': 'foobar'}
