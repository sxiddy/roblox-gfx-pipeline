"""Painted finish from render passes (docs/SUPERIOR_PLAN.md step 6). Pillow + numpy (+ OpenCV for 16-bit and blur).
    python finish.py finish BEAUTY PASSDIR OUT_FINISH OUT_FINAL [options]
    python finish.py side OUT HEIGHT IMG1 IMG2 ...          (row of images at one height, for side-by-sides and sheets)
PASSDIR holds mask.png (avatar alpha), hair.png (head accessories alpha), emission.png (lights off, black world),
depth.png (view distance / dmax, 16-bit grey), normal.png (camera space, n*0.5+0.5) and meta.json (dmax, head_box).
What it paints, in order:
  1 depth haze     far pixels drift toward a haze colour and pick up the wide glow; never on the avatar
  2 glow           bloom built from the emission pass only, so skin and faces are never a bloom source
  3 rim glow       normal . rim direction, only near the silhouette edge of the mask, plus a small outer halo
  4 hair highlight soft streak on the rim side of the hair mask
  5 dust           specks on depth layers: each speck has a depth and is hidden where the scene is closer; none on the face
then a gentle grade for the final: contrast and saturation (weaker on the avatar), vignette, low grain."""
import argparse, json, os, sys
import numpy as np
from PIL import Image
try:
    import cv2
except Exception:  # blur falls back to Pillow, 16-bit depth is read by Pillow as I;16
    cv2 = None


def load(path, grey=False):
    if cv2 is not None:
        a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if a is None:
            raise SystemExit(f"cannot read {path}")
        a = a.astype(np.float32) / (65535.0 if a.dtype == np.uint16 else 255.0)
        if a.ndim == 3:
            a = a[..., [2, 1, 0] + ([3] if a.shape[2] == 4 else [])]
    else:
        im = Image.open(path); a = np.asarray(im).astype(np.float32)
        a /= 65535.0 if im.mode.startswith("I") else 255.0
    if grey and a.ndim == 3:
        a = a[..., :3].mean(axis=-1)
    return a


