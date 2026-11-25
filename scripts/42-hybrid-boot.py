"""Hybrid boot image: STOCK Samsung kernel (3.10.17, known to bring the modem up) + LineageOS 13 ramdisk
(already patched: /productinfo fstab line commented). Header fields (addresses, page size, name, cmdline) from stock."""
import gzip, hashlib, os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = f"{ROOT}/recon/boot"
H = struct.Struct("<8s10I16s512s32s1024s")
def parse(p):
    img = open(p, "rb").read(); f = H.unpack_from(img); page = f[8]
    up = lambda n: (n + page - 1) // page * page
    ko = page; ro = ko + up(f[1]); so = ro + up(f[3])
    return f, img[ko:ko+f[1]], img[ro:ro+f[3]], img[so:so+f[5]], page
sf, skern, sram, ssec, page = parse(f"{ROOT}/recon/stock/boot-stock.img")
lf, lkern, lram, lsec, lpage = parse(f"{B}/boot-patched.img")
assert page == lpage == 2048
# --- kernel identity: init_uts_ns release/version (uname, /proc/version) + linux_banner (dmesg) ---
# The stock image is an uncompressed zImage, so the strings are patched in place. init_uts_ns holds
# 65-byte NUL-padded fields; the banners are NUL-terminated .rodata strings, so a shorter replacement
# is padded and a longer one is refused. VERMAGIC_STRING (module vermagic) is left untouched on purpose:
# mali.ko is built for 3.10.17-8496516 and insmod compares against that constant, not against utsname.
KREL_OLD, KREL_NEW = b"3.10.17-8496516", b"3.10.17-manikineko"
KVER_OLD, KVER_NEW = b"#2 SMP PREEMPT Wed Jan 4 20:01:38 KST 2017", b"#1 SMP PREEMPT Tue Nov 24 04:30 UTC 2026"
BANNER_OLD = b"Linux version 3.10.17-8496516 (dpi@SWHD7303) (gcc version 4.7 (GCC) ) " + KVER_OLD + b"\n"
BANNER_NEW = b"Linux version 3.10.17-manikineko (manikineko) (gcc version 4.7 (GCC) ) " + KVER_NEW + b"\n"
PROC_OLD = b"%s version %s (dpi@SWHD7303) (gcc version 4.7 (GCC) ) %s\n"
PROC_NEW = b"%s version %s (manikineko) (gcc version 4.7 (GCC) ) %s\n"
skern = bytearray(skern)
def put(off, old, new):
    assert skern[off:off + len(old)] == old, ("kernel string not found at", off)
    assert len(new) <= len(old), ("kernel string too long", len(new), len(old))
    skern[off:off + len(old)] = new + b"\0" * (len(old) - len(new))
i = skern.find(KREL_OLD + b"\0" * (65 - len(KREL_OLD))); assert i > 0, "uts release field not found"
put(i, KREL_OLD + b"\0" * (65 - len(KREL_OLD)), KREL_NEW)
i = skern.find(KVER_OLD + b"\0" * (65 - len(KVER_OLD))); assert i > 0, "uts version field not found"
put(i, KVER_OLD + b"\0" * (65 - len(KVER_OLD)), KVER_NEW)
i = skern.find(BANNER_OLD); assert i > 0, "linux_banner not found"
put(i, BANNER_OLD, BANNER_NEW)
i = skern.find(PROC_OLD); assert i > 0, "linux_proc_banner not found"
put(i, PROC_OLD, PROC_NEW)
skern = bytes(skern)
print("kernel identity:", KREL_NEW.decode(), "|", KVER_NEW.decode())
print("stock kernel", len(skern), "| LOS ramdisk", len(lram), "| stock cmdline:", sf[12].split(b"\0")[0].decode(),
      "| LOS cmdline:", lf[12].split(b"\0")[0].decode())
# SELinux policy version inside the LOS ramdisk (kernel 3.10 supports <= 29)
raw = gzip.decompress(lram); i = raw.find(b"070701"); pos = 0
while True:
    h = raw[pos+6:pos+110]; v = lambda k: int(h[k*8:(k+1)*8], 16); fs, ns = v(6), v(11)
    name = raw[pos+110:pos+110+ns-1].decode(); pos = (pos+110+ns+3) & ~3; data = raw[pos:pos+fs]; pos = (pos+fs+3) & ~3
    if name == "TRAILER!!!": break
    if name == "sepolicy":
        magic, slen = struct.unpack_from("<II", data); ver = struct.unpack_from("<I", data, 8 + slen)[0]
        print("LOS sepolicy: magic %#x policydb version %d (kernel 3.10 max 29)" % (magic, ver))
