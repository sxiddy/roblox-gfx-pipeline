"""Post for anim_door v2: plain movie subtitles + real recorded SFX, edge-tts voices and night ambience, then ffmpeg.
Reads gfx_output/anim_door_v2/cues.json (written by anim_door.perform) and frames/.
Usage: python tools/anim_post2.py            -> sub/ frames, mix.wav, Bio_x_Suhaa_door_v2.mp4
       python tools/anim_post2.py sub 200    -> one subtitle preview frame
       python tools/anim_post2.py audio      -> mix only
"""
import os, sys, glob, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.signal import butter, lfilter, fftconvolve

ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
D = os.path.join(ROOT, "gfx_output", "anim_door_v2")
SFX = os.path.join(ROOT, "library", "sfx")
FONT = os.path.join(ROOT, "library", "fonts", "montserrat", "Montserrat[wght].ttf")
FONT_I = os.path.join(ROOT, "library", "fonts", "montserrat", "Montserrat-Italic[wght].ttf")
CUES = json.load(open(os.path.join(D, "cues.json")))
FPS, N, SR = CUES["fps"], CUES["frames"], 48000


# ---------------------------------------------------------------- subtitles: white, thin outline, soft shadow, bottom centre
def font(path, size, weight):
    f = ImageFont.truetype(path, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def subtitle(img, f):
    W, H = img.size; s = W / 1920
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for a, b, who, text in CUES["subs"]:
        if not (a <= f <= b):
            continue
        t = max(0.0, min(1.0, (f - a) / 4, (b - f) / 4))
        sfx = who is None
        fn = font(FONT_I if sfx else FONT, int((36 if sfx else 48) * s), 500 if sfx else 600)
        d = ImageDraw.Draw(layer); w = d.textlength(text, font=fn)
        x, y = (W - w) / 2, H - (96 if sfx else 118) * s
        ImageDraw.Draw(shadow).text((x, y + 3 * s), text, font=fn, fill=(0, 0, 0, int(170 * t)))
        d.text((x, y), text, font=fn, fill=(*((222, 222, 228) if sfx else (255, 255, 255)), int(255 * t)),
               stroke_width=max(2, int(2.5 * s)), stroke_fill=(0, 0, 0, int(235 * t)))
    out = img.convert("RGBA")
    out.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(5 * s))); out.alpha_composite(layer)
    return out.convert("RGB")


def vignette(size, strength=0.3):
    W, H = size; y, x = np.mgrid[0:H, 0:W]
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
    return (1 - strength * np.clip(r, 0, 1) ** 2.2)[..., None]


# ---------------------------------------------------------------- audio
def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def sfx(name):
    return load(glob.glob(os.path.join(SFX, "kenney_*", "**", name), recursive=True)[0])


def db(x):
    return 10 ** (x / 20)


def lowpass(x, hz):
    b, a = butter(2, hz / (SR / 2)); return lfilter(b, a, x)


def rms_norm(x, target_db):
    r = np.sqrt(np.mean(x[np.abs(x) > 1e-4] ** 2)) if np.any(np.abs(x) > 1e-4) else 1.0
    return x / r * db(target_db)


def room(x, wet=0.16, decay=0.28, seed=2):
    """A small warm room: short decaying noise impulse, low-passed."""
    rng = np.random.default_rng(seed); n = int(decay * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (decay / 5 * SR)); ir = lowpass(ir, 3500); ir /= np.abs(ir).sum() / 6
    return x * (1 - wet) + fftconvolve(x, ir)[:len(x)] * wet


