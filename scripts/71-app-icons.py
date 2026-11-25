"""Manikineko icon generator (dark rounded tile + accent glyph, one visual language).

  python -I scripts/71-app-icons.py <res-dir> <glyph>      app launcher icon set (mdpi..xxhdpi ic_launcher.png)
  python -I scripts/71-app-icons.py <res-dir> --pack       launcher icon pack: drawable-nodpi/ic_app_<glyph>.png (192 px)
  python -I scripts/71-app-icons.py <png-path> --sheet     contact sheet of every glyph for a visual check
"""
import math, os, sys
from PIL import Image, ImageDraw

BG, SURF, ACC, TXT = (0x0B, 0x0F, 0x14), (0x1B, 0x24, 0x30), (0x4F, 0xA3, 0xE3), (0xE8, 0xEE, 0xF5)
GLYPHS = ["phone", "contacts", "messages", "clock", "calculator", "camera", "gallery", "settings", "notes", "files", "browser", "store", "torch", "level", "recorder", "calendar", "music", "radio"]


def tile(W):
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, W - 1), radius=W * 0.22, fill=SURF, outline=ACC, width=max(2, W // 32))
    return im, d


def thick_line(d, pts, w, fill):
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill=fill, width=int(w))
    for p in pts:
        d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=fill)