# stock 3.10.17 kernel only loads SELinux policy v15..28: convert the ramdisk's sepolicy (v30) with 43-sepolicy-downgrade
import importlib.util
_sp = importlib.util.spec_from_file_location("dg", f"{ROOT}/scripts/43-sepolicy-downgrade.py")
dg = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(dg)
# SELinux hardening (scripts/44): domains listed in MK_ENFORCE (comma separated) are made enforcing, rest stay permissive
_hp = importlib.util.spec_from_file_location("hd", f"{ROOT}/scripts/44-sepolicy-harden.py")
hd = importlib.util.module_from_spec(_hp); _hp.loader.exec_module(hd)
DEFAULT_ENFORCE = "untrusted_app,isolated_app,platform_app,system_app,bluetooth,nfc,radio,system_server"   # beta 1.5; MK_ENFORCE="" = old all-permissive 1.4 policy
ENFORCE = [d for d in os.environ.get("MK_ENFORCE", DEFAULT_ENFORCE).split(",") if d]
BOOT_OUT = os.environ.get("MK_BOOT_OUT", "boot-hybrid.img")
# narrow, named extras (src:tgt:class:perm,perm joined by ';'): gps HAL text relocations; CM themeservice runs as platform_app and owns /data/system/theme
DEFAULT_ALLOW = ("system_server:system_file:file:execmod;"
                 "platform_app:themeservice_app_data_file:dir:getattr,search,read,open,write,add_name,remove_name,setattr,create,rmdir;"
                 "platform_app:themeservice_app_data_file:file:getattr,read,open,write,create,setattr,unlink,rename,append,lock")
