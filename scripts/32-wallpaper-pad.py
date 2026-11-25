"""KitKat's wallpaper service wants 800x800 (scrollable). Pad the 480x800 source to 800x800:
centre stays the original frame (what the screen shows unscrolled); sides replicate the edge."""
import os, sys
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1] if len(sys.argv) > 1 else "frame_6"
TW = int(sys.argv[2]) if len(sys.argv) > 2 else 800   # target width: 800 on KitKat, 960 on LineageOS 13
PAD = (TW - 480) // 2
OUTNAME = sys.argv[3] if len(sys.argv) > 3 else "wallpaper_800.jpg"
im = Image.open(f"{ROOT}/branding/wallpapers/{src}_480x800.png").convert("RGB")
out = Image.new("RGB", (TW, 800))
out.paste(im, (PAD, 0))
out.paste(im.crop((0, 0, 1, 800)).resize((PAD, 800)), (0, 0))
out.paste(im.crop((479, 0, 480, 800)).resize((PAD, 800)), (PAD + 480, 0))
p = f"{ROOT}/branding/boot/{OUTNAME}"
out.save(p, quality=92); print(p, os.path.getsize(p))
