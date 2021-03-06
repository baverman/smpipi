import sys
import struct

PY2 = sys.version_info[0] == 2

if PY2:  # pragma: no cover
    import __builtin__ as builtins
    range = builtins.xrange
    reduce = builtins.reduce
    string_types = (str, unicode)
    bchr = builtins.chr

    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()
    listkeys = lambda d: d.keys()
    listvalues = lambda d: d.values()
    listitems = lambda d: d.items()

    def bytestr(data, encoding='utf-8'):
        if isinstance(data, unicode):
            data = data.encode(encoding)
        elif not isinstance(data, str):
            data = str(data)
        return data
else:  # pragma: no cover
    import builtins
    from functools import reduce
    range = builtins.range
    string_types = (str, )

    iterkeys = lambda d: d.keys()
    itervalues = lambda d: d.values()
    iteritems = lambda d: d.items()
    listkeys = lambda d: list(d.keys())
    listvalues = lambda d: list(d.values())
    listitems = lambda d: list(d.items())

    def bytestr(data, encoding='utf-8'):
        if isinstance(data, str):
            data = data.encode(encoding)
        elif not isinstance(data, bytes):
            data = str(data).encode(encoding)

        return data

    bchr = struct.Struct('B').pack
