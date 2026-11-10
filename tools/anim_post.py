"""Post for anim_door: styled subtitles + vignette on every frame (Pillow), synthesized sound (numpy/scipy),
then ffmpeg to H.264 mp4. Usage: python tools/anim_post.py [preview_frame]"""
import os, sys, glob, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.io import wavfile
from scipy.signal import butter, lfilter

ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
D = os.path.join(ROOT, "gfx_output", "anim_door")
FPS, N = 24, 360
FONT = os.path.join(ROOT, "library", "fonts", "montserrat", "Montserrat[wght].ttf")
FONT_I = os.path.join(ROOT, "library", "fonts", "montserrat", "Montserrat-Italic[wght].ttf")

# (start, end, speaker or None for a sound caption, text)
LINES = [(74, 114, None, "knock  ·  knock  ·  knock"),
         (130, 156, None, "the door creaks open"),
         (166, 216, "SUHAA", "Are you Bio?"),
         (220, 264, "BIO", "Yeah. That's me."),
         (266, 298, "SUHAA", "Aww, come on in!"),
         (342, 359, None, "door closes")]
COL = {"BIO": (245, 184, 46), "SUHAA": (244, 166, 196)}


def font(path, size, weight):
    f = ImageFont.truetype(path, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def fade(f, a, b, n=6):
    return max(0.0, min(1.0, (f - a) / n, (b - f) / n))


def subtitle(img, f):
    W, H = img.size; s = W / 1920
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for a, b, who, text in LINES:
        if not (a <= f <= b):
            continue
        t = fade(f, a, b); rise = int((1 - t) * 14 * s)
        d = ImageDraw.Draw(layer)
        if who is None:  # sound caption: small italic, soft grey, no box
            fi = font(FONT_I, int(34 * s), 500)
            w = d.textlength(text, font=fi); x = (W - w) / 2; y = H - 120 * s + rise
            sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((x, y + 2 * s), text, font=fi, fill=(0, 0, 0, int(200 * t)))
            layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4 * s)))
            d.text((x, y), text, font=fi, fill=(225, 225, 235, int(235 * t)))
            continue
        fm = font(FONT, int(50 * s), 650); fn = font(FONT, int(24 * s), 800)
        tw = d.textlength(text, font=fm); pad = 34 * s
        bw, bh = tw + 2 * pad, 96 * s
        x0 = (W - bw) / 2; y0 = H - 170 * s + rise
        # soft drop shadow, frosted dark pill, speaker-coloured accent bar and name chip
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 8 * s, x0 + bw, y0 + bh + 8 * s), radius=bh / 2, fill=(0, 0, 0, int(150 * t)))
        layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14 * s)))
        d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=bh / 2, fill=(14, 12, 20, int(200 * t)))
        c = COL[who]
        d.rounded_rectangle((x0 + 18 * s, y0 + bh - 9 * s, x0 + bw - 18 * s, y0 + bh - 4 * s), radius=3 * s, fill=(*c, int(255 * t)))
        nw = d.textlength(who, font=fn) + 30 * s; nx = (W - nw) / 2; ny = y0 - 22 * s
        d.rounded_rectangle((nx, ny, nx + nw, ny + 40 * s), radius=20 * s, fill=(*c, int(255 * t)))
        d.text((nx + 15 * s, ny + 7 * s), who, font=fn, fill=(20, 14, 20, int(255 * t)))
        d.text((x0 + pad, y0 + 18 * s), text, font=fm, fill=(255, 255, 255, int(255 * t)))
    # title card at the start
    if f < 60:
        t = fade(f, 4, 60, 10); d = ImageDraw.Draw(layer)
        ft = font(FONT, int(30 * s), 700); fs = font(FONT, int(20 * s), 500)
        d.text((60 * s, 50 * s), "BIO_ISHERE  ×  SUHAA_OFFICIAL", font=ft, fill=(255, 255, 255, int(230 * t)))
        d.text((60 * s, 92 * s), "late night visit", font=fs, fill=(244, 166, 196, int(230 * t)))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def vignette(size, strength=0.35):
    W, H = size; y, x = np.mgrid[0:H, 0:W]
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
    return (1 - strength * np.clip(r, 0, 1) ** 2.2)[..., None]


# ---------------------------------------------------------------- sound
SR = 48000


def env(n, decay):
    return np.exp(-np.arange(n) / (decay * SR))


def bp(x, lo, hi):
    b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], "band"); return lfilter(b, a, x)


