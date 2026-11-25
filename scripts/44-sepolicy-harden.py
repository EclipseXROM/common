"""Make chosen SELinux domains ENFORCING in a v28 kernel policy (output of 43-sepolicy-downgrade.py).

Why this is needed: on the hybrid (stock 3.10.17 kernel + LOS13 ramdisk) /init has no security xattr, so init never
transitions into u:r:init:s0 and every init-started daemon (servicemanager, surfaceflinger, netd, logd, rild, mediaserver...)
runs in the single domain u:r:kernel:s0. App domains (untrusted_app, platform_app, ...) DO get their own domains from zygote.
The AOSP policy only allows an app to talk to the real daemon domains, so enforcing an app domain would deny every access to
`kernel`. We therefore copy, for every ENFORCED domain S, each allow rule  S -> D  (D = any domain type that is a target of
process/binder rules) to  S -> kernel  (merged, never narrowing anything). Everything else stays as the ROM policy defines it.

  python -I scripts/44-sepolicy-harden.py <in-v28-policy> <out-policy> <domain> [<domain> ...]
  python -I scripts/44-sepolicy-harden.py <in-v28-policy> --list     (type/class summary)
"""
import struct, sys

ALLOWED = 0x0001


class R:
    def __init__(s, b): s.b, s.p = b, 0
    def u32(s): v = struct.unpack_from("<I", s.b, s.p)[0]; s.p += 4; return v
    def raw(s, n): v = s.b[s.p:s.p + n]; s.p += n; return v
    def ebitmap(s):
        s.u32(); s.u32(); n = s.u32(); s.p += 12 * n


def parse_expr(r):
    for _ in range(r.u32()):
        et, _a, _o = r.u32(), r.u32(), r.u32()
        if et == 5: r.ebitmap()


def parse(b):
    r = R(b)
    assert r.u32() == 0xf97cff8c
    r.raw(r.u32())
    ver_off = r.p; ver = r.u32(); r.u32(); symn = r.u32(); r.u32()
    assert ver == 28 and symn == 8, (ver, symn)
    r.ebitmap()                                       # policy capabilities
    perm_range = (r.p, None); r.ebitmap(); perm_range = (perm_range[0], r.p)
    types, classes = {}, {}
    commons, cperms, ccommon = {}, {}, {}
    ntypes = 0
    for sym in range(8):
        nprim, nel = r.u32(), r.u32()
        if sym == 3: ntypes = nprim
        for _ in range(nel):
            if sym == 2:
                ln = r.u32(); r.u32(); r.u32(); r.raw(ln); r.ebitmap(); r.ebitmap()
            elif sym == 3:
                ln = r.u32(); val = r.u32(); r.u32(); r.u32(); types[r.raw(ln).decode()] = val
            elif sym == 4:
                ln = r.u32(); r.u32(); r.u32(); r.raw(ln); r.ebitmap()
                items = r.u32(); r.p += 4 * items; r.ebitmap()
                if items > 1: r.ebitmap()
                r.u32(); r.ebitmap()
            elif sym == 5:
                r.u32(); r.u32(); ln = r.u32(); r.raw(ln)
            elif sym == 6:
                ln = r.u32(); r.u32(); r.raw(ln); r.u32(); r.ebitmap()
            elif sym == 7:
                ln = r.u32(); r.u32(); r.u32(); r.raw(ln)
            elif sym == 0:
                ln, _v, _np, pn = r.u32(), r.u32(), r.u32(), r.u32(); cname = r.raw(ln).decode(); commons[cname] = {}
                for _ in range(pn): pl, pv = r.u32(), r.u32(); commons[cname][r.raw(pl).decode()] = pv
            else:
                ln, ln2, val, _np, pn, ncons = (r.u32() for _ in range(6)); name = r.raw(ln).decode(); ccommon[name] = r.raw(ln2).decode()
                classes[name] = val; cperms[name] = {}
                for _ in range(pn): pl, pv = r.u32(), r.u32(); cperms[name][r.raw(pl).decode()] = pv
                for _ in range(ncons): r.u32(); parse_expr(r)
                for _ in range(r.u32()): parse_expr(r)
                r.u32(); r.u32(); r.u32(); r.u32()
    nel_off = r.p; nel = r.u32(); rules = {}; order = []
    for _ in range(nel):
        k = struct.unpack_from("<4H", b, r.p); r.p += 8
        d = struct.unpack_from("<I", b, r.p)[0]; r.p += 4
        if k in rules: raise SystemExit("duplicate avtab key %r in input policy" % (k,))
        rules[k] = d; order.append(k)
    return dict(types=types, classes=classes, commons=commons, cperms=cperms, ccommon=ccommon, ntypes=ntypes, perm_range=perm_range, nel_off=nel_off,
                avtab_end=r.p, rules=rules, order=order, ver_off=ver_off)


