#!/usr/bin/env python
"""Crop the 4K Frame_*.png wallpapers to 480x800 portrait for SM-G355HN.

Centre-crops each frame to the 480:800 aspect ratio, then resizes with
LANCZOS. Output goes to branding/wallpapers/ as both PNG and a compressed
JPEG, because the device has limited /system space and JPEG is far smaller.
"""
import os
import glob
from PIL import Image

W, H = 480, 800
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "branding", "wallpapers")
os.makedirs(OUT, exist_ok=True)

target_ratio = W / H

for src in sorted(glob.glob(os.path.join(ROOT, "Frame_*.png"))):
    im = Image.open(src).convert("RGB")
    sw, sh = im.size
    src_ratio = sw / sh

    if src_ratio > target_ratio:
        new_w = int(round(sh * target_ratio))
        left = (sw - new_w) // 2
        box = (left, 0, left + new_w, sh)
    else:
        new_h = int(round(sw / target_ratio))
        top = (sh - new_h) // 2
        box = (0, top, sw, top + new_h)

    crop = im.crop(box).resize((W, H), Image.LANCZOS)
    name = os.path.splitext(os.path.basename(src))[0].lower()
    png = os.path.join(OUT, name + "_480x800.png")
    jpg = os.path.join(OUT, name + "_480x800.jpg")
    crop.save(png, optimize=True)
    crop.save(jpg, quality=88, optimize=True)
    print("%-12s %s -> %s  png=%dB jpg=%dB"
          % (name, (sw, sh), box, os.path.getsize(png), os.path.getsize(jpg)))
