"""Grade the concert frames (bloom on emissives/beams, crushed blacks, vignette, film grain) and encode an mp4.
  python tools/anim_concert_post.py [audio.wav]   -> gfx_output/anim_concert/concert.mp4"""
import os, sys, glob, subprocess
import numpy as np, cv2

ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
D = os.path.join(ROOT, "gfx_output", os.environ.get("CONCERT_DIR", "anim_concert"))
SRC, DST = os.path.join(D, os.environ.get("CONCERT_FRAMES", "frames")), os.path.join(D, os.environ.get("CONCERT_GRADED", "graded"))
os.makedirs(DST, exist_ok=True)

files = sorted(glob.glob(os.path.join(SRC, "f*.png")))
h, w = cv2.imread(files[0]).shape[:2]
yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
vig = 1.0 - 0.45 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) ** 1.3
vig = np.clip(vig, 0.35, 1.0)[..., None]
rng = np.random.default_rng(3)
for i, f in enumerate(files):
    img = cv2.imread(f).astype(np.float32) / 255.0
    lum = img.max(axis=2, keepdims=True)
    hi = img * np.clip((lum - 0.7) / 0.3, 0, 1)  # bloom only from bright lights, threshold 0.7 keeps the face clean
    bloom = cv2.GaussianBlur(hi, (0, 0), 18) * 0.55 + cv2.GaussianBlur(hi, (0, 0), 60) * 0.35
    out = img + bloom
    out = np.clip((out - 0.025) / 0.975, 0, None) ** 1.06  # crush blacks a touch
    out = out * vig
    out += rng.normal(0, 0.018, (h, w, 1)).astype(np.float32)  # mono grain
    cv2.imwrite(os.path.join(DST, f"g{i:04d}.png"), np.clip(out * 255, 0, 255).astype(np.uint8))
print("graded", len(files))
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", os.path.join(DST, "g%04d.png")]
if len(sys.argv) > 1:
    cmd += ["-i", sys.argv[1], "-c:a", "aac", "-b:a", "256k", "-shortest"]
cmd += ["-c:v", "libx264", "-crf", "23", "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        os.path.join(D, "concert.mp4" if len(sys.argv) > 1 else "concert_silent.mp4")]
subprocess.run(cmd, check=True)
print("done")
