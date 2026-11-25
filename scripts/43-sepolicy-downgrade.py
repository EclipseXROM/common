"""Downgrade a kernel binary SELinux policy (v30/v29) to v28 so a 3.10.17 kernel (accepts 15..28) can load it.
v30 adds xperms (only used by allowxperm rules, absent in Android M policy -> checked by flag scan of avtab is skipped,
verified by the kernel on load); v29 adds a type_set (ebitmap types, ebitmap negset, u32 flags) after the `names`
ebitmap of every CEXPR_NAMES constraint expression. We drop those and stamp version 28.
Only the header + commons + classes need parsing (constraints live in classes); everything after is copied verbatim."""
import struct, sys

class R:
    def __init__(s, b): s.b, s.p = b, 0
    def u32(s): v = struct.unpack_from("<I", s.b, s.p)[0]; s.p += 4; return v
    def raw(s, n): v = s.b[s.p:s.p+n]; s.p += n; return v
    def ebitmap(s):   # mapunit, highbit, count, count*(u32 startbit, u64 map)
        s.u32(); s.u32(); n = s.u32(); s.p += 12 * n

CEXPR_NAMES = 5

def parse_expr(r, has_tset, cut):
    """returns nothing; records [start,end) ranges of type_set bytes in `cut`"""
    nexpr = r.u32()
    for _ in range(nexpr):
        et, attr, op = r.u32(), r.u32(), r.u32()
        if et == CEXPR_NAMES:
            r.ebitmap()
            if has_tset:
                a = r.p; r.ebitmap(); r.ebitmap(); r.u32(); cut.append((a, r.p))

def downgrade(b):
    r = R(b)
    magic = r.u32(); assert magic == 0xf97cff8c, hex(magic)
    slen = r.u32(); r.raw(slen)
    ver_off = r.p; ver = r.u32(); cfg = r.u32(); symn = r.u32(); ocn = r.u32()
    assert symn == 8, symn
    if ver >= 22: r.ebitmap()          # policy capabilities
    perm_range = None
    if ver >= 23: a0 = r.p; r.ebitmap(); perm_range = (a0, r.p)     # permissive types (bit = type value)
    has_tset = ver >= 29
    cut = []; type_nprim = [0]
    for sym in range(8):
        nprim, nel = r.u32(), r.u32()
        if sym == 3: type_nprim[0] = nprim
        for _ in range(nel):
            if sym == 2:                     # role: len, value, [bounds], key, dominates, types
                ln = r.u32(); r.u32()
                if ver >= 24: r.u32()
                r.raw(ln); r.ebitmap(); r.ebitmap()
            elif sym == 3:                   # type: len, value, [properties, bounds], key
                ln = r.u32(); r.u32()
                if ver >= 24: r.u32(); r.u32()
                r.raw(ln)
            elif sym == 4:                   # user: len, value, [bounds], key, roles, [range, default level]
                ln = r.u32(); r.u32()
                if ver >= 24: r.u32()
                r.raw(ln); r.ebitmap()
                if ver >= 19:
                    items = r.u32(); r.p += 4 * items; r.ebitmap()
                    if items > 1: r.ebitmap()
                    r.u32(); r.ebitmap()
            elif sym == 5:                   # bool: value, state, len, key
                r.u32(); r.u32(); ln = r.u32(); r.raw(ln)
            elif sym == 6:                   # level (sensitivity): len, isalias, key, level(sens, cats)
                ln = r.u32(); r.u32(); r.raw(ln); r.u32(); r.ebitmap()
            elif sym == 7:                   # category: len, value, isalias, key
                ln = r.u32(); r.u32(); r.u32(); r.raw(ln)
            elif sym == 0:                     # common: len, value, nprim, nel, key, perms
                ln, _v, _np, pn = r.u32(), r.u32(), r.u32(), r.u32(); r.raw(ln)
                for _ in range(pn): pl, _pv = r.u32(), r.u32(); r.raw(pl)
            else:                            # class
                ln, ln2, _v, _np, pn, ncons = (r.u32() for _ in range(6)); r.raw(ln); r.raw(ln2)
                for _ in range(pn): pl, _pv = r.u32(), r.u32(); r.raw(pl)
                for _ in range(ncons): r.u32(); parse_expr(r, has_tset, cut)       # constraint: perms, exprs
                if ver >= 19:                                                       # validatetrans
                    for _ in range(r.u32()): parse_expr(r, has_tset, cut)
                if ver >= 27: r.u32(); r.u32(); r.u32()                             # default user/role/range
                if ver >= 28: r.u32()                                               # default type
    # main avtab: nel, then entries (4*u16 key; xperms entries (flag 0x0700) carry 1+1+32 bytes, others a u32)
    nel_off = r.p; nel = r.u32(); kept = bytearray(); dropped = 0; first_entry = r.p
    for _ in range(nel):
        a = r.p; src, tgt, cls, spec = struct.unpack_from("<4H", b, r.p); r.p += 8
        if spec & 0x0700: r.p += 33; dropped += 1; continue
        r.p += 4; kept += b[a:r.p]
    avtab_end = r.p
    cut_avtab = (nel_off, avtab_end, struct.pack("<I", nel - dropped) + bytes(kept))
    # make EVERY type permissive: the stock kernel (unlike the LOS one) has no forced-permissive hack and init enforces
    ntypes = type_nprim[0]; top = ntypes + 1
    nodes = []; start = 0
    while start < top:
        m = 0
        for bit in range(64):
            v = start + bit
            if 1 <= v <= ntypes: m |= 1 << bit
        nodes.append((start, m)); start += 64
    highbit = start
    perm_bytes = struct.pack("<III", 64, highbit, len(nodes)) + b"".join(struct.pack("<IQ", a, m) for a, m in nodes)
    out = bytearray(); last = 0
    items = sorted([(a, z, b"") for a, z in cut] + [cut_avtab] + [(perm_range[0], perm_range[1], perm_bytes)])
    for a, z, rep in items: out += b[last:a] + rep; last = z
    out += b[last:]
    struct.pack_into("<I", out, ver_off, 28)
    return bytes(out), ver, len(cut), dropped, nel

if __name__ == "__main__":
    data = open(sys.argv[1], "rb").read()
    new, ver, n, dropped, nel = downgrade(data)
    open(sys.argv[2], "wb").write(new)
    print(f"v{ver} -> v28: removed {n} type_set blocks and {dropped}/{nel} xperms avtab entries, all types set permissive, {len(data)} -> {len(new)} bytes")
