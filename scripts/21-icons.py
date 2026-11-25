#!/usr/bin/env python
"""Generate launcher icons from the Manikineko logo.

The source logo is 1056x833 RGBA with a soft drop shadow. It is trimmed to its
opaque bounding box, padded to a square, and exported at the standard density
buckets so the launcher icon is crisp on the 480x800 hdpi panel.
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "logo (1).png")
RES = os.path.join(ROOT, "launcher", "res")

SIZES = {
    "drawable-mdpi": 48,
    "drawable-hdpi": 72,
    "drawable-xhdpi": 96,
    "drawable-xxhdpi": 144,
}

im = Image.open(SRC).convert("RGBA")

# Trim to the visible pixels so the mark fills the icon instead of floating.
bbox = im.split()[3].getbbox()
if bbox:
    im = im.crop(bbox)

w, h = im.size
side = max(w, h)
square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
square.paste(im, ((side - w) // 2, (side - h) // 2), im)

for folder, px in SIZES.items():
    out_dir = os.path.join(RES, folder)
    os.makedirs(out_dir, exist_ok=True)
    icon = square.resize((px, px), Image.LANCZOS)
    path = os.path.join(out_dir, "ic_launcher.png")
    icon.save(path, optimize=True)
    print("%-18s %dx%d  %dB" % (folder, px, px, os.path.getsize(path)))

print("source trimmed to", (w, h), "-> square", (side, side))
