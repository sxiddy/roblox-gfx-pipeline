"""Cut a beat sheet to a video with sound (docs/SUPERIOR_PLAN.md step 7). The same file makes the animatic and the film.
    python tools/animatic.py beats.json            -> <out>_animatic.mp4: one still held per shot, shot label burned in
    python tools/animatic.py beats.json final      -> <out>.mp4: every shot's rendered frames, no labels
    python tools/animatic.py beats.json frame 120  -> <dir>/cut_preview_120.png (one finished film frame, global number)
beats.json, paths relative to its folder, frames are 1-based and local to the shot:
  {"fps": 24, "out": "name", "lut": "film.cube" (optional), "ambience": {"file": ..., "rms": -42},
   "shots": [{"name": "s1", "label": "arrive", "count": 44, "still": "s1/stills/f_0022.png",
              "frames": "s1/frames/f_%04d.png", "first": 1,
              "subs": [{"text": "...", "start": 14, "end": 60}],
              "audio": [{"file": "line.wav", "at": 14, "rms": -17, "lowpass": 0}]}]}
Post per frame: LUT, vignette, grain, subtitle (Montserrat 600 drawn at 4x, soft halo + shadow, 3-frame fade)."""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import film_lut

FONT = os.path.join(ROOT, "library", "fonts", "montserrat", "Montserrat[wght].ttf")
SS = 4; SR = 44100
J = os.path.abspath(sys.argv[1]); D = os.path.dirname(J); B = json.load(open(J)); FPS = B["fps"]
MODE = sys.argv[2] if len(sys.argv) > 2 else "animatic"
P = lambda p: p if os.path.isabs(p) else os.path.join(D, p)
LUT = film_lut.load(P(B["lut"])) if B.get("lut") else None
_cache = {}


def sub_layers(text, w, h, size=0.05, y=0.905, weight=600):
    key = (text, w, h, size, y)
    if key in _cache:
        return _cache[key]
    W, H = w * SS, h * SS
    f = ImageFont.truetype(FONT, int(h * size * SS)); f.set_variation_by_axes([weight])
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    box = d.textbbox((0, 0), text, font=f); tw = box[2] - box[0]
    d.text(((W - tw) / 2 - box[0], H * y - box[3]), text, font=f, fill=255)
    px = h / 540.0 * SS
    halo = m.filter(ImageFilter.MaxFilter(2 * int(1.2 * px) + 1)).filter(ImageFilter.GaussianBlur(1.0 * px))
    drop = Image.new("L", (W, H), 0); drop.paste(m.filter(ImageFilter.GaussianBlur(3.5 * px)), (0, int(2 * px)))
    pool = m.filter(ImageFilter.MaxFilter(2 * int(5 * px) + 1)).filter(ImageFilter.GaussianBlur(22 * px))
    sh = np.maximum.reduce([np.asarray(halo, np.float32) * 0.85, np.asarray(drop, np.float32) * 0.7,
                            np.asarray(pool, np.float32) * 0.42])
    sh = Image.fromarray(sh.clip(0, 255).astype(np.uint8)).resize((w, h), Image.LANCZOS)
    _cache[key] = (np.asarray(m.resize((w, h), Image.LANCZOS), np.float32)[..., None] / 255, np.asarray(sh, np.float32)[..., None] / 255)
    return _cache[key]


def text_on(im, text, t=1.0, **kw):
    a, s = sub_layers(text, im.shape[1], im.shape[0], **kw)
    im = im * (1 - s * t)
    return im * (1 - a * t) + np.array([246, 244, 238], np.float32) * a * t


def timeline():
    """[(global frame, shot, local frame)]"""
    out = []; g = 1
    for sh in B["shots"]:
        for i in range(1, sh["count"] + 1):
            out.append((g, sh, i)); g += 1
    return out


def frame(g, sh, i, final):
    src = P(sh["frames"] % (sh.get("first", 1) + i - 1)) if final else P(sh["still"])
    im = np.asarray(Image.open(src).convert("RGB"), np.float32)
    h, w = im.shape[:2]
    if LUT is not None:
        im = film_lut.apply(im / 255, LUT) * 255
    yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) / 1.414
    im = im * (1 - 0.38 * r ** 2.2)[..., None]
    im += np.random.default_rng(g).normal(0, 0.013 * 255, (h, w, 1))
    for sb in sh.get("subs", []):
        t = min(1.0, (i - sb["start"] + 1) / 3.0, (sb["end"] - i + 1) / 3.0)
        if t > 0:
            im = text_on(im, sb["text"], t)
    if not final:
        im = text_on(im, f'{sh["name"]}  {sh.get("label", "")}  {sh["count"] / FPS:.1f} s', size=0.035, y=0.09, weight=500)
    return Image.fromarray(im.clip(0, 255).astype(np.uint8))


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def mix(total):
    from scipy.signal import butter, lfilter
    db = lambda v: 10 ** (v / 20.0)
    norm = lambda x, v: x / max(1e-9, np.sqrt(np.mean(x ** 2))) * db(v)
    out = np.zeros(int(total / FPS * SR) + SR // 2)
    amb = B.get("ambience")
    if amb:
        x = decode(P(amb["file"])); x = np.tile(x, len(out) // len(x) + 1)[:len(out)]
        out += norm(x, amb.get("rms", -42))
    g0 = 0
    for sh in B["shots"]:
        for au in sh.get("audio", []):
            x = decode(P(au["file"]))
            if au.get("lowpass"):
                b, a = butter(2, au["lowpass"] / (SR / 2), "low"); x = lfilter(b, a, x)
            x = norm(x, au.get("rms", -17)); s = int((g0 + au["at"] - 1) / FPS * SR); n = min(len(x), len(out) - s)
            out[s:s + n] += x[:n]
        g0 += sh["count"]
    fade = int(0.4 * SR); out[-fade:] *= np.linspace(1, 0, fade); out[:fade // 4] *= np.linspace(0, 1, fade // 4)
    out = np.tanh(out / db(-1.0)) * db(-1.0)
    path = os.path.join(D, B["out"] + "_mix.wav")
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
    return path


if MODE == "frame":
    g = int(sys.argv[3]); _, sh, i = timeline()[g - 1]
    p = os.path.join(D, f"cut_preview_{g}.png"); frame(g, sh, i, True).save(p); print("SAVED", p, sh["name"], i)
else:
    final = MODE == "final"; tl = timeline()
    tmp = os.path.join(D, "cut_final" if final else "cut_animatic"); os.makedirs(tmp, exist_ok=True)
    for old in os.listdir(tmp):
        os.remove(os.path.join(tmp, old))
    for g, sh, i in tl:
        frame(g, sh, i, final).save(os.path.join(tmp, f"{g:04d}.png"))
    wav = mix(len(tl)); mp4 = os.path.join(D, B["out"] + ("" if final else "_animatic") + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%04d.png"), "-i", wav,
                    "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", mp4], check=True)
    print("WROTE", mp4, len(tl), "frames", round(len(tl) / FPS, 2), "s")