ALLOW = [a for a in os.environ.get("MK_ALLOW", DEFAULT_ALLOW).split(";") if a]   # narrow extra rules "src:tgt:class:perm,perm" (by name)
pos = 0; out_cpio = bytearray(); ALIASES = {"init.sc8830.rc": "init.unknown.rc", "ueventd.sc8830.rc": "ueventd.unknown.rc", "fstab.sc8830": "fstab.unknown"}
saved = {}   # stock kernel gives no androidboot.hardware -> init uses ro.hardware=unknown: alias the sc8830 files
while True:
    h = raw[pos+6:pos+110]; v = lambda k: int(h[k*8:(k+1)*8], 16); fs, ns = v(6), v(11)
    name = raw[pos+110:pos+110+ns-1].decode(); dstart = (pos+110+ns+3) & ~3
    data = raw[dstart:dstart+fs]; nxt = (dstart+fs+3) & ~3
    if name in ALIASES: saved[name] = (bytes(raw[pos:pos+110]), data)
    if name == "TRAILER!!!":
        for k, (src, dst) in enumerate(ALIASES.items()):
            hdr, body = saved[src]; hdr = bytearray(hdr); nm = dst.encode() + bytes([0])
            if dst == "init.unknown.rc":   # hybrid-only: the stock kernel has Mali as a module (LOS kernel has it built in)
                body = body + "\n".join(["", "# --- Manikineko hybrid (stock 3.10.17 kernel) ---",
                                         "on post-fs", "    insmod /mali.ko", "",
                                         # Spreadtrum's `pipe` init command does not exist in Android 6 init, so the FIFOs
                                         # are never created; the audio HAL then select()s on fd -1 -> FORTIFY abort.
                                         "on boot", "    start mk_pipes", "",   # after early-boot made /dev/pipe
                                         "service mk_pipes /system/bin/mkfifo -m 666 /dev/pipe/mmi.audio.ctrl"
                                         " /dev/rpipe/ril.vt.0 /dev/rpipe/ril.vt.1 /dev/rpipe/ril.vt.2",
                                         "    user root", "    oneshot", "    disabled", "",
                                         # init services run with umask 077: open the FIFOs up once mkfifo is done
                                         "on property:init.svc.mk_pipes=stopped",
                                         "    chmod 0666 /dev/pipe/mmi.audio.ctrl", "    chmod 0666 /dev/rpipe/ril.vt.0",
                                         "    chmod 0666 /dev/rpipe/ril.vt.1", "    chmod 0666 /dev/rpipe/ril.vt.2", ""]).encode()
                hdr[6+6*8:6+7*8] = b"%08X" % len(body)
            hdr[6:14] = b"%08X" % (0x7E000000 + k)                     # unique inode number
            hdr[6+11*8:6+12*8] = b"%08X" % len(nm)                       # namesize
            entry = bytes(hdr) + nm; entry += bytes((4 - len(entry) % 4) % 4)
            entry += body; entry += bytes((4 - len(entry) % 4) % 4)
            out_cpio += entry; print("added alias", dst, "<-", src, len(body), "bytes")
        # stock Mali r4p0 kernel module (vermagic 3.10.17-8496516), matches LOS libMali.so (byte-identical to stock)
        ko = open(f"{ROOT}/recon/boot/mali.ko", "rb").read(); hdr = bytearray(saved["fstab.sc8830"][0]); nm = b"mali.ko" + bytes([0])
        hdr[6:14] = b"%08X" % 0x7E0000F0; hdr[14:22] = b"%08X" % 0o100644
        hdr[6+6*8:6+7*8] = b"%08X" % len(ko); hdr[6+11*8:6+12*8] = b"%08X" % len(nm)
        entry = bytes(hdr) + nm; entry += bytes((4 - len(entry) % 4) % 4); entry += ko; entry += bytes((4 - len(entry) % 4) % 4)
        out_cpio += entry; print("added /mali.ko", len(ko), "bytes")
    if name == "sepolicy":
        data, ver, ncut, dropped, nel = dg.downgrade(data); print(f"sepolicy v{ver} -> v28 ({ncut} type_sets, {dropped}/{nel} xperms rules removed, {fs} -> {len(data)} bytes)")
        if ENFORCE:
            data, st = hd.harden(data, ENFORCE, ALLOW); print("sepolicy hardened, enforcing:", ENFORCE, st)
        hdr = bytearray(raw[pos:pos+110]); hdr[6+6*8:6+7*8] = b"%08X" % len(data)
        out_cpio += hdr + raw[pos+110:dstart] + data + bytes((4 - len(data) % 4) % 4)
    elif name == "init.rc":
        # LOS bug: `service media` lists 15 supplementary groups, Android 6 init accepts at most 12 and then drops the whole
        # group option -> mediaserver runs without audio/camera groups (no sound, camera HAL shim not applied).
        old_g = b"    group system audio camera inet net_bt net_bt_admin net_bw_acct drmrpc qcom_diag mediadrm radio sdcard_rw sdcard_r media_rw shell"
        new_g = b"    group system audio camera inet net_bt net_bt_admin net_bw_acct drmrpc mediadrm radio sdcard_rw media_rw"
        assert data.count(old_g) == 1, "media group line not found"
        data = data.replace(old_g, new_g); print("init.rc: media service groups 15 -> 11 supplementary")
        # LOS bug 2: the camera HAL shim points to libmemoryheapion_sprd.so, which is not in /system; the exported
        # android::MemoryHeapIon ctor lives in /system/lib/libmemoryheapion.so
        assert data.count(b"libmemoryheapion_sprd.so") == 2
        data = data.replace(b"libmemoryheapion_sprd.so", b"libmemoryheapion.so"); print("init.rc: camera shim -> libmemoryheapion.so")
        hdr = bytearray(raw[pos:pos+110]); hdr[6+6*8:6+7*8] = b"%08X" % len(data)
        out_cpio += hdr + raw[pos+110:dstart] + data + bytes((4 - len(data) % 4) % 4)
    elif name == "init.kanas3g_base.rc":
        # SM-G355HN is single-SIM; this LOS build is configured dual-SIM (SM-G355H DUOS) -> SubscriptionInfoUpdater waits for
        # SIM2 forever, no subscription, only emergency calls. Also see build.prop changes (ro.modem.w.count etc.).
        old_s = b"    setprop ro.multisim.simslotcount 2"; assert data.count(old_s) == 1
        data = data.replace(old_s, b"    setprop ro.multisim.simslotcount 1"); print("init.kanas3g_base.rc: simslotcount 2 -> 1")
        hdr = bytearray(raw[pos:pos+110]); hdr[6+6*8:6+7*8] = b"%08X" % len(data)
        out_cpio += hdr + raw[pos+110:dstart] + data + bytes((4 - len(data) % 4) % 4)
    elif name == "file_contexts":
        # stock kernel rootfs has no security xattr support: restorecon("/init") must find the label already correct.
        # The inode's in-core context comes from the policy genfscon (rootfs), so declare /init as rootfs here.
        old = b"/init			u:object_r:init_exec:s0"; assert data.count(old) == 1, "file_contexts /init line not found"
        data = data.replace(old, b"/init			u:object_r:rootfs:s0"); print("file_contexts: /init -> rootfs")
        hdr = bytearray(raw[pos:pos+110]); hdr[6+6*8:6+7*8] = b"%08X" % len(data)
        out_cpio += hdr + raw[pos+110:dstart] + data + bytes((4 - len(data) % 4) % 4)
    else:
        out_cpio += raw[pos:nxt]
    pos = nxt
    if name == "TRAILER!!!": break
patched = bytes(out_cpio)
lram = gzip.compress(patched, 9, mtime=0)
sha = hashlib.sha1(skern + struct.pack("<I", len(skern)) + lram + struct.pack("<I", len(lram)) + b"" + struct.pack("<I", 0))
hdr = H.pack(sf[0], len(skern), sf[2], len(lram), sf[4], 0, sf[6], sf[7], page, sf[9], sf[10], sf[11], sf[12], sha.digest() + b"\0"*12, sf[14])
pad = lambda b: b + b"\0" * ((len(b) + page - 1) // page * page - len(b))
out = pad(hdr) + pad(skern) + pad(lram)
open(f"{B}/{BOOT_OUT}", "wb").write(out)
print(BOOT_OUT, len(out), "bytes sha256", hashlib.sha256(out).hexdigest())
