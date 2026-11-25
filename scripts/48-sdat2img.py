"""Convert an OTA system.new.dat + system.transfer.list pair into a raw ext4 image.

Only needed to recover files that exist in the ROM zip but not on the device (the
framework odex files, for instance). Version 3 transfer lists put the block ranges in a
single comma-separated field, which is why a naive whitespace split fails.

Usage: python scripts/48-sdat2img.py <rom.zip> <out.img>
"""
import os
import sys
import zipfile

BLOCK = 4096


def parse(transfer_list):
    """v3 commands are `new <n> <start>,<end>,...` where n counts the following values and
    each start/end pair is a half-open block range (end exclusive)."""
    lines = [l.strip() for l in transfer_list.decode().splitlines() if l.strip()]
    version = int(lines[0])
    cmds = []
    for line in lines[3:]:
        parts = line.split(None, 1)
        if len(parts) != 2 or parts[0] not in ("new", "zero", "erase"):
            continue
        nums = [int(x) for x in parts[1].replace(",", " ").split()]
        count, ranges = nums[0], nums[1:]
        if count != len(ranges) or len(ranges) % 2:
            raise SystemExit(f"bad {parts[0]} command: count={count} values={len(ranges)}")
        cmds.append((parts[0], [(ranges[i], ranges[i + 1]) for i in range(0, len(ranges), 2)]))
    return version, cmds


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    rom, out = sys.argv[1], sys.argv[2]
    with zipfile.ZipFile(rom) as z:
        version, cmds = parse(z.read("system.transfer.list"))
        total = sum(e - s for _, rs in cmds for s, e in rs)
        print(f"transfer list v{version}, {len(cmds)} commands, {total} blocks")
        with z.open("system.new.dat") as dat, open(out, "wb") as f:
            f.truncate(total * BLOCK)
            for cmd, rs in cmds:
                for start, end in rs:
                    n = (end - start) * BLOCK
                    # Commands are grouped by type, not by position, so every range is
                    # written at its own block offset instead of sequentially.
                    f.seek(start * BLOCK)
                    if cmd == "new":
                        chunk = dat.read(n)
                        if len(chunk) != n:
                            raise SystemExit(f"short read: wanted {n}, got {len(chunk)}")
                        f.write(chunk)
                    else:
                        f.write(b"\0" * n)
    print(f"wrote {out} {os.path.getsize(out)} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
