"""2D side of the GFX pipeline: measure a reference, compare a render with it, match its grade, add post effects.

  python gfx2d.py grid    REF OUT.png                      labelled 10x10 grid to read positions as fractions
  python gfx2d.py compare REF RENDER OUTDIR                side.png, blend.png, edges.png + numeric report
  python gfx2d.py grade   REF RENDER OUT.png [--strength 0.8] [--auto] [--bloom 0.3] [--grain 0.03]
                          [--vignette 0.3] [--ca 2] [--mask MASK.png --char-strength 0.3] [--sat 1.3]
                          [--levels black,white] [--sharpen 0.6]
  python gfx2d.py post    RENDER OUT.png [--glow 0.4] [--sparkles 6] [--sparkle-at x,y,size ...]
                          [--leak r,g,b,corner,strength] [--outline MASK --outline-px 8 --outline-color 255,255,255]
                          [--text "TXT" --font anton --text-size 0.12 --text-pos 0.5,0.1 --text-color 255,255,255]
                          [--seed 1] [--dust 25 --dust-box x0,y0,x1,y1]

Positions are fractions of the frame (0,0 = top-left). Run with `python -I`; needs numpy, scipy, Pillow.
"""
import argparse
import glob
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library", "fonts")


# ---------------------------------------------------------------- colour space
def load(path, size=None):
    im = Image.open(path).convert("RGB")
    if size:
        im = fit(im, size)
    return np.asarray(im).astype(np.float32) / 255.0


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def fit(im, size):
    """Centre-crop to the target aspect ratio, then resize."""
    w, h = im.size; tw, th = size
    if w / h > tw / th:
        nw = round(h * tw / th); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = round(w * th / tw); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im.resize(size, Image.LANCZOS)


def to_linear(c):
    c = np.clip(c, 0, None)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(c, 0, None)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
WHITE = np.array([0.95047, 1.0, 1.08883])


def rgb2lab(a):
    xyz = to_linear(a) @ M.T / WHITE
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def lab2rgb(lab):
    fy = (lab[..., 0] + 16) / 116; fx = fy + lab[..., 1] / 500; fz = fy - lab[..., 2] / 200
    f = np.stack([fx, fy, fz], -1)
    xyz = np.where(f > 0.2069, f ** 3, (f - 16 / 116) / 7.787) * WHITE
    return np.clip(to_srgb(xyz @ np.linalg.inv(M).T), 0, 1)


def luma(a):
    return a @ np.array([0.2126, 0.7152, 0.0722])


