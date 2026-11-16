"""Post for the pilot shot: vignette, grain, subtitle, then ffmpeg with the voice.
    python tools/pilot_post.py preview 60     -> post/sub_preview_60.png (old | new side by side if the old frame exists)
    python tools/pilot_post.py all v4         -> post2/f_####.png and Bio_IsHere_pilot_shot_v4.mp4
Subtitle: Montserrat 600, drawn at 4x and scaled down (clean edges at 540p), no hard stroke; a tight dark halo plus a
soft drop shadow and a faint dark pool behind the line keep it readable over the shirt print. Fades over 3 frames."""
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "gfx_output", "Bio_IsHere", "pilot")
FONT = os.path.join(ROOT, "library", "fonts", "montserrat", "Montserrat[wght].ttf")
TEXT = "You really thought I wouldn't show up?"
SUB = (36, 86); FPS = 24; VOICE = 36; END = 110; SS = 4
_cache = {}


def sub_layers(w, h):
    """(text RGBA, shadow L) at frame size, built once."""
    if (w, h) in _cache:
        return _cache[(w, h)]
    W, H = w * SS, h * SS
    f = ImageFont.truetype(FONT, int(h * 0.05 * SS)); f.set_variation_by_axes([600])
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    box = d.textbbox((0, 0), TEXT, font=f); tw = box[2] - box[0]
    d.text(((W - tw) / 2 - box[0], H * 0.905 - box[3]), TEXT, font=f, fill=255)
    px = h / 540.0 * SS
    halo = m.filter(ImageFilter.MaxFilter(2 * int(1.2 * px) + 1)).filter(ImageFilter.GaussianBlur(1.0 * px))
    drop = Image.new("L", (W, H), 0); drop.paste(m.filter(ImageFilter.GaussianBlur(3.5 * px)), (0, int(2 * px)))
    pool = m.filter(ImageFilter.MaxFilter(2 * int(5 * px) + 1)).filter(ImageFilter.GaussianBlur(22 * px))
    sh = np.maximum.reduce([np.asarray(halo, np.float32) * 0.85, np.asarray(drop, np.float32) * 0.7,
                            np.asarray(pool, np.float32) * 0.42])
    sh = Image.fromarray(sh.clip(0, 255).astype(np.uint8)).resize((w, h), Image.LANCZOS)
    _cache[(w, h)] = (m.resize((w, h), Image.LANCZOS), sh)
    return _cache[(w, h)]


def post(f):
    im = np.asarray(Image.open(os.path.join(D, "frames", f"f_{f:04d}.png")).convert("RGB"), np.float32)
    h, w = im.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) / 1.414
    im = im * (1 - 0.38 * r ** 2.2)[..., None]
    im += np.random.default_rng(f).normal(0, 0.013 * 255, (h, w, 1))
    t = min(1.0, (f - SUB[0] + 1) / 3.0, (SUB[1] - f + 1) / 3.0)
    if t > 0:
        txt, sh = sub_layers(w, h)
        s = np.asarray(sh, np.float32)[..., None] / 255 * t; a = np.asarray(txt, np.float32)[..., None] / 255 * t
        im = im * (1 - s)
        im = im * (1 - a) + np.array([246, 244, 238], np.float32) * a
    return Image.fromarray(im.clip(0, 255).astype(np.uint8))


if sys.argv[1] == "preview":
    f = int(sys.argv[2]); new = post(f); old = os.path.join(D, "post", f"f_{f:04d}.png")
    if os.path.exists(old):
        o = Image.open(old).convert("RGB"); c = Image.new("RGB", (new.width, new.height), 0)
        hh = new.height // 2
        c.paste(o.crop((0, hh, o.width, o.height)), (0, 0)); c.paste(new.crop((0, hh, new.width, new.height)), (0, hh))
        new = c
    p = os.path.join(D, "post", f"sub_preview_{f}.png"); new.save(p); print("SAVED", p)
else:
    out = os.path.join(D, "post2"); os.makedirs(out, exist_ok=True)
    for f in range(1, END + 1):
        post(f).save(os.path.join(out, f"f_{f:04d}.png"))
    mp4 = os.path.join(D, f"Bio_IsHere_pilot_shot_{sys.argv[2]}.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(out, "f_%04d.png"),
                    "-itsoffset", f"{(VOICE - 1) / FPS:.4f}", "-i", os.path.join(D, "line.wav"),
                    "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    mp4], check=True)
    print("WROTE", mp4)
