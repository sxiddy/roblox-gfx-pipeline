"""Track up to 5 dancers in a reference dance video with MediaPipe Pose Landmarker (heavy) and save, per video frame,
each dancer's 33 world landmarks (metres, hip-centred) plus the hip position in the image.
Dancers keep their identity by nearest hip x from the previous frame (left-to-right order at the start).
  python tools/track_dance.py video.mp4 out.json"""
import sys, json
import cv2, numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

MODEL = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\library\models_ml\pose_landmarker_heavy.task"
N = 5
opts = vision.PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=MODEL), running_mode=vision.RunningMode.VIDEO,
                                    num_poses=N, min_pose_detection_confidence=0.3, min_tracking_confidence=0.3)
cap = cv2.VideoCapture(sys.argv[1]); fps = cap.get(cv2.CAP_PROP_FPS)
frames = []; prev = None; i = 0
with vision.PoseLandmarker.create_from_options(opts) as det:
    while True:
        ok, img = cap.read()
        if not ok:
            break
        res = det.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB)), int(i * 1000 / fps))
        people = []
        for lm, wl in zip(res.pose_landmarks, res.pose_world_landmarks):
            hx = (lm[23].x + lm[24].x) / 2; hy = (lm[23].y + lm[24].y) / 2
            people.append({"hx": hx, "hy": hy, "w": [[p.x, p.y, p.z, p.visibility] for p in wl]})
        slots = [None] * N
        if prev is None:
            for s, p in enumerate(sorted(people, key=lambda p: p["hx"])[:N]):
                slots[s] = p
        else:
            free = list(range(N))
            for p in sorted(people, key=lambda p: p["hx"]):
                s = min(free, key=lambda s: abs((prev[s] or {"hx": 9})["hx"] - p["hx"])) if free else None
                if s is not None and abs((prev[s] or {"hx": p["hx"]})["hx"] - p["hx"]) < 0.12:
                    slots[s] = p; free.remove(s)
        prev = [slots[s] or (prev[s] if prev else None) for s in range(N)]
        frames.append(slots); i += 1
json.dump({"fps": fps, "frames": frames}, open(sys.argv[2], "w"))
print("frames", len(frames), "fps", fps, "coverage", [sum(1 for f in frames if f[s]) for s in range(N)])
