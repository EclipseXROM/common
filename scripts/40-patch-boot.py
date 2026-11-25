"""Patch LineageOS 13 boot.img: fstab.sc8830 has a /productinfo (PRODNV) entry, but on this device that
partition ('prodnv', p15) holds no ext4 filesystem and the stock firmware never mounted it. mount_all therefore
fails, ro.crypto.state is never set and init never starts class main (zygote). Fix: comment that one line out
(same-length edit: first '/' -> '#'), then repack."""
import gzip, hashlib, struct, sys, zipfile, os, zlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP = f"{ROOT}/twrp/lineage-13.0-20170317-UNOFFICIAL-kanas-SandroidTeam-Ih24n.zip"
OUT = f"{ROOT}/recon/boot"
img = zipfile.ZipFile(ZIP).read("boot.img")
open(f"{OUT}/boot-orig.img", "wb").write(img)
H = struct.Struct("<8s10I16s512s32s1024s")
(magic, ksz, kadr, rsz, radr, ssz, sadr, tadr, page, dtsz, _u, name, cmd, _id, xcmd) = H.unpack_from(img)
assert magic == b"ANDROID!", magic
up = lambda n: (n + page - 1) // page * page
ko = page; ro = ko + up(ksz); so = ro + up(rsz); do = so + up(ssz)
kernel, ramdisk, second, dt = img[ko:ko+ksz], img[ro:ro+rsz], img[so:so+ssz], img[do:do+dtsz]
print("page", page, "kernel", ksz, "ramdisk", rsz, "second", ssz, "dt", dtsz)
raw = gzip.decompress(ramdisk)
old = b"/dev/block/platform/sprd-sdhci.3/by-name/PRODNV /productinfo"
new = b"#" + old[1:]
n = raw.count(old); print("occurrences of", old, "in ramdisk:", n)
assert n == 1
patched = raw.replace(old, new)
assert len(patched) == len(raw)
gz = gzip.compress(patched, 9, mtime=0)
sha = hashlib.sha1(kernel + struct.pack("<I", ksz) + gz + struct.pack("<I", len(gz)) + second + struct.pack("<I", ssz))
if dtsz: sha.update(dt + struct.pack("<I", dtsz))
bid = sha.digest() + b"\0" * 12
hdr = H.pack(magic, ksz, kadr, len(gz), radr, ssz, sadr, tadr, page, dtsz, _u, name, cmd, bid, xcmd)
pad = lambda b: b + b"\0" * (up(len(b)) - len(b))
out = pad(hdr) + pad(kernel) + pad(gz) + (pad(second) if ssz else b"") + (pad(dt) if dtsz else b"")
open(f"{OUT}/boot-patched.img", "wb").write(out)
print("patched ramdisk gz", len(gz), "(was", rsz, ") image", len(out), "bytes (orig", len(img), ")")
# self-check: re-parse and confirm the edit
chk = open(f"{OUT}/boot-patched.img", "rb").read()
f = H.unpack_from(chk); r2 = chk[page+up(f[1]):page+up(f[1])+f[3]]
d = gzip.decompress(r2); print("check: active entry left:", d.count(old), " commented:", d.count(new), " kernel identical:", chk[page:page+ksz] == kernel)
print("sha256", hashlib.sha256(out).hexdigest())
