"""Synthesize the Manikineko ringtone / notification / alarm as 16-bit mono WAV (no ffmpeg needed).
Soft bell-like timbre: sine + quiet harmonics with exponential decay."""
import math, os, struct, wave
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "branding", "sounds"); os.makedirs(OUT, exist_ok=True)
SR = 22050
N = {"C5":523.25,"D5":587.33,"E5":659.25,"G5":783.99,"A5":880.0,"C6":1046.5,"E6":1318.5,"G4":392.0,"A4":440.0}

def note(freq, dur, vol=0.5, decay=5.0):
    n = int(SR * dur); out = []
    for i in range(n):
        t = i / SR
        env = math.exp(-decay * t) * min(1.0, t / 0.005)          # 5 ms attack, no click
        s = math.sin(2*math.pi*freq*t) + 0.35*math.sin(2*math.pi*2*freq*t) + 0.12*math.sin(2*math.pi*3*freq*t)
        out.append(vol * env * s / 1.47)
    return out

def seq(items, total):
    buf = [0.0] * int(SR * total)
    for start, f, dur, vol, dec in items:
        s = int(start * SR)
        for i, v in enumerate(note(N[f], dur, vol, dec)):
            if s + i < len(buf): buf[s + i] += v
    return buf

def save(name, buf):
    p = os.path.join(OUT, name)
    with wave.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32000)) for v in buf))
    print(name, os.path.getsize(p))

# Ringtone ~8 s: five-note motif (ma-ni-ki-ne-ko) twice, then a pause, loops cleanly.
m = [("C5",.0),("E5",.22),("G5",.44),("E5",.66),("C6",.88)]
items = []
for rep, base in enumerate((0.0, 1.8)):
    for f, t in m: items.append((base + t, f, 1.0, 0.55, 4.0))
    items.append((base + 1.2, "G5", 0.5, 0.35, 6.0))
save("Manikineko_Ring.wav", seq(items, 4.8))
# Notification ~1 s: two soft rising notes.
save("Manikineko_Note.wav", seq([(0.0, "E6", 0.6, 0.5, 7.0), (0.16, "A5", 0.8, 0.5, 6.0)], 1.0))
# Alarm ~5 s: brighter repeating triplet, firmer so it wakes you.
a = []
for k in range(4):
    b = k * 1.25
    a += [(b, "G5", 0.4, 0.8, 5.0), (b + 0.18, "C6", 0.4, 0.8, 5.0), (b + 0.36, "E6", 0.6, 0.8, 4.0)]
save("Manikineko_Alarm.wav", seq(a, 5.0))