def mix():
    L = int(N / FPS * SR); out = np.zeros(L)

    def put(x, frame, gain_db=0.0, align_peak=False):
        i = int(frame / FPS * SR) - (int(np.argmax(np.abs(x))) if align_peak else 0)
        i = max(0, i); seg = x[:max(0, L - i)] * db(gain_db); out[i:i + len(seg)] += seg

    cams = CUES["cams"]; inside = (cams["CamOTS"], cams["CamEnd"])
    # night ambience: crickets bed, a bit quieter and duller while the camera is inside the house
    amb = load(os.path.join(SFX, "ambience", "crickets_40s.wav"))[:L]
    env = np.ones(L); a0, a1 = (int(f / FPS * SR) for f in inside)
    ramp = int(0.25 * SR); env[a0:a1] = db(-6); env[a0 - ramp:a0] = np.linspace(1, db(-6), ramp); env[a1:a1 + ramp] = np.linspace(db(-6), 1, ramp)
    out += rms_norm(amb, -34) * env
    # footsteps: concrete porch for Bio (round robin), soft carpet inside for Suhaa
    porch = [sfx(n) for n in ("footstep04.ogg", "footstep06.ogg", "footstep09.ogg")]
    carpet = [lowpass(sfx(n), 2500) for n in ("footstep_carpet_003.ogg", "footstep_carpet_004.ogg")]
    for i, f in enumerate(CUES["steps_bio_out"]):
        put(rms_norm(porch[i % 3], -30), f, align_peak=True)
    for i, f in enumerate(CUES["steps_bio_in"]):
        put(rms_norm((porch[i % 3] if i < 2 else carpet[i % 2]), -31), f, align_peak=True)
    for i, f in enumerate(CUES["steps_suhaa"]):
        put(rms_norm(carpet[i % 2], -33), f, align_peak=True)
    # knocks: three different wood takes so they don't sound copy-pasted
    for f, n in zip(CUES["knocks"], ("impactWood_medium_002.ogg", "impactWood_medium_003.ogg", "impactWood_medium_001.ogg")):
        put(rms_norm(sfx(n), -21), f, align_peak=True)
    # door: latch + creak while it swings open; slam lands exactly when it shuts
    put(rms_norm(lowpass(sfx("doorOpen_1.ogg"), 5000), -25), CUES["door_open"])
    put(rms_norm(lowpass(sfx("creak1.ogg"), 4000), -24), CUES["door_open"] + 4)
    put(rms_norm(lowpass(sfx("doorClose_1.ogg"), 4500), -20), CUES["door_shut"], align_peak=True)
    put(rms_norm(lowpass(sfx("doorClose_4.ogg"), 900), -17), CUES["door_shut"], align_peak=True)  # body thud under the click
    # voices: Bio outside (dry), Suhaa inside (small warm room); dialogue sits on top
    for k in ("ask", "bio", "come"):
        v = load(os.path.join(D, "voice", k + ".wav")); b, a = butter(2, 90 / (SR / 2), "high"); v = lfilter(b, a, v)
        v = room(v) if k != "bio" else v
        put(rms_norm(v, -17), CUES["voice"][k])
    # loudness: bring the speech-led mix up to about -16 LUFS, then a soft clip keeps peaks under -1 dBFS
    out = out / max(1e-6, np.sqrt(np.mean(out ** 2))) * db(-19)
    out = np.tanh(out / db(-1.0) * 1.0) * db(-1.0)
    path = os.path.join(D, "mix.wav")
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
    return path


def main():
    if sys.argv[1:2] == ["sub"]:
        f = int(sys.argv[2]); p = os.path.join(D, "frames", f"{f:04d}.png")
        im = Image.open(p if os.path.exists(p) else os.path.join(D, "stills", f"{f:04d}.png")).convert("RGB").resize((1920, 1080))
        subtitle(im, f).save(os.path.join(D, f"sub_preview_{f}.png")); return
    if sys.argv[1:2] == ["audio"]:
        print(mix()); return
    frames = sorted(glob.glob(os.path.join(D, "frames", "*.png")))
    assert len(frames) == N, f"expected {N} frames, found {len(frames)}"
    os.makedirs(os.path.join(D, "sub"), exist_ok=True); v = None
    for p in frames:
        f = int(os.path.basename(p)[:4]); im = Image.open(p).convert("RGB")
        v = vignette(im.size) if v is None else v
        im = Image.fromarray((np.asarray(im) * v).astype(np.uint8))
        subtitle(im, f).save(os.path.join(D, "sub", f"{f:04d}.png"))
    wav = mix(); out = os.path.join(D, "Bio_x_Suhaa_door_v2.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(D, "sub", "%04d.png"), "-i", wav,
                    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
