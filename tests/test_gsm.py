# -*- coding: utf-8 -*-
import pytest
from smpipi import gsm


def test_latin_encode():
    assert gsm.encode(u'boo') == (b'boo', 0)


def test_cyrillic_encode():
    assert gsm.encode(u'Бу') == (b'\x04\x11\x04C', 8)


def test_extended_encode():
    assert gsm.encode(u'boo^') == (b'boo\x1b\x14', 0)


def test_latin_parts():
    parts, encoding, cls = gsm.make_parts(u'boo')
    assert parts == (b'boo',)
    assert encoding == 0
    assert cls == 0

    parts, encoding, cls = gsm.make_parts(u'boo' * 100)
    assert len(parts) == 2
    assert encoding == 0
    assert cls == 64


def test_cyrillic_parts():
    parts, encoding, cls = gsm.make_parts(u'буу' * 25)
    assert len(parts) == 2
    assert encoding == 8
    assert cls == 64


def test_too_long_parts():
    with pytest.raises(gsm.MessageTooLong):
        gsm.make_parts('a' * (160 * 256))