def save(path, a):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def blur(a, sigma):
    if sigma <= 0:
        return a
    if cv2 is not None:
        return cv2.GaussianBlur(a, (0, 0), sigma)
    from PIL import ImageFilter
    ch = a[..., None] if a.ndim == 2 else a
    out = np.stack([np.asarray(Image.fromarray((np.clip(ch[..., i], 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sigma))) for i in range(ch.shape[2])], -1) / 255.0
    return out[..., 0] if a.ndim == 2 else out.astype(np.float32)


screen = lambda a, b: 1 - (1 - np.clip(a, 0, 1)) * (1 - np.clip(b, 0, 1))
luma = lambda a: a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
vec = lambda s: np.array([float(v) for v in s.split(",")], np.float32)


def finish(A):
    B = load(A.beauty)[..., :3]; h, w = B.shape[:2]; P = A.passes; raw = B.copy()
    meta = json.load(open(os.path.join(P, "meta.json")))
    M = load(os.path.join(P, "mask.png"))[..., 3]; Hm = load(os.path.join(P, "hair.png"))[..., 3]
    E = load(os.path.join(P, "emission.png"))[..., :3]; D = load(os.path.join(P, "depth.png"), grey=True)
    N = load(os.path.join(P, "normal.png"))[..., :3] * 2 - 1
    for n, a in (("mask", M), ("hair", Hm), ("emission", E), ("depth", D), ("normal", N)):
        if a.shape[:2] != (h, w):
            raise SystemExit(f"{n} pass is {a.shape[1]}x{a.shape[0]}, beauty is {w}x{h}")
    Dm = np.where(D <= 1e-4, 1.0, D) * meta["dmax"]; k = w / 1080.0; log = []

    def step(name, new):
        nonlocal B
        log.append(f"{name}: mean change {float(np.abs(new - B).mean()) * 255:.2f}, on the avatar {float((np.abs(new - B).mean(-1) * M).sum() / max(M.sum(), 1)) * 255:.2f} (0-255)")
        B = np.clip(new, 0, 1)
    Es = np.clip((E - A.glow_floor) / (1 - A.glow_floor), 0, 1)
    G = blur(Es, 6 * k) * 0.5 + blur(Es, 20 * k) * 0.35 + blur(Es, 60 * k) * 0.25; wide = blur(Es, 130 * k)
    # 1 haze
    t = np.clip((Dm - A.haze_near) / (A.haze_far - A.haze_near), 0, 1); t = t * t * (3 - 2 * t)
    a = (blur(t, 3 * k) * A.haze * (1 - M))[..., None]
    step("haze", B * (1 - a) + (vec(A.haze_color) + wide * 1.5) * a)
    # 2 glow from emission only
    step("glow", screen(B, G * A.glow * (1 - 0.6 * M)[..., None]))
    # 3 rim
    L = vec(A.rim_dir); L /= np.linalg.norm(L); rc = vec(A.rim_color)
    edge = np.clip((M - blur(M, 14 * k)) * 3.0, 0, 1)
    rim = M * edge * np.clip(N @ L, 0, 1) ** 1.5
    layer = rim[..., None] * rc * A.rim
    step("rim", screen(B, layer + blur(layer, 5 * k) * 0.6))
    # 4 hair highlight
    L2 = L + np.array([0, 0.8, 0], np.float32); L2 /= np.linalg.norm(L2)
    hl = blur(Hm * np.clip(N @ L2, 0, 1) ** 3, 4 * k)
    step("hair", screen(B, hl[..., None] * rc * A.hair))
    # 5 dust on depth layers
    rng = np.random.default_rng(A.seed); x0, y0, x1, y1 = meta["head_box"]; dust = np.zeros((h, w, 3), np.float32); kept = 0
    for lo, hi, sig in ((0.9, 1.8, 2.6), (1.8, 3.5, 1.5), (3.5, 7.0, 0.9)):
        lay = np.zeros((h, w, 3), np.float32)
        for _ in range(A.dust // 3):
            x, y, z = rng.random(), rng.random(), rng.uniform(lo, hi)
            if x0 - 0.04 < x < x1 + 0.04 and y0 - 0.04 < y < y1 + 0.06:
                continue
            px, py = int(x * (w - 1)), int(y * (h - 1))
            if Dm[py, px] <= z:
                continue
            lit = G[py, px] * 2.0 + wide[py, px] * 2.0 + 0.10
            lay[py, px] += np.clip(lit, 0, 1) * rng.uniform(0.5, 1.0); kept += 1
        dust += blur(lay, sig * k) * (2 * np.pi * (sig * k) ** 2) * (0.55 if sig > 2 else 0.9)
    step(f"dust ({kept} specks)", screen(B, dust * A.dust_strength))
    save(A.out_finish, B)
    # gentle grade
    Mg = M[..., None]; amt = 1 - 0.65 * Mg
    C = (B - 0.35) * A.contrast + 0.35; B2 = B + (C - B) * amt
    lu = luma(B2)[..., None]; B2 = B2 + ((lu + (B2 - lu) * A.sat) - B2) * amt
    B2 = B2 + np.array([0.008, 0.0, 0.024], np.float32) * ((1 - lu) ** 2) * (1 - Mg)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); r = np.hypot((xx / w - 0.5) * 2, (yy / h - 0.5) * 2) / np.sqrt(2)
    B2 = B2 * (1 - A.vignette * r ** 2.2)[..., None]
    B2 = B2 + (rng.standard_normal((h, w)).astype(np.float32) * A.grain)[..., None] * (1 - 0.4 * Mg)
    save(A.out, B2)
    for n, im in (("raw", raw), ("finish", B), ("final", np.clip(B2, 0, 1))):
        l = luma(im) * 255
        print(f"{n}: mean luma {l.mean():.1f}, black point (2%) {np.percentile(l, 2):.0f}, white point (99.5%) {np.percentile(l, 99.5):.0f}, head-box luma {l[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)].mean():.0f}")
    print("\n".join(log))


def side(A):
    ims = [Image.open(p).convert("RGB") for p in A.images]; H = A.height; gap = 12
    ims = [im.resize((round(im.width * H / im.height), H), Image.LANCZOS) for im in ims]
    out = Image.new("RGB", (sum(im.width for im in ims) + gap * (len(ims) - 1), H), (12, 12, 14)); x = 0
    for im in ims:
        out.paste(im, (x, 0)); x += im.width + gap
    out.save(A.out, quality=92); print("wrote", A.out, out.size)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("finish"); [f.add_argument(n) for n in ("beauty", "passes", "out_finish", "out")]
    f.add_argument("--haze", type=float, default=0.28); f.add_argument("--haze-near", type=float, default=2.5)
    f.add_argument("--haze-far", type=float, default=9.0); f.add_argument("--haze-color", default="0.16,0.11,0.26")
    f.add_argument("--glow", type=float, default=0.55); f.add_argument("--glow-floor", type=float, default=0.2)
    f.add_argument("--rim", type=float, default=0.4); f.add_argument("--rim-dir", default="0.85,0.3,0.25")
    f.add_argument("--rim-color", default="0.62,0.32,1.0"); f.add_argument("--hair", type=float, default=0.22)
    f.add_argument("--dust", type=int, default=240); f.add_argument("--dust-strength", type=float, default=0.5)
    f.add_argument("--contrast", type=float, default=1.06); f.add_argument("--sat", type=float, default=1.05)
    f.add_argument("--vignette", type=float, default=0.3); f.add_argument("--grain", type=float, default=0.006)
    f.add_argument("--seed", type=int, default=3)
    sd = sub.add_parser("side"); sd.add_argument("out"); sd.add_argument("height", type=int); sd.add_argument("images", nargs="+")
    A = ap.parse_args(); finish(A) if A.cmd == "finish" else side(A)
