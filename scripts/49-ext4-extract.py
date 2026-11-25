"""Extract files from a raw ext4 image without mounting it.

Needed because the phone's TWRP kernel refuses to loop-mount the reconstructed ROM image
("Invalid argument"), and 7-Zip cannot open it either. Only the read path is implemented:
superblock, group descriptors, inode table, extent trees and linear directory entries.

Usage: python scripts/49-ext4-extract.py <image> <path-in-image> <out-dir-or-file>
Example: python scripts/49-ext4-extract.py system.img /framework/oat work/framework-oat
"""
import os
import struct
import sys

EXT4_MAGIC = 0xEF53
EXTENT_MAGIC = 0xF30A
INCOMPAT_64BIT = 0x80


class Ext4:
    def __init__(self, path):
        self.f = open(path, "rb")
        sb = self._read(1024, 1024)
        if struct.unpack_from("<H", sb, 56)[0] != EXT4_MAGIC:
            raise SystemExit("not an ext4 image")
        self.inodes_count = struct.unpack_from("<I", sb, 0)[0]
        self.blocks_count = struct.unpack_from("<I", sb, 4)[0]
        self.first_data_block = struct.unpack_from("<I", sb, 20)[0]
        self.block_size = 1024 << struct.unpack_from("<I", sb, 24)[0]
        self.blocks_per_group = struct.unpack_from("<I", sb, 32)[0]
        self.inodes_per_group = struct.unpack_from("<I", sb, 40)[0]
        self.inode_size = struct.unpack_from("<H", sb, 88)[0]
        self.incompat = struct.unpack_from("<I", sb, 96)[0]
        self.desc_size = 64 if self.incompat & INCOMPAT_64BIT else 32
        self.gd_start = (self.first_data_block + 1) * self.block_size
        self._inode_tables = {}

    def _read(self, off, n):
        self.f.seek(off)
        d = self.f.read(n)
        if len(d) != n:
            raise SystemExit(f"short read at {off}: {len(d)} != {n}")
        return d

    def _inode_table(self, group):
        if group not in self._inode_tables:
            gd = self._read(self.gd_start + group * self.desc_size, self.desc_size)
            self._inode_tables[group] = struct.unpack_from("<I", gd, 8)[0]
        return self._inode_tables[group]

    def inode(self, ino):
        group, idx = divmod(ino - 1, self.inodes_per_group)
        off = self._inode_table(group) * self.block_size + idx * self.inode_size
        raw = self._read(off, self.inode_size)
        mode = struct.unpack_from("<H", raw, 0)[0]
        size = struct.unpack_from("<I", raw, 4)[0] | (struct.unpack_from("<I", raw, 108)[0] << 32)
        flags = struct.unpack_from("<I", raw, 32)[0]
        return {"mode": mode, "size": size, "flags": flags, "block": raw[40:100]}

    def _extents(self, node, out):
        magic, entries, _max, depth = struct.unpack_from("<HHHH", node, 0)
        if magic != EXTENT_MAGIC:
            raise SystemExit("inode is not extent-based")
        for i in range(entries):
            off = 12 + i * 12
            if depth == 0:
                lblk, ln, hi, lo = struct.unpack_from("<IHHI", node, off)
                out.append((lblk, ln & 0x7FFF, (hi << 32) | lo))
            else:
                _lblk, lo, hi, _ = struct.unpack_from("<IIHH", node, off)
                child = self._read(((hi << 32) | lo) * self.block_size, self.block_size)
                self._extents(child, out)

    def read_file(self, ino):
        inode = self.inode(ino)
        extents = []
        self._extents(inode["block"], extents)
        data = bytearray()
        for _lblk, length, start in sorted(extents):
            data += self._read(start * self.block_size, length * self.block_size)
        return bytes(data[: inode["size"]])

    def listdir(self, ino):
        data = self.read_file(ino)
        out = {}
        pos = 0
        while pos + 8 <= len(data):
            child, rec_len, name_len, _ftype = struct.unpack_from("<IHBB", data, pos)
            if rec_len < 8:
                break
            name = data[pos + 8: pos + 8 + name_len].decode("utf-8", "replace")
            if child and name not in (".", ".."):
                out[name] = child
            pos += rec_len
        return out

    def lookup(self, path):
        ino = 2
        for part in [p for p in path.split("/") if p]:
            entries = self.listdir(ino)
            if part not in entries:
                raise SystemExit(f"not found in image: {path} (missing {part})")
            ino = entries[part]
        return ino


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    img, inner, dest = sys.argv[1], sys.argv[2], sys.argv[3]
    fs = Ext4(img)
    ino = fs.lookup(inner)
    node = fs.inode(ino)
    is_dir = (node["mode"] & 0xF000) == 0x4000
    if not is_dir:
        os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
        with open(dest, "wb") as fh:
            fh.write(fs.read_file(ino))
        print("wrote", dest, node["size"])
        return 0

    total = 0
    stack = [(ino, dest)]
    while stack:
        cur_ino, cur_dest = stack.pop()
        os.makedirs(cur_dest, exist_ok=True)
        for name, child in sorted(fs.listdir(cur_ino).items()):
            child_node = fs.inode(child)
            out = os.path.join(cur_dest, name)
            if (child_node["mode"] & 0xF000) == 0x4000:
                stack.append((child, out))
                continue
            with open(out, "wb") as fh:
                fh.write(fs.read_file(child))
            total += 1
            print(f"  {out} {child_node['size']}")
    print(f"extracted {total} files into {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
