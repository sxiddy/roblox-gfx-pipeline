"""Turn MediaPipe dancer tracks (track_one.py) into per-frame bone directions at the animation frame rate.
Avatar space: +X = dancer's right, +Y = forward (toward the audience), +Z = up. The reference dancer faces the camera,
so from MediaPipe world coords (x image-right, y down, z away from camera): avatar = (-x, -z, -y).
Gaps in the main track are filled from the backup track (same choreography), then linearly; light temporal smoothing.
  python tools/choreo_from_track.py main.json backup.json out.json [fps=24] [duration]"""
import sys, json
import numpy as np
from scipy.ndimage import gaussian_filter1d

main, backup = (json.load(open(p)) for p in sys.argv[1:3])
FPS = float(sys.argv[4]) if len(sys.argv) > 4 else 24.0
src_fps = main["fps"]; n = len(main["frames"])
dur = float(sys.argv[5]) if len(sys.argv) > 5 else n / src_fps
L = np.full((n, 33, 3), np.nan)
for i in range(n):
    f = main["frames"][i] or (backup["frames"][i] if i < len(backup["frames"]) else None)
    if f:
        w = np.array(f["w"])[:, :3]
        L[i] = np.stack([-w[:, 0], -w[:, 2], -w[:, 1]], axis=1)
idx = np.arange(n)
for j in range(33):  # fill remaining gaps
    for c in range(3):
        v = L[:, j, c]; ok = ~np.isnan(v)
        L[:, j, c] = np.interp(idx, idx[ok], v[ok])
L = gaussian_filter1d(L, sigma=1.2, axis=0)  # 30 fps source: removes jitter, keeps hits sharp
t_out = np.arange(int(round(dur * FPS))) / FPS
Lr = np.stack([np.stack([np.interp(t_out * src_fps, idx, L[:, j, c]) for c in range(3)], 1) for j in range(33)], 1)


def unit(v):
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-9)


P = lambda k: Lr[:, k]
midS, midH = (P(11) + P(12)) / 2, (P(23) + P(24)) / 2
spine = unit(midS - midH)
right = unit(P(12) - P(11))  # MediaPipe 12 = dancer's right shoulder
fwd = unit(np.cross(spine, right))  # z x x = y
hip_right = unit(P(24) - P(23)); hip_fwd = unit(np.cross(np.array([0, 0, 1.0]), hip_right))
ears = (P(7) + P(8)) / 2
head_fwd = unit(P(0) - ears); head_up = unit(np.cross(unit(P(8) - P(7)), head_fwd))  # right x fwd = up
out = {"fps": FPS, "frames": len(t_out), "spine": spine, "fwd": fwd, "hip_fwd": hip_fwd, "head_up": head_up,
       "head_fwd": head_fwd}
for side, (s, e, w, h, k, a, toe) in {"R": (12, 14, 16, 24, 26, 28, 32), "L": (11, 13, 15, 23, 25, 27, 31)}.items():
    out["uarm" + side] = unit(P(e) - P(s)); out["larm" + side] = unit(P(w) - P(e))
    out["uleg" + side] = unit(P(k) - P(h)); out["lleg" + side] = unit(P(a) - P(k)); out["foot" + side] = unit(P(toe) - P(a))
json.dump({k: (v.round(4).tolist() if isinstance(v, np.ndarray) else v) for k, v in out.items()}, open(sys.argv[3], "w"))
print("frames", len(t_out), "| sample @4.5s uarmR", out["uarmR"][int(4.5 * FPS)].round(2), "spine", spine[int(4.5 * FPS)].round(2),
      "| arms-up check (z of uarm max)", out["uarmR"][:, 2].max().round(2))
