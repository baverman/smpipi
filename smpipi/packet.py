from struct import Struct


class AttrDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class Integer(object):
    default = 0

    def __init__(self, fmt):
        self.struct = Struct(fmt)

    def encode(self, value):
        if value is None:
            value = 0
        return self.struct.pack(int(value))

    def decode(self, buf, offset):
        value, = self.struct.unpack_from(buf, offset)
        return value, offset + self.struct.size


class String(object):
    def __init__(self, max):
        self.max = max

    def encode(self, value):
        if value is None:
            value = ''

        value = str(value)
        return value, len(value)

    def decode(self, buf, offset, size):
        return buf[offset:offset+size], offset+size


class NString(object):
    def __init__(self, max):
        self.max = max

    def encode(self, value):
        if value is None:
            value = ''
        return str(value) + '\x00'

    def decode(self, buf, offset):
        pos = buf.find('\x00', offset, offset+self.max)
        assert pos >= 0
        return buf[offset:pos], pos + 1


class Array(object):
    def __init__(self, packet):
        self.packet = packet

    def encode(self, value):
        result = ''
        for v in value or []:
            result += self.packet.encode(v)
        return result, value and len(value) or 0

    def decode(self, buf, offset, size):
        result = []
        for _ in xrange(size):
            value, offset = self.packet.decode(buf, offset)
            result.append(value)
        return result, offset


int32 = Integer('!L')
int16 = Integer('!H')
int8 = Integer('!B')


class Field(object):
    counter = 0

    def __init__(self, type, name=None):
        self.type = type
        self.set_order()
        self.name = name

    def set_order(self):
        self.order = Field.counter
        Field.counter += 1

    def decode(self, ctx, buf, offset):
        value, offset = self.type.decode(buf, offset)
        ctx[self.name] = value
        return offset

    def encode(self, ctx):
        return self.type.encode(ctx.get(self.name))


class SizeField(Field):
    def __init__(self, length_field, type):
        self.length_field = length_field
        self.type = type
        self.set_order()

    def decode(self, ctx, buf, offset):
        offset = self.length_field.decode(ctx, buf, offset)
        size = ctx[self.length_field.name]
        value, offset = self.type.decode(buf, offset, size)
        ctx[self.name] = value
        return offset

    def encode(self, ctx):
        value, size = self.type.encode(ctx.get(self.name))
        ctx[self.length_field.name] = size
        return self.length_field.encode(ctx) + value


class DispatchField(Field):
    def __init__(self, type, mapping):
        self.type = type
        self.mapping = mapping
        self.set_order()

    def decode(self, ctx, buf, offset):
        dval, offset = self.type.decode(buf, offset)
        ctx[self.name] = dval
        value, offset = self.mapping[dval].decode(buf, offset)
        ctx.update(value)
        return offset

    def encode(self, ctx):
        dval = ctx[self.name]
        return self.type.encode(dval) + self.mapping[dval].encode(ctx)


def with_name(field, name):
    field.name = name
    return field


class PacketMeta(type):
    def __init__(cls, name, bases, fields):
        fmt_fields = [with_name(v, k) for k, v in fields.items() if isinstance(v, Field)]
        cls.fields = sorted(fmt_fields, key=lambda r: r.order)


class Packet(PacketMeta('PacketBase', (object,), {})):
    @classmethod
    def decode(cls, buf, offset=0):
        result = AttrDict()
        for field in cls.fields:
            offset = field.decode(result, buf, offset)

        return result, offset

    @classmethod
    def encode(cls, data):
        result = ''
        for field in cls.fields:
            result += field.encode(data)

        return result
