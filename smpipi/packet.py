from struct import Struct


class AttrDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class Integer(object):
    default = 0

    def __init__(self, fmt):
        self.struct = Struct(fmt)

    def encode(self, value):
        return self.struct.pack(value)

    def decode(self, buf, offset):
        value, = self.struct.unpack_from(buf, offset)
        return value, offset + self.struct.size


class String(object):
    default = ''

    def __init__(self, size):
        self.size = size

    def encode(self, value):
        return str(value)

    def decode(self, buf, offset):
        return buf[offset:offset+self.size], offset+self.size


class NString(object):
    default = ''

    def __init__(self, max):
        self.max = max

    def encode(self, value):
        return str(value) + '\x00'

    def decode(self, buf, offset):
        pos = buf.find('\x00', offset, offset+self.max)
        assert pos >= 0
        return buf[offset:pos], pos + 1


class NStringDec(NString):
    pass


class NStringHex(NString):
    pass


int32 = Integer('!L')
int16 = Integer('!H')
int8 = Integer('!B')


class Field(object):
    counter = 0

    def __init__(self, type):
        self.type = type
        self.set_order()

    def set_order(self):
        self.order = Field.counter
        Field.counter += 1

    def decode(self, ctx, buf, offset):
        return self.type.decode(buf, offset)

    def prepare(self, ctx, value):
        pass

    def encode(self, value):
        if value is None:
            value = self.type.default
        return self.type.encode(value)


class VarField(Field):
    def __init__(self, name, max):
        self.name = name
        self.max = max
        self.set_order()

    def decode(self, ctx, buf, offset):
        return String(ctx[self.name]).decode(buf, offset)

    def prepare(self, ctx, value):
        if value is None:
            value = ''
        ctx[self.name] = len(value)

    def encode(self, value):
        if value is None:
            value = ''
        return str(value)


class PacketMeta(type):
    def __init__(cls, name, bases, fields):
        fmt_fields = [(k, v) for k, v in fields.items() if isinstance(v, Field)]
        cls.fields = sorted(fmt_fields, key=lambda r: r[1].order)


class Packet(PacketMeta('PacketBase', (object,), {})):
    @classmethod
    def decode(cls, buf, offset=0):
        result = AttrDict()
        for name, field in cls.fields:
            result[name], offset = field.decode(result, buf, offset)

        return result, offset

    @classmethod
    def encode(cls, data):
        result = ''
        for name, field in cls.fields:
            field.prepare(data, data.get(name))

        for name, field in cls.fields:
            result += field.encode(data.get(name))

        return result
