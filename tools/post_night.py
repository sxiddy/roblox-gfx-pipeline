"""Night grade: crushed blacks, slight purple tint, light chromatic aberration, vignette, fine grain. python post_night.py IN OUT"""
import sys
import numpy as np
from PIL import Image

im = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(np.float32) / 255
h, w, _ = im.shape
im = np.clip((im - 0.025) / 0.975, 0, 1) ** 1.06                      # deeper blacks
im = im * np.array([1.0, 0.97, 1.03])                                   # purple lean
s = 2                                                                   # CA: red out, blue in
im[:, :, 0] = np.roll(im[:, :, 0], s, axis=1); im[:, :, 2] = np.roll(im[:, :, 2], -s, axis=1)
yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot((xx - w / 2) / (w / 2), (yy - h * 0.42) / (h / 2))
im *= (1 - 0.38 * np.clip(r - 0.45, 0, 1) ** 1.6)[..., None]            # vignette
im += np.random.default_rng(3).normal(0, 0.018, (h, w, 1))             # grain
Image.fromarray((np.clip(im, 0, 1) * 255).astype(np.uint8)).save(sys.argv[2])
print("saved", sys.argv[2])
