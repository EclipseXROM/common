"""Restore the odex trees that belong to the re-signed APKs.

The ROM ships stripped APKs (no classes.dex inside), so ART can only load them through the
matching .odex. Deleting the oat directories therefore breaks the boot classpath and every
stripped priv-app: "No original dex files found for dex location ...". This script pulls the
oat trees back out of the ROM image for exactly the packages that were re-signed.

Usage: python scripts/50-restore-oat.py <system.img> [--dry-run]
Writes: work/oat-tree/<same relative path>/oat/...
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESIGNED = os.path.join(ROOT, "work", "resigned")
OUT = os.path.join(ROOT, "work", "oat-tree")

sys.argv = [sys.argv[0]] + sys.argv[1:]
exec(open(os.path.join(ROOT, "scripts", "49-ext4-extract.py")).read()
     .replace('if __name__ == "__main__":\n    sys.exit(main())', ''))


def targets():
    out = []
    for dirpath, _, files in os.walk(RESIGNED):
        for f in sorted(files):
            if f.endswith(".apk"):
                rel = os.path.relpath(os.path.join(dirpath, f), RESIGNED).replace("\\", "/")
                out.append(rel)
    return sorted(out)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    img = sys.argv[1]
    dry = "--dry-run" in sys.argv
    fs = Ext4(img)

    rels = targets()
    print(f"re-signed packages: {len(rels)}")
    missing, done = [], 0
    for rel in rels:
        inner = "/" + rel.rsplit("/", 1)[0] + "/oat"
        dest = os.path.join(OUT, rel.rsplit("/", 1)[0].replace("/", os.sep), "oat")
        try:
            ino = fs.lookup(inner)
        except SystemExit:
            missing.append(rel)
            continue
        if dry:
            print("  would restore", inner)
            continue
        stack = [(ino, dest)]
        while stack:
            cur, cur_dest = stack.pop()
            os.makedirs(cur_dest, exist_ok=True)
            for name, child in fs.listdir(cur).items():
                node = fs.inode(child)
                path = os.path.join(cur_dest, name)
                if (node["mode"] & 0xF000) == 0x4000:
                    stack.append((child, path))
                    continue
                with open(path, "wb") as fh:
                    fh.write(fs.read_file(child))
        done += 1
    print(f"restored {done} oat trees, {len(missing)} packages had none")
    for m in missing:
        print("  no oat:", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