def knock(rng):
    n = int(0.25 * SR); t = np.arange(n) / SR
    body = sum(a * np.sin(2 * math.pi * fr * t) for fr, a in ((165, 1.0), (330, 0.5), (690, 0.25))) * env(n, 0.045)
    click = bp(rng.standard_normal(n), 900, 4000) * env(n, 0.006) * 0.6
    return (body + click) * 0.8


def step(rng, vol):
    n = int(0.18 * SR)
    return bp(rng.standard_normal(n), 120, 1500) * env(n, 0.03) * vol


def creak(dur, rng):
    n = int(dur * SR); t = np.arange(n) / SR
    fr = 260 + 120 * np.sin(2 * math.pi * 0.9 * t) + 40 * rng.standard_normal(n).cumsum() / math.sqrt(n)
    ph = np.cumsum(fr) / SR
    saw = 2 * (ph % 1) - 1
    am = 0.5 + 0.5 * np.abs(np.sin(2 * math.pi * 7 * t))
    return bp(saw * am, 300, 2500) * np.minimum(1, np.minimum(t / 0.1, (dur - t) / 0.2)) * 0.35


def thud(rng):
    n = int(0.5 * SR); t = np.arange(n) / SR
    return (np.sin(2 * math.pi * 70 * t) * env(n, 0.09) + knock(rng)[:n] * 0.5 if n <= int(0.25 * SR) else
            np.sin(2 * math.pi * 70 * t) * env(n, 0.09)) * 1.0


def audio(path):
    rng = np.random.default_rng(4); L = int(N / FPS * SR) + SR; out = np.zeros(L)

    def put(x, frame, gain=1.0):
        i = int(frame / FPS * SR); out[i:i + len(x)] += x[:max(0, L - i)] * gain
    # night ambience: wind bed + crickets
    out += bp(rng.standard_normal(L), 80, 400) * 0.03
    t = np.arange(L) / SR
    for k in range(6):
        f0 = rng.uniform(4200, 5200); rate = rng.uniform(2.5, 4.5); ph = rng.uniform(0, 6)
        chirp = np.sin(2 * math.pi * f0 * t) * (np.sin(2 * math.pi * 30 * t) > 0) * (np.sin(2 * math.pi * rate * t + ph) > 0.6)
        out += chirp * 0.006
    for f in range(4, 56, 9):    put(step(rng, 0.35), f)        # Bio's swagger steps on the porch
    for f in range(100, 127, 6): put(step(rng, 0.14), f)        # Suhaa inside, muffled
    for f in range(154, 166, 6): put(step(rng, 0.18), f)
    for f in range(286, 298, 6): put(step(rng, 0.16), f)
    for f in range(300, 338, 9): put(step(rng, 0.3), f)
    for f in (82, 92, 102):      put(knock(rng), f)
    put(creak(0.9, rng), 132)
    put(creak(0.6, rng), 338, 0.6)
    put(thud(rng), 352); put(knock(rng), 352, 0.5)
    out = out[:int(N / FPS * SR)]
    out = out / max(1e-6, np.abs(out).max()) * 0.85
    wavfile.write(path, SR, (out * 32767).astype(np.int16))


def main():
    frames = sorted(glob.glob(os.path.join(D, "frames", "*.png")))
    if len(sys.argv) > 1:  # preview one frame
        f = int(sys.argv[1]); im = Image.open(os.path.join(D, "frames", f"{f:04d}.png")) if os.path.exists(os.path.join(D, "frames", f"{f:04d}.png")) \
            else Image.open(os.path.join(D, "stills", f"{f:04d}.png")).resize((1920, 1080))
        v = vignette(im.size); im = Image.fromarray((np.asarray(im.convert("RGB")) * v).astype(np.uint8))
        subtitle(im, f).save(os.path.join(D, f"sub_preview_{f}.png")); return
    assert len(frames) == N, f"expected {N} frames, found {len(frames)}"
    os.makedirs(os.path.join(D, "sub"), exist_ok=True)
    v = None
    for p in frames:
        f = int(os.path.basename(p)[:4]); im = Image.open(p).convert("RGB")
        v = vignette(im.size) if v is None else v
        im = Image.fromarray((np.asarray(im) * v).astype(np.uint8))
        subtitle(im, f).save(os.path.join(D, "sub", f"{f:04d}.png"))
    audio(os.path.join(D, "audio.wav"))
    out = os.path.join(D, "Bio_x_Suhaa_door.mp4")
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(D, "sub", "%04d.png"), "-i", os.path.join(D, "audio.wav"),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
