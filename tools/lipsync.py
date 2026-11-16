"""Lip sync for face_rig.py: turn a voice line (wav) into mouth keys on the Avatar.

    import lipsync as ls
    cues = ls.rhubarb(wav, text="what the line says")      # timed mouth shapes from Rhubarb Lip Sync
    ls.apply(cues, start_frame=10)                          # keys f_mouth_open and f_mouth_sx
    # no rhubarb, or a non-English line:
    ls.apply(ls.loudness(wav), start_frame=10)

Outside Blender (plain Python) `python lipsync.py line.wav ["the text"]` prints the cues.

Only the mouth controls f_mouth_open and f_mouth_sx are keyed, so expressions keyed with face_rig.pose() on the
other controls stay. Key the expression first, the lip sync after: pose() also keys the mouth controls.
The wav must be PCM (edge-tts gives mp3: `ffmpeg -i line.mp3 -ar 44100 -ac 1 line.wav`).
"""
import json, os, subprocess, sys, wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RHUBARB = os.path.join(ROOT, "tools", "bin", "rhubarb", "Rhubarb-Lip-Sync-1.14.0-Windows", "rhubarb.exe")
# Rhubarb's shapes -> (f_mouth_open, f_mouth_sx). A = closed (m, b, p), B = teeth together (k, s, t),
# C = open (eh, ae), D = wide open (aa), E = rounded (ao, er), F = puckered (oo, w), G = teeth on lip (f, v),
# H = tongue up (l), X = rest.
SHAPES = {"A": (0.05, 1.0), "B": (0.22, 1.12), "C": (0.55, 1.0), "D": (1.0, 1.05), "E": (0.5, 0.7),
          "F": (0.38, 0.45), "G": (0.18, 0.95), "H": (0.6, 0.9), "X": (0.0, 1.0)}


def rhubarb(wav, text=None, exe=RHUBARB):
    """Run Rhubarb on a wav. Returns [(start_s, end_s, open, sx, shape)]. text (what is said) makes it more accurate."""
    cmd = [exe, "-f", "json", "--extendedShapes", "GHX", "-q"]
    tmp = None
    if text:
        tmp = wav + ".dialog.txt"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
        cmd += ["-d", tmp]
    res = wav + ".rhubarb.json"                # rhubarb printed nothing to a piped stdout here; use -o
    try:
        subprocess.run(cmd + ["-o", res, wav], capture_output=True, text=True, check=True)
        with open(res, encoding="utf-8") as f:
            out = f.read()
    finally:
        for t in (tmp, res):
            if t and os.path.exists(t):
                os.remove(t)
    return [(c["start"], c["end"], *SHAPES[c["value"]], c["value"]) for c in json.loads(out)["mouthCues"]]


def loudness(wav, fps=24):
    """Fallback without rhubarb: mouth open follows the loudness of the voice, one cue per frame.
    Returns the same cue list as rhubarb() with shape "L"."""
    with wave.open(wav, "rb") as w:
        sr = w.getframerate(); ch = w.getnchannels(); sw = w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if sw != 2:
        raise RuntimeError("lipsync: the wav must be 16-bit PCM")
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32).reshape(-1, ch).mean(axis=1) / 32768.0
    hop = sr / fps; n = int(len(x) / hop)
    rms = np.array([np.sqrt(np.mean(x[int(i * hop):int((i + 1) * hop)] ** 2) + 1e-12) for i in range(n)])
    ref = np.percentile(rms, 95) or 1.0
    op = np.clip((rms / ref - 0.08) / 0.92, 0, 1) ** 0.6            # gate breath noise, lift quiet syllables
    return [(i / fps, (i + 1) / fps, float(round(op[i], 3)), 1.0, "L") for i in range(n)]


def apply(cues, start_frame=1, fps=None, strength=1.0):
    """Key the cues on the Avatar (inside Blender). start_frame = the frame where the wav starts.
    Each shape is reached on its cue's first frame and held to one frame before the next cue, so the mouth
    snaps between shapes in one frame (as mouths do) instead of drifting. Returns the last keyed frame."""
    import bpy
    import face_rig as fr
    a = fr.arm(); fps = fps or bpy.context.scene.render.fps
    keys = {}                                   # frame -> (open, sx); a later cue wins a shared frame
    for i, (t0, t1, op, sx, _s) in enumerate(cues):
        f0 = start_frame + int(round(t0 * fps)); f1 = start_frame + int(round(t1 * fps))
        keys[f0] = (op * strength, sx)
        if f1 - 1 > f0:
            keys[f1 - 1] = (op * strength, sx)
    first = min(keys); last = max(keys)
    keys.setdefault(first - 2, (0.0, 1.0)); keys[last + 2] = (0.0, 1.0)      # closed before and after the line
    for f in sorted(keys):
        op, sx = keys[f]
        a["f_mouth_open"] = float(op); a["f_mouth_sx"] = float(sx)
        a.keyframe_insert(data_path='["f_mouth_open"]', frame=f); a.keyframe_insert(data_path='["f_mouth_sx"]', frame=f)
    a["f_mouth_open"] = 0.0; a["f_mouth_sx"] = 1.0
    return last + 2


if __name__ == "__main__":
    wav = sys.argv[1]; text = sys.argv[2] if len(sys.argv) > 2 else None
    for c in rhubarb(wav, text):
        print(f"{c[0]:6.2f} {c[1]:6.2f}  {c[4]}  open {c[2]:.2f}  sx {c[3]:.2f}")
