"""Stylized music-video frame (stage, spotlights, five dancer silhouettes, player UI) for the gamer-corner monitor.
No real footage. Usage: python make_cortis_screen.py OUT_PNG"""
import sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 2928, 1100
out = sys.argv[1]
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
img = np.zeros((H, W, 3), np.float32) + np.array([0.02, 0.03, 0.06])
# spotlight cones from the top
for cx, col in ((0.18, (0.2, 0.5, 1.0)), (0.5, (1.0, 0.45, 0.2)), (0.82, (0.2, 0.5, 1.0)), (0.34, (1.0, 0.3, 0.5)), (0.66, (1.0, 0.3, 0.5))):
    spread = (0.02 + 0.22 * (y / H)) * W
    d = np.abs(x - (cx * W + (0.5 - cx) * 0.5 * y)) / spread
    img += (np.clip(1 - d, 0, 1) ** 2 * (1 - y / H * 0.6))[..., None] * np.array(col) * 0.45
# floor glow
img += (np.clip((y - 0.72 * H) / (0.28 * H), 0, 1) ** 1.5)[..., None] * np.array([0.9, 0.45, 0.25]) * 0.35
im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im)
# crowd light sticks
r = random.Random(4)
for _ in range(90):
    px, py = r.randint(0, W), r.randint(int(0.86 * H), H); d.line((px, py, px + r.randint(-6, 6), py - r.randint(30, 80)), fill=(255, r.randint(120, 220), r.randint(80, 220)), width=5)
# five dancers: round-limbed silhouettes with a coloured rim, varied poses
def limb(dr, p, q, w, col):
    dr.line((p, q), fill=col, width=w)
    for c in (p, q): dr.ellipse((c[0]-w/2, c[1]-w/2, c[0]+w/2, c[1]+w/2), fill=col)
POSES = [dict(la=(-1.0,-0.9), ra=(1.0,-0.2), lk=(-0.3,1.0), rk=(0.5,0.9)), dict(la=(-0.8,-1.0), ra=(0.9,-1.0), lk=(-0.2,1.0), rk=(0.2,1.0)),
         dict(la=(-1.0,0.1), ra=(0.7,-1.1), lk=(-0.5,0.9), rk=(0.3,1.0)), dict(la=(-0.5,-1.1), ra=(1.0,0.3), lk=(-0.2,1.0), rk=(0.6,0.8)),
         dict(la=(-0.9,-0.5), ra=(0.8,-0.9), lk=(-0.4,0.9), rk=(0.1,1.0))]
RIM = [(120, 180, 255), (255, 120, 170), (255, 170, 90), (255, 120, 170), (120, 180, 255)]
for i, cx in enumerate((0.26, 0.38, 0.5, 0.62, 0.74)):
    bx = int(cx * W); top = int(0.30 * H + (i % 2) * 36); S = 1.0 + (0.1 if i == 2 else 0); P = POSES[i]
    for off, col in (((5, -4), RIM[i]), ((0, 0), (8, 8, 12))):
        ox, oy = off; sh = (bx + ox, top + 150 + oy); hip = (bx + ox, top + 300 + oy); fn = lambda v, L: (sh[0] + v[0] * L, sh[1] + v[1] * L)
        d.ellipse((bx + ox - 38, top + oy, bx + ox + 38, top + 84 + oy), fill=col)
        limb(d, (sh[0], sh[1] - 20), hip, 78, col)
        for sgn, ak in ((-1, "la"), (1, "ra")):
            s0 = (sh[0] + sgn * 38, sh[1] - 5); e = (s0[0] + P[ak][0] * 70, s0[1] + P[ak][1] * 70); h = (e[0] + P[ak][0] * 70, e[1] + P[ak][1] * 70)
            limb(d, s0, e, 26, col); limb(d, e, h, 22, col)
        for sgn, lk in ((-1, "lk"), (1, "rk")):
            h0 = (hip[0] + sgn * 20, hip[1]); k_ = (h0[0] + P[lk][0] * 60, h0[1] + 90); f = (k_[0] + sgn * 12, k_[1] + 100)
            limb(d, h0, k_, 34, col); limb(d, k_, f, 28, col); limb(d, f, (f[0] + sgn * 30, f[1] + 6), 20, col)
im = im.filter(ImageFilter.GaussianBlur(1.2)); d = ImageDraw.Draw(im)
def font(n):
    for f in ("segoeuib.ttf", "arialbd.ttf"):
        try: return ImageFont.truetype(f, n)
        except Exception: pass
    return ImageFont.load_default()
d.text((1560, 60), "CORTIS", fill=(255, 255, 255), font=font(150))
d.text((1566, 225), "LIVE  -  stage performance", fill=(255, 170, 120), font=font(56))
# player bar
d.rectangle((0, H - 90, W, H), fill=(10, 10, 14)); d.rectangle((60, H - 62, W - 60, H - 52), fill=(70, 70, 80)); d.rectangle((60, H - 62, 1500, H - 52), fill=(255, 60, 70))
d.ellipse((1480, H - 74, 1512, H - 42), fill=(255, 60, 70)); d.polygon([(70, H - 85), (70, H - 65), (95, H - 75)], fill=(255, 255, 255))
a = np.asarray(im).astype(np.float32) / 255
a *= (0.93 + 0.07 * (np.arange(H) % 4 < 2))[:, None, None]
Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(out); print("ok")