def glyph(d, W, name):
    f = lambda x: W * x
    if name == "notes":
        x0, y0, x1, y1 = f(.28), f(.20), f(.72), f(.80)
        d.rounded_rectangle((x0, y0, x1, y1), radius=f(.04), fill=TXT)
        for i in range(4):
            y = y0 + (y1 - y0) * (0.22 + 0.17 * i)
            d.rounded_rectangle((x0 + f(.05), y, x1 - f(.05 if i < 3 else .17), y + f(.025)), radius=f(.01), fill=SURF)
        d.polygon([(x1 - f(.12), y0), (x1, y0 + f(.12)), (x1 - f(.12), y0 + f(.12))], fill=ACC)
    elif name == "browser":    # globe: ring, meridian ellipse, equator and two parallels
        w = int(f(.05))
        d.ellipse((f(.20), f(.20), f(.80), f(.80)), outline=TXT, width=int(f(.06)))
        d.ellipse((f(.36), f(.20), f(.64), f(.80)), outline=ACC, width=w)
        d.line((f(.20), f(.50), f(.80), f(.50)), fill=ACC, width=w)
        d.line((f(.26), f(.35), f(.74), f(.35)), fill=TXT, width=w // 2 + 1)
        d.line((f(.26), f(.65), f(.74), f(.65)), fill=TXT, width=w // 2 + 1)
    elif name == "torch":      # flashlight: body, head, accent beam
        d.rounded_rectangle((f(.42), f(.40), f(.58), f(.84)), radius=f(.04), fill=TXT)
        d.polygon([(f(.36), f(.18)), (f(.64), f(.18)), (f(.58), f(.40)), (f(.42), f(.40))], fill=TXT)
        for x0, x1 in ((.22, .30), (.46, .54), (.70, .78)):
            thick_line(d, [(f(x0), f(.08)), (f(x1 if x0 != .46 else .50), f(.12))], f(.035), ACC)
    elif name == "level":      # spirit level: bar with window and bubble
        d.rounded_rectangle((f(.14), f(.36), f(.86), f(.64)), radius=f(.07), fill=TXT)
        d.rounded_rectangle((f(.36), f(.43), f(.64), f(.57)), radius=f(.07), fill=SURF)
        d.ellipse((f(.44), f(.44), f(.56), f(.56)), fill=ACC)
        thick_line(d, [(f(.40), f(.45)), (f(.40), f(.55))], f(.012), TXT)
        thick_line(d, [(f(.60), f(.45)), (f(.60), f(.55))], f(.012), TXT)
    elif name == "radio":      # radio set: body, dial, speaker lines, antenna
        d.rounded_rectangle((f(.16), f(.36), f(.84), f(.80)), radius=f(.07), fill=TXT)
        thick_line(d, [(f(.30), f(.36)), (f(.66), f(.16))], f(.035), TXT)
        d.ellipse((f(.58), f(.46), f(.76), f(.64)), fill=ACC)
        for i in range(3):
            y = f(.50 + 0.07 * i)
            d.rounded_rectangle((f(.24), y, f(.48), y + f(.03)), radius=f(.01), fill=SURF)
        d.rounded_rectangle((f(.24), f(.70), f(.76), f(.74)), radius=f(.01), fill=SURF)
    elif name == "recorder":   # microphone
        d.rounded_rectangle((f(.40), f(.16), f(.60), f(.56)), radius=f(.10), fill=TXT)
        d.arc((f(.28), f(.30), f(.72), f(.70)), 0, 180, fill=ACC, width=int(f(.05)))
        thick_line(d, [(f(.50), f(.70)), (f(.50), f(.82))], f(.05), ACC)
        thick_line(d, [(f(.38), f(.82)), (f(.62), f(.82))], f(.05), ACC)
    elif name == "calendar":   # page with header band and day dots
        d.rounded_rectangle((f(.20), f(.22), f(.80), f(.80)), radius=f(.06), fill=TXT)
        d.rounded_rectangle((f(.20), f(.22), f(.80), f(.38)), radius=f(.06), fill=ACC)
        d.rectangle((f(.20), f(.30), f(.80), f(.38)), fill=ACC)
        for r in range(3):
            for c in range(4):
                x, y = f(.28 + 0.12 * c), f(.46 + 0.11 * r)
                d.rounded_rectangle((x, y, x + f(.07), y + f(.07)), radius=f(.015), fill=ACC if (r, c) == (1, 2) else SURF)
    elif name == "music":      # beamed notes
        d.ellipse((f(.22), f(.58), f(.42), f(.76)), fill=TXT)
        d.ellipse((f(.52), f(.52), f(.72), f(.70)), fill=TXT)
        thick_line(d, [(f(.40), f(.67)), (f(.40), f(.26))], f(.05), TXT)
        thick_line(d, [(f(.70), f(.61)), (f(.70), f(.20))], f(.05), TXT)
        d.polygon([(f(.40), f(.26)), (f(.70), f(.20)), (f(.70), f(.32)), (f(.40), f(.38))], fill=ACC)
    elif name == "store":      # shopping bag: body, handle arc, accent down-arrow
        d.rounded_rectangle((f(.24), f(.36), f(.76), f(.80)), radius=f(.05), fill=TXT)
        d.arc((f(.34), f(.18), f(.66), f(.54)), 180, 360, fill=TXT, width=int(f(.05)))
        thick_line(d, [(f(.50), f(.46)), (f(.50), f(.66))], f(.06), ACC)
        d.polygon([(f(.40), f(.60)), (f(.60), f(.60)), (f(.50), f(.72))], fill=ACC)
    elif name == "files":
        d.rounded_rectangle((f(.20), f(.30), f(.80), f(.78)), radius=f(.05), fill=ACC)
        d.rounded_rectangle((f(.20), f(.24), f(.46), f(.40)), radius=f(.04), fill=ACC)
        d.rounded_rectangle((f(.20), f(.38), f(.80), f(.78)), radius=f(.05), fill=TXT)
        d.rounded_rectangle((f(.26), f(.46), f(.74), f(.50)), radius=f(.01), fill=SURF)
    elif name == "phone":      # handset: thick curved body with two earpiece/mouthpiece blobs
        # classic handset: a quarter arc around an upper-right centre, with an ear cap and a mouth cap at its ends
        cx, cy, r = f(.62), f(.38), f(.34)
        pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(180, 89, -6)]
        thick_line(d, pts, f(.13), TXT)
        d.ellipse((f(.19), f(.24), f(.39), f(.50)), fill=ACC)       # ear cap (upper left end)
        d.ellipse((f(.50), f(.61), f(.76), f(.81)), fill=ACC)       # mouth cap (lower right end)
    elif name == "contacts":
        d.ellipse((f(.36), f(.20), f(.64), f(.48)), fill=TXT)
        d.pieslice((f(.22), f(.46), f(.78), f(1.02)), 180, 360, fill=TXT)
        d.ellipse((f(.62), f(.62), f(.80), f(.80)), fill=ACC)
        d.rectangle((f(.69), f(.66), f(.73), f(.76)), fill=SURF)
        d.rectangle((f(.65), f(.70), f(.77), f(.72)), fill=SURF)
    elif name == "messages":
        d.rounded_rectangle((f(.18), f(.22), f(.82), f(.66)), radius=f(.10), fill=TXT)
        d.polygon([(f(.30), f(.64)), (f(.30), f(.82)), (f(.50), f(.64))], fill=TXT)
        for i in range(3):
            cx = f(.34 + 0.16 * i)
            d.ellipse((cx - f(.04), f(.40) - f(.04), cx + f(.04), f(.40) + f(.04)), fill=ACC)
    elif name == "clock":
        d.ellipse((f(.20), f(.20), f(.80), f(.80)), outline=TXT, width=int(f(.07)))
        thick_line(d, [(f(.50), f(.50)), (f(.50), f(.30))], f(.06), ACC)
        thick_line(d, [(f(.50), f(.50)), (f(.64), f(.58))], f(.06), ACC)
        d.ellipse((f(.46), f(.46), f(.54), f(.54)), fill=TXT)
    elif name == "calculator":
        d.rounded_rectangle((f(.24), f(.16), f(.76), f(.84)), radius=f(.06), fill=TXT)
        d.rounded_rectangle((f(.30), f(.22), f(.70), f(.38)), radius=f(.02), fill=SURF)
        for r in range(3):
            for c in range(3):
                x, y = f(.31 + 0.14 * c), f(.46 + 0.12 * r)
                d.rounded_rectangle((x, y, x + f(.10), y + f(.08)), radius=f(.015), fill=ACC if c == 2 else SURF)
    elif name == "camera":
        d.rounded_rectangle((f(.16), f(.32), f(.84), f(.78)), radius=f(.07), fill=TXT)
        d.rounded_rectangle((f(.34), f(.24), f(.50), f(.36)), radius=f(.03), fill=TXT)
        d.ellipse((f(.34), f(.40), f(.66), f(.72)), fill=SURF)
        d.ellipse((f(.40), f(.46), f(.60), f(.66)), fill=ACC)
        d.ellipse((f(.73), f(.38), f(.79), f(.44)), fill=ACC)
    elif name == "gallery":
        d.rounded_rectangle((f(.18), f(.22), f(.82), f(.78)), radius=f(.06), fill=TXT)
        d.polygon([(f(.18), f(.78)), (f(.40), f(.46)), (f(.56), f(.66)), (f(.66), f(.54)), (f(.82), f(.78))], fill=ACC)
        d.ellipse((f(.62), f(.30), f(.74), f(.42)), fill=ACC)
    elif name == "settings":   # gear: 8 teeth around a disc with a hole
        cx = cy = f(.50)
        for i in range(8):                                   # 8 rectangular teeth
            a = math.radians(i * 45)
            ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
            r0, r1, hw = f(.20), f(.33), f(.065)
            d.polygon([(cx + ux * r0 + vx * hw, cy + uy * r0 + vy * hw), (cx + ux * r1 + vx * hw, cy + uy * r1 + vy * hw),
                       (cx + ux * r1 - vx * hw, cy + uy * r1 - vy * hw), (cx + ux * r0 - vx * hw, cy + uy * r0 - vy * hw)], fill=TXT)
        d.ellipse((cx - f(.25), cy - f(.25), cx + f(.25), cy + f(.25)), fill=TXT)
        d.ellipse((cx - f(.10), cy - f(.10), cx + f(.10), cy + f(.10)), fill=SURF)
        d.ellipse((cx - f(.06), cy - f(.06), cx + f(.06), cy + f(.06)), fill=ACC)


def draw(size, name):
    k = 4
    im, d = tile(size * k)
    glyph(d, size * k, name)
    return im.resize((size, size), Image.LANCZOS)


def main():
    a, b = sys.argv[1], sys.argv[2]
    if b == "--sheet":
        sheet = Image.new("RGB", (5 * 150, 2 * 150), BG)
        for i, g in enumerate(GLYPHS):
            ic = draw(128, g)
            sheet.paste(ic, ((i % 5) * 150 + 11, (i // 5) * 150 + 11), ic)
        sheet.save(a); print("sheet", a)
    elif b == "--pack":
        p = os.path.join(a, "drawable-nodpi"); os.makedirs(p, exist_ok=True)
        for g in GLYPHS:
            draw(192, g).save(os.path.join(p, "ic_app_%s.png" % g))
        print("pack:", len(GLYPHS), "icons ->", p)
    else:
        for dpi, s in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144)):
            p = os.path.join(a, "drawable-" + dpi); os.makedirs(p, exist_ok=True)
            draw(s, b).save(os.path.join(p, "ic_launcher.png"))
        print("icons written to", a)


if __name__ == "__main__":
    main()
