"""Build branding/boot/bootanimation.zip (480x800) from the Manikineko logo.
part0: logo fades in + rises slightly (plays once). part1: held frame, loops until boot ends."""
import os, shutil, zipfile
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 480, 800, 20
BG = (0x0B, 0x0F, 0x14)
logo = Image.open(os.path.join(ROOT, "logo (1).png")).convert("RGBA")
lw = 260
logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
try:
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
except OSError:
    font = ImageFont.load_default()

def frame(alpha, dy):
    im = Image.new("RGB", (W, H), BG)
    x, y = (W - logo.width) // 2, 250 + dy
    l = logo.copy(); l.putalpha(l.getchannel("A").point(lambda v: int(v * alpha)))
    im.paste(l, (x, y), l)
    d = ImageDraw.Draw(im)
    text = "MANIKINEKO PHONE"
    tw = d.textlength(text, font=font)
    c = tuple(int(BG[i] + (v - BG[i]) * alpha) for i, v in enumerate((0x7C, 0x8A, 0x9A)))
    d.text(((W - tw) / 2, y + logo.height + 40), text, font=font, fill=c)
    return im

out = os.path.join(ROOT, "branding", "boot", "build")
shutil.rmtree(out, ignore_errors=True)
os.makedirs(out + "/part0"); os.makedirs(out + "/part1")
N = 30
for i in range(N):
    t = i / (N - 1); e = 1 - (1 - t) ** 3
    frame(e, int(24 * (1 - e))).save(f"{out}/part0/{i:04d}.png", optimize=True)
frame(1.0, 0).save(f"{out}/part1/0000.png", optimize=True)
open(out + "/desc.txt", "w", newline="\n").write(f"{W} {H} {FPS}\np 1 0 part0\np 0 0 part1\n")

zp = os.path.join(ROOT, "branding", "boot", "bootanimation.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:   # bootanimation requires STORE
    z.write(out + "/desc.txt", "desc.txt")
    for p in ("part0", "part1"):
        for f in sorted(os.listdir(f"{out}/{p}")):
            z.write(f"{out}/{p}/{f}", f"{p}/{f}")
print(zp, os.path.getsize(zp), "bytes")
