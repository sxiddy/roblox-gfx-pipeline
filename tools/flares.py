"""Lens flares for GFX post (screen blend).
python -I tools/flares.py IN OUT [--flare x,y,len,strength ...] [--halo x,y,radius,strength] [--color r,g,b] [--halo-color r,g,b]
x,y are frame fractions (y down). --flare = horizontal anamorphic streak + hot core; --halo = soft round glow (moon)."""
import argparse
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--flare", nargs="*", default=[]); ap.add_argument("--halo", nargs="*", default=[])
ap.add_argument("--color", default="1,0.48,0.1"); ap.add_argument("--halo-color", default="0.35,0.75,1")
a = ap.parse_args()
im = np.asarray(Image.open(a.src).convert("RGB")).astype(np.float32) / 255
H, W, _ = im.shape
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
add = np.zeros_like(im)
col = np.array([float(v) for v in a.color.split(",")], np.float32)
hcol = np.array([float(v) for v in a.halo_color.split(",")], np.float32)
for spec in a.flare:
    x, y, ln, st = (float(v) for v in spec.split(","))
    cx, cy = x * W, y * H
    streak = np.exp(-((xx - cx) / (ln * W)) ** 2 * 4) * np.exp(-((yy - cy) / (0.005 * H)) ** 2)
    wide = np.exp(-((xx - cx) / (ln * W * 0.5)) ** 2 * 4) * np.exp(-((yy - cy) / (0.02 * H)) ** 2) * 0.35
    core = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (0.045 * W) ** 2 * 3) * 0.6
    add += ((streak + wide + core) * st)[..., None] * col
for spec in a.halo:
    x, y, rad, st = (float(v) for v in spec.split(","))
    r = np.sqrt((xx - x * W) ** 2 + (yy - y * H) ** 2) / (rad * W)
    add += (np.exp(-r ** 2 * 2.5) * st)[..., None] * hcol
res = 1 - (1 - im) * (1 - np.clip(add, 0, 1))
Image.fromarray((np.clip(res, 0, 1) * 255).astype(np.uint8)).save(a.out)
print("ok", a.out)
