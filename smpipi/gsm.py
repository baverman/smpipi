# -*- coding: utf8 -*-
import binascii
import random

# from http://stackoverflow.com/questions/2452861/python-library-for-converting-plain-text-ascii-into-gsm-7-bit-character-set
gsm = (u"@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>"
       u"?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ`¿abcdefghijklmnopqrstuvwxyzäöñüà")
ext = (u"````````````````````^```````````````````{}`````\\````````````[~]`"
       u"|````````````````````````````````````€``````````````````````````")

SMPP_ENCODING_DEFAULT = 0x00  # SMSC Default
SMPP_ENCODING_ISO88591 = 0x03  # Latin 1 (ISO-8859-1)
SMPP_ENCODING_ISO10646 = 0x08  # UCS2 (ISO/IEC-10646)

SMPP_GSMFEAT_UDHI = 0x40  # UDHI Indicator (only relevant for MT msgs)
SMPP_MSGTYPE_DEFAULT = 0x00  # Default message type (i.e. normal message)

SEVENBIT_SIZE = 160
EIGHTBIT_SIZE = 140
UCS2_SIZE = 70
SEVENBIT_MP_SIZE = SEVENBIT_SIZE - 7
EIGHTBIT_MP_SIZE = EIGHTBIT_SIZE - 6
UCS2_MP_SIZE = UCS2_SIZE - 3


class EncodeError(ValueError):
    pass


class MessageTooLong(ValueError):
    pass


def gsm_encode(plaintext, hex=False):
    """Replace non-GSM ASCII symbols"""
    res = ""
    for c in plaintext:
        idx = gsm.find(c)
        if idx != -1:
            res += chr(idx)
            continue
        idx = ext.find(c)
        if idx != -1:
            res += chr(27) + chr(idx)
            continue
        raise EncodeError()
    return binascii.b2a_hex(res) if hex else res


def encode(text):
    try:
        text = gsm_encode(text)
        encoding = SMPP_ENCODING_DEFAULT
    except EncodeError:
        encoding = SMPP_ENCODING_ISO10646
        text = text.encode('utf-16-be')

    return text, encoding


def make_parts(text):
    """Returns tuple(parts, encoding, esm_class)"""
    try:
        text = gsm_encode(text)
        encoding = SMPP_ENCODING_DEFAULT
        need_split = len(text) > SEVENBIT_SIZE
        partsize = SEVENBIT_MP_SIZE
        encode = lambda s: s
    except EncodeError:
        encoding = SMPP_ENCODING_ISO10646
        need_split = len(text) > UCS2_SIZE
        partsize = UCS2_MP_SIZE
        encode = lambda s: s.encode('utf-16-be')

    esm_class = SMPP_MSGTYPE_DEFAULT

    if need_split:
        esm_class = SMPP_GSMFEAT_UDHI

        starts = tuple(range(0, len(text), partsize))
        if len(starts) > 255:
            raise MessageTooLong()

        parts = []
        ipart = 1
        uid = random.randint(0, 255)
        for start in starts:
            parts.append(''.join(('\x05\x00\x03', chr(uid),
                                  chr(len(starts)), chr(ipart),
                                  encode(text[start:start + partsize]))))
            ipart += 1
    else:
        parts = (encode(text),)

    return parts, encoding, esm_class
