"""One grade for the whole film as a 3D LUT (.cube), so every shot matches (docs/SUPERIOR_PLAN.md step 7).
    python tools/film_lut.py look OUT.cube                    -> the house look below
    python tools/film_lut.py match RAW.png GRADED.png OUT.cube -> learn per-channel curves from an approved hero frame pair
    python tools/film_lut.py apply LUT.cube IN.png OUT.png
The .cube also works in ffmpeg: -vf lut3d=file.cube. In Python: lut = load(path); img01 = apply(img01, lut)."""
import sys
import numpy as np

N = 33


def look(c):
    """Gentle film look on float RGB 0-1: lifted mids, soft S-curve, teal shadows / warm highlights, slightly less saturation."""
    c = np.clip(c, 0, 1) ** 0.9
    c = 0.5 + (c - 0.5) * 1.06
    l = (c * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True)
    sh = (1 - l) ** 3; hi = l ** 2
    c = c + sh * np.array([-0.012, 0.004, 0.016]) + hi * np.array([0.02, 0.006, -0.02])
    return np.clip(l + (c - l) * 0.95, 0, 1)


def grid():
    v = np.linspace(0, 1, N); b, g, r = np.meshgrid(v, v, v, indexing="ij")
    return np.stack([r, g, b], -1)                       # [b, g, r] -> rgb


def write(lut, path):
    with open(path, "w") as f:
        f.write(f"LUT_3D_SIZE {N}\n")
        for row in lut.reshape(-1, 3):
            f.write("%.6f %.6f %.6f\n" % tuple(row))


def load(path):
    rows = [l.split() for l in open(path) if l[:1].isdigit() or l[:1] == "-"]
    a = np.array(rows, np.float32); n = round(len(a) ** (1 / 3))
    return a.reshape(n, n, n, 3)


def apply(img, lut):
    from scipy.ndimage import map_coordinates
    n = lut.shape[0]; p = np.clip(img, 0, 1) * (n - 1)
    co = [p[..., 2], p[..., 1], p[..., 0]]
    return np.stack([map_coordinates(lut[..., c], co, order=1) for c in range(3)], -1)


def match(raw, graded):
    """Per-channel curve that maps the raw frame's histogram onto the graded frame's."""
    g = grid(); out = np.empty_like(g); q = np.linspace(0, 1, 257)
    for c in range(3):
        a = np.quantile(raw[..., c], q); b = np.quantile(graded[..., c], q)
        a = np.maximum.accumulate(a + np.arange(257) * 1e-7)
        out[..., c] = np.interp(g[..., c], a, b)
    return out


if __name__ == "__main__":
    from PIL import Image
    img = lambda p: np.asarray(Image.open(p).convert("RGB"), np.float32) / 255
    m = sys.argv[1]
    if m == "look":
        write(look(grid()), sys.argv[2])
    elif m == "match":
        write(match(img(sys.argv[2]), img(sys.argv[3])), sys.argv[4])
    elif m == "apply":
        Image.fromarray((apply(img(sys.argv[3]), load(sys.argv[2])) * 255 + 0.5).astype(np.uint8)).save(sys.argv[4])
    print("OK", m)
