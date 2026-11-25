"""Android sparse image -> raw. Usage: python -I 41-unsparse.py <tar.md5> <member> <out.raw>"""
import struct, sys, tarfile
tf = tarfile.open(sys.argv[1], "r:"); f = tf.extractfile(sys.argv[2])
magic, major, minor, fhs, chs, bs, tb, tc, crc = struct.unpack("<IHHHHIIII", f.read(28))
assert magic == 0xED26FF3A, hex(magic)
f.read(fhs - 28)
with open(sys.argv[3], "wb") as o:
    for _ in range(tc):
        ct, _r, cb, ts = struct.unpack("<HHII", f.read(12)); f.read(chs - 12)
        n = cb * bs
        if ct == 0xCAC1:   # RAW
            rem = n
            while rem:
                b = f.read(min(rem, 1 << 22)); o.write(b); rem -= len(b)
        elif ct == 0xCAC2: # FILL
            v = f.read(4); o.write(v * (n // 4))
        elif ct == 0xCAC3: # DONT_CARE
            o.seek(n, 1)
        elif ct == 0xCAC4: f.read(4)
    o.truncate(tb * bs)
print("raw size", tb * bs)
