"""Track ONE dancer in a reference video: follow a crop window around them (upscaled x2) with MediaPipe Pose (heavy).
Saves per-frame 33 world landmarks (metres, hip-centred; x right of image, y down, z toward camera negative) and the
hip x in the full frame. Missing frames are null.
  python tools/track_one.py video.mp4 out.json start_x(0-1)"""
import sys, json
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

MODEL = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\library\models_ml\pose_landmarker_heavy.task"
opts = vision.PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=MODEL), running_mode=vision.RunningMode.VIDEO,
                                    num_poses=3, min_pose_detection_confidence=0.3, min_tracking_confidence=0.3)
cap = cv2.VideoCapture(sys.argv[1]); fps = cap.get(cv2.CAP_PROP_FPS)
cx = float(sys.argv[3]); out = []; i = 0
with vision.PoseLandmarker.create_from_options(opts) as det:
    while True:
        ok, img = cap.read()
        if not ok:
            break
        H, W = img.shape[:2]; half = int(0.13 * W)
        x0 = max(0, min(W - 2 * half, int(cx * W) - half)); crop = img[int(0.15 * H):H, x0:x0 + 2 * half]
        crop = cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        res = det.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)), int(i * 1000 / fps))
        best = None
        for lm, wl in zip(res.pose_landmarks, res.pose_world_landmarks):
            hx = x0 / W + (lm[23].x + lm[24].x) / 2 * (2 * half) / W
            if best is None or abs(hx - cx) < abs(best[0] - cx):
                best = (hx, wl)
        if best and abs(best[0] - cx) < 0.08:
            cx = 0.7 * cx + 0.3 * best[0]
            out.append({"hx": best[0], "w": [[p.x, p.y, p.z, p.visibility] for p in best[1]]})
        else:
            out.append(None)
        i += 1
json.dump({"fps": fps, "frames": out}, open(sys.argv[2], "w"))
print("frames", len(out), "tracked", sum(1 for f in out if f), "end x", round(cx, 3))