def perm_bitmap(permissive_values, ntypes):
    top = ntypes + 1
    nodes = []; start = 0
    while start < top:
        m = 0
        for bit in range(64):
            v = start + bit
            if v in permissive_values: m |= 1 << bit
        if m: nodes.append((start, m))
        start += 64
    return struct.pack("<III", 64, start, len(nodes)) + b"".join(struct.pack("<IQ", a, m) for a, m in nodes)


def harden(b, domains, extra=()):
    p = parse(b)
    T, C, rules = p["types"], p["classes"], p["rules"]
    missing = [d for d in domains if d not in T]
    if missing: raise SystemExit("unknown domain type(s): %s" % ", ".join(missing))
    kernel = T["kernel"]
    enforce = {T[d] for d in domains}
    proc, binder = C["process"], C["binder"]
    # domain types = targets of process/binder rules (attribute-expanded avtab has real types only)
    D = {k[1] for k in rules if k[2] in (proc, binder) and k[3] == ALLOWED}
    D.discard(kernel)
    new = dict(rules); added = widened = 0
    for (s, t, c, spec), data in rules.items():
        if spec != ALLOWED or s not in enforce or t not in D: continue
        key = (s, kernel, c, ALLOWED)
        if key in new:
            if new[key] | data != new[key]: new[key] |= data; widened += 1
        else:
            new[key] = data; added += 1
    for spec in extra:                                   # "src:tgt:class:perm[,perm]" by name, ADDS only
        src, tgt, cls, perms = spec.split(":")
        pm = dict(p["commons"].get(p["ccommon"].get(cls, ""), {})); pm.update(p["cperms"][cls])
        bits = 0
        for pn in perms.split(","): bits |= 1 << (pm[pn] - 1)
        key = (T[src], T[tgt], C[cls], ALLOWED)
        new[key] = new.get(key, 0) | bits
    keep = list(p["order"]) + [k for k in new if k not in rules]
    avtab = struct.pack("<I", len(keep)) + b"".join(struct.pack("<4HI", *k, new[k]) for k in keep)
    perm = perm_bitmap({v for v in T.values()} - enforce, p["ntypes"])
    a, z = p["perm_range"]
    out = bytearray(b[:a]) + perm + b[z:p["nel_off"]] + avtab + b[p["avtab_end"]:]
    return bytes(out), dict(domains=len(enforce), domain_targets=len(D), added=added, widened=widened,
                            rules_in=len(rules), rules_out=len(keep))


if __name__ == "__main__":
    data = open(sys.argv[1], "rb").read()
    if sys.argv[2] == "--list":
        p = parse(data)
        print("types", len(p["types"]), "classes", len(p["classes"]), "avtab", len(p["rules"]))
        print(" ".join(sorted(t for t in p["types"] if t.endswith("_app") or t in ("system_server", "radio", "shell", "kernel", "init"))))
        sys.exit(0)
    import os
    out, st = harden(data, sys.argv[3:], [e for e in os.environ.get("MK_ALLOW", "").split(";") if e])
    open(sys.argv[2], "wb").write(out)
    print("hardened:", st, "|", len(data), "->", len(out), "bytes")
