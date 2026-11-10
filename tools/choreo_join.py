"""Append a second choreo (later song section) to the first, starting `skip` seconds into the second, with a short
direction blend across the seam so the join does not snap.
  python tools/choreo_join.py first.json second.json skip_s out.json [blend_frames=6]"""
import sys, json
import numpy as np

a, b = (json.load(open(p)) for p in sys.argv[1:3])
skip, out = float(sys.argv[3]), sys.argv[4]
nb = int(sys.argv[5]) if len(sys.argv) > 5 else 6
k0 = int(round(skip * a["fps"]))
res = {"fps": a["fps"]}
for key, v in a.items():
    if not isinstance(v, list):
        continue
    A, B = np.array(v), np.array(b[key])[k0:]
    for i in range(min(nb, len(B))):  # ease the first frames of B from A's last direction
        w = (i + 1) / (nb + 1)
        B[i] = (1 - w) * A[-1] + w * B[i]
        B[i] /= np.linalg.norm(B[i]) + 1e-9
    res[key] = np.concatenate([A, B]).round(4).tolist()
res["frames"] = len(res["spine"])
res["seam"] = a["frames"]
json.dump(res, open(out, "w"))
print("frames", res["frames"], "seam", res["seam"])