# ---------------------------------------------------------------- measuring
def grid(src, out):
    im = Image.open(src).convert("RGB"); w, h = im.size
    d = ImageDraw.Draw(im); font = ImageFont.load_default(size=max(12, w // 60))
    for i in range(1, 10):
        x, y = w * i // 10, h * i // 10
        d.line([(x, 0), (x, h)], fill=(255, 0, 80), width=max(1, w // 600))
        d.line([(0, y), (w, y)], fill=(255, 0, 80), width=max(1, w // 600))
        d.text((x + 3, 3), f".{i}", fill=(255, 255, 0), font=font)
        d.text((3, y + 3), f".{i}", fill=(255, 255, 0), font=font)
    im.save(out)


def edges(a):
    g = ndimage.gaussian_filter(luma(a), 1.2)
    mag = np.hypot(ndimage.sobel(g, 0), ndimage.sobel(g, 1))
    return mag > np.percentile(mag, 90)


def stats(a):
    lab = rgb2lab(a); L = lab[..., 0]; h, w = L.shape
    cells = [[float(L[h * r // 3:h * (r + 1) // 3, w * c // 3:w * (c + 1) // 3].mean()) for c in range(3)] for r in range(3)]
    centre = L[h // 4:3 * h // 4, w // 4:3 * w // 4].mean()
    ring = np.concatenate([L[:h // 8].ravel(), L[-h // 8:].ravel(), L[:, :w // 8].ravel(), L[:, -w // 8:].ravel()]).mean()
    hp = luma(a) - ndimage.gaussian_filter(luma(a), 1.0)
    local = np.clip(ndimage.uniform_filter(hp ** 2, 15), 0, None) ** 0.5
    return {
        "L mean": float(L.mean()), "L contrast (std)": float(L.std()),
        "black point L p5": float(np.percentile(L, 5)), "white point L p95": float(np.percentile(L, 95)),
        "tint a (+red/-green)": float(lab[..., 1].mean()), "tint b (+yellow/-blue)": float(lab[..., 2].mean()),
        "saturation (chroma)": float(np.hypot(lab[..., 1], lab[..., 2]).mean()),
        "vignette (centre-edge L)": float(centre - ring), "grain": float(np.percentile(local, 20) * 100),
        "cells": cells,
    }


def compare(ref_path, render_path, outdir):
    os.makedirs(outdir, exist_ok=True)
    r = load(render_path); h, w = r.shape[:2]
    f = load(ref_path, (w, h))
    side = np.concatenate([f, np.ones((h, w // 60, 3)), r], 1)
    save(np.asarray(Image.fromarray((side * 255).astype(np.uint8)).resize((side.shape[1] // 2, h // 2))) / 255, os.path.join(outdir, "side.png"))
    save((f + r) / 2, os.path.join(outdir, "blend.png"))
    ef, er = edges(f), edges(r)
    ov = np.full((h, w, 3), 0.08); ov[ef] = (1, 0.2, 0.2); ov[er] = (0.2, 0.9, 1); ov[ef & er] = (1, 1, 1)
    save(ov, os.path.join(outdir, "edges.png"))
    for name, img in (("ref", f), ("render", r)):
        save(img, os.path.join(outdir, f"_{name}.png")); grid(os.path.join(outdir, f"_{name}.png"), os.path.join(outdir, f"_{name}.png"))
    gl = [Image.open(os.path.join(outdir, f"_{n}.png")) for n in ("ref", "render")]
    sg = Image.new("RGB", (w * 2 + w // 60, h), (255, 255, 255)); sg.paste(gl[0], (0, 0)); sg.paste(gl[1], (w + w // 60, 0))
    sg.resize((sg.width // 2, h // 2)).save(os.path.join(outdir, "side_grid.png"))
    for n in ("ref", "render"):
        os.remove(os.path.join(outdir, f"_{n}.png"))
    df, dr = ndimage.binary_dilation(ef, iterations=4), ndimage.binary_dilation(er, iterations=4)
    sf, sr = stats(f), stats(r)
    lines = [f"structure overlap (edge IoU): {(df & dr).sum() / max(1, (df | dr).sum()):.2f}   (1.0 = same shapes in same places)", ""]
    lines.append(f"{'':28}{'reference':>10}{'render':>10}{'diff':>8}")
    for k in sf:
        if k != "cells":
            lines.append(f"{k:28}{sf[k]:10.1f}{sr[k]:10.1f}{sr[k] - sf[k]:+8.1f}")
    lines += ["", "brightness by region, L (ref -> render):"]
    for row_f, row_r in zip(sf["cells"], sr["cells"]):
        lines.append("   " + "   ".join(f"{a:5.1f}->{b:5.1f}" for a, b in zip(row_f, row_r)))
    bf = int(np.argmax(sf["cells"])); br = int(np.argmax(sr["cells"]))
    names = ["top-left", "top", "top-right", "left", "centre", "right", "bottom-left", "bottom", "bottom-right"]
    lines.append(f"brightest region: reference {names[bf]}, render {names[br]}")
    hints = []
    dL = sr["L mean"] - sf["L mean"]
    if abs(dL) > 4:
        hints.append(f"exposure: render is {dL:+.0f} L; change exposure by about {-dL / 12:+.1f} stop")
    if abs(sr["L contrast (std)"] - sf["L contrast (std)"]) > 4:
        hints.append("contrast: " + ("raise" if sr["L contrast (std)"] < sf["L contrast (std)"] else "lower") + " light ratio / contrast")
    if abs(sr["saturation (chroma)"] - sf["saturation (chroma)"]) > 4:
        hints.append("saturation: " + ("raise" if sr["saturation (chroma)"] < sf["saturation (chroma)"] else "lower"))
    if bf != br:
        hints.append(f"key light: move the brightest area from {names[br]} to {names[bf]}")
    lines += ["", "hints:"] + ["  - " + x for x in hints or ["none above thresholds"]]
    rep = "\n".join(lines)
    open(os.path.join(outdir, "report.txt"), "w").write(rep)
    print(rep)


# ---------------------------------------------------------------- grading
def bloom(a, amount, thresh=0.72):
    lin = to_linear(a); bright = np.clip(lin - thresh, 0, None)
    s = a.shape[1] * 0.015
    glow = sum(ndimage.gaussian_filter(bright, (s * k, s * k, 0)) for k in (1, 3, 8)) / 3
    return to_srgb(lin + glow * amount * 3)


def vignette(a, amount):
    h, w = a.shape[:2]; y, x = np.mgrid[0:h, 0:w]
    r = np.hypot((x - w / 2) / (w / 2), (y - h / 2) / (h / 2)) / np.sqrt(2)
    return a * (1 - amount * np.clip((r - 0.35) / 0.65, 0, 1) ** 1.6)[..., None]


def grain(a, amount, seed=0):
    n = ndimage.gaussian_filter(np.random.default_rng(seed).normal(0, 1, a.shape[:2]), 0.6)
    return a + (n / n.std() * amount)[..., None]


def aberration(a, px):
    h, w = a.shape[:2]; y, x = np.mgrid[0:h, 0:w].astype(np.float32); out = a.copy()
    for ch, k in ((0, px / w), (2, -px / w)):
        out[..., ch] = ndimage.map_coordinates(a[..., ch], [(y - h / 2) * (1 - k) + h / 2, (x - w / 2) * (1 - k) + w / 2], order=1, mode="nearest")
    return out


def grade(ref_path, render_path, out, strength=0.8, auto=False, bloom_amt=0.0, grain_amt=0.0, vig=0.0, ca=0.0,
          mask=None, char_strength=0.3, sat=1.0, levels=None, sharpen=0.0):
    r = load(render_path); h, w = r.shape[:2]; f = load(ref_path, (w, h))
    lr, lf = rgb2lab(r), rgb2lab(f)
    mr, sr_ = lr.reshape(-1, 3).mean(0), lr.reshape(-1, 3).std(0) + 1e-4
    mf, sf_ = lf.reshape(-1, 3).mean(0), lf.reshape(-1, 3).std(0)
    ratio = np.clip(sf_ / sr_, 0.5, 2.0)
    matched = (lr - mr) * ratio + mf
    k = np.full((h, w, 1), strength)
    if mask:  # keep the avatar's own colours (e.g. black hair) mostly intact
        m = np.asarray(Image.open(mask).convert("RGBA").split()[-1].resize((w, h))).astype(np.float32)[..., None] / 255
        k = strength * (1 - m) + char_strength * m
    lo = lr + (matched - lr) * k
    if sat != 1.0:  # extra saturation outside the avatar
        bg = (1 - m) if mask else np.ones((h, w, 1))
        lo[..., 1:] *= 1 + (sat - 1) * bg
    if levels:
        b_, w_ = levels; lo[..., :1] = np.clip((lo[..., :1] - b_) / (w_ - b_) * 100, 0, 100)
    a = lab2rgb(lo)
    if sharpen:
        a = a + sharpen * (a - ndimage.gaussian_filter(a, (1.0, 1.0, 0)))
    if auto:
        s_ref, s_now = stats(f), stats(a)
        vig = max(vig, np.clip((s_ref["vignette (centre-edge L)"] - s_now["vignette (centre-edge L)"]) / 40, 0, 0.7))
        grain_amt = max(grain_amt, np.clip((s_ref["grain"] - s_now["grain"]) / 100, 0, 0.08))
        print(f"auto: vignette {vig:.2f}, grain {grain_amt:.3f}")
    if bloom_amt:
        a = bloom(a, bloom_amt)
    if ca:
        a = aberration(a, ca)
    if vig:
        a = vignette(a, vig)
    if grain_amt:
        a = grain(a, grain_amt)
    save(a, out)


# ---------------------------------------------------------------- post effects
def sparkle(img, x, y, size, color=(255, 255, 255)):
    """Four-point star with a soft glow, drawn on a separate layer and screened on."""
    w, h = img.size; L = Image.new("RGB", img.size); d = ImageDraw.Draw(L)
    s = size * w; t = s * 0.13; cx, cy = x * w, y * h
    d.polygon([(cx, cy - s), (cx + t, cy - t), (cx + s, cy), (cx + t, cy + t), (cx, cy + s), (cx - t, cy + t), (cx - s, cy), (cx - t, cy - t)], fill=color)
    a = np.asarray(L).astype(np.float32) / 255
    a = a + ndimage.gaussian_filter(a, (s * 0.25, s * 0.25, 0)) * 1.5
    base = np.asarray(img).astype(np.float32) / 255
    return Image.fromarray((np.clip(1 - (1 - base) * (1 - np.clip(a, 0, 1)), 0, 1) * 255).astype(np.uint8))


def leak(a, color, corner, strength):
    h, w = a.shape[:2]; y, x = np.mgrid[0:h, 0:w]
    cx, cy = {"tl": (0, 0), "tr": (w, 0), "bl": (0, h), "br": (w, h)}[corner]
    g = np.clip(1 - np.hypot(x - cx, y - cy) / (0.9 * max(w, h)), 0, 1) ** 2 * strength
    c = np.array(color) / 255
    return 1 - (1 - a) * (1 - g[..., None] * c)


def font_path(name):
    hits = glob.glob(os.path.join(FONTS, name, "*.ttf"))
    if not hits:
        raise SystemExit(f"font '{name}' not found; have: {', '.join(sorted(os.listdir(FONTS)))}")
    return hits[0]


def post(src, out, glow=0.0, sparkles=0, sparkle_at=(), leak_spec=None, outline=None, outline_px=8,
         outline_color=(255, 255, 255), text=None, font="anton", text_size=0.12, text_pos=(0.5, 0.1),
         text_color=(255, 255, 255), seed=1, dust=0, dust_box=(0, 0, 1, 1)):
    a = load(src); h, w = a.shape[:2]
    if outline:
        m = np.asarray(Image.open(outline).convert("RGBA").split()[-1].resize((w, h))) > 127
        ring = ndimage.binary_dilation(m, iterations=outline_px) & ~m
        soft = ndimage.gaussian_filter(ring.astype(np.float32), 1.0)[..., None]
        a = a * (1 - soft) + np.array(outline_color) / 255 * soft
    if glow:
        a = bloom(a, glow, 0.6)
    if leak_spec:
        p = leak_spec.split(","); a = leak(a, tuple(map(float, p[:3])), p[3], float(p[4]))
    img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    rng = np.random.default_rng(seed)
    spots = [tuple(map(float, s.split(","))) for s in sparkle_at]
    spots += [(rng.uniform(0.08, 0.92), rng.uniform(0.08, 0.6), rng.uniform(0.012, 0.035)) for _ in range(sparkles)]
    for x, y, s in spots:
        img = sparkle(img, x, y, s)
    if dust:  # tiny soft floating specks
        L = np.zeros((h, w), np.float32); x0, y0, x1, y1 = dust_box
        for _ in range(dust):
            cx, cy = int(rng.uniform(x0, x1) * w), int(rng.uniform(y0, y1) * h); r = rng.uniform(1, 2.5)
            yy, xx = np.ogrid[-4:5, -4:5]; blob = np.exp(-(xx ** 2 + yy ** 2) / (2 * r * r)) * rng.uniform(0.6, 0.9)
            L[max(cy - 4, 0):cy + 5, max(cx - 4, 0):cx + 5] += blob[max(4 - cy, 0):9 - max(cy + 5 - h, 0), max(4 - cx, 0):9 - max(cx + 5 - w, 0)]
        L = ndimage.gaussian_filter(L, 0.6)[..., None]
        base = np.asarray(img).astype(np.float32) / 255
        img = Image.fromarray((np.clip(1 - (1 - base) * (1 - np.clip(L, 0, 1)), 0, 1) * 255).astype(np.uint8))
    if text:
        d = ImageDraw.Draw(img); f = ImageFont.truetype(font_path(font), int(text_size * h))
        d.text((text_pos[0] * w, text_pos[1] * h), text, font=f, fill=tuple(text_color), anchor="mm",
               stroke_width=max(2, int(text_size * h * 0.06)), stroke_fill=(0, 0, 0))
    img.save(out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("grid"); g.add_argument("src"); g.add_argument("out")
    c = sub.add_parser("compare"); c.add_argument("ref"); c.add_argument("render"); c.add_argument("outdir")
    gr = sub.add_parser("grade"); gr.add_argument("ref"); gr.add_argument("render"); gr.add_argument("out")
    gr.add_argument("--strength", type=float, default=0.8); gr.add_argument("--auto", action="store_true")
    gr.add_argument("--bloom", type=float, default=0); gr.add_argument("--grain", type=float, default=0)
    gr.add_argument("--vignette", type=float, default=0); gr.add_argument("--ca", type=float, default=0)
    gr.add_argument("--mask"); gr.add_argument("--char-strength", type=float, default=0.3)
    gr.add_argument("--sat", type=float, default=1.0); gr.add_argument("--levels")
    gr.add_argument("--sharpen", type=float, default=0.0)
    po = sub.add_parser("post"); po.add_argument("src"); po.add_argument("out")
    po.add_argument("--glow", type=float, default=0); po.add_argument("--sparkles", type=int, default=0)
    po.add_argument("--sparkle-at", nargs="*", default=[]); po.add_argument("--leak")
    po.add_argument("--outline"); po.add_argument("--outline-px", type=int, default=8)
    po.add_argument("--outline-color", default="255,255,255"); po.add_argument("--text")
    po.add_argument("--font", default="anton"); po.add_argument("--text-size", type=float, default=0.12)
    po.add_argument("--text-pos", default="0.5,0.1"); po.add_argument("--text-color", default="255,255,255")
    po.add_argument("--seed", type=int, default=1); po.add_argument("--dust", type=int, default=0)
    po.add_argument("--dust-box", default="0,0,1,1")
    a = p.parse_args()
    if a.cmd == "grid":
        grid(a.src, a.out)
    elif a.cmd == "compare":
        compare(a.ref, a.render, a.outdir)
    elif a.cmd == "grade":
        grade(a.ref, a.render, a.out, a.strength, a.auto, a.bloom, a.grain, a.vignette, a.ca, a.mask, a.char_strength,
              a.sat, tuple(map(float, a.levels.split(","))) if a.levels else None, a.sharpen)
    else:
        rgb = lambda s: tuple(int(v) for v in s.split(","))
        post(a.src, a.out, a.glow, a.sparkles, a.sparkle_at, a.leak, a.outline, a.outline_px, rgb(a.outline_color),
             a.text, a.font, a.text_size, tuple(map(float, a.text_pos.split(","))), rgb(a.text_color), a.seed,
             a.dust, tuple(map(float, a.dust_box.split(","))))


if __name__ == "__main__":
    main()
