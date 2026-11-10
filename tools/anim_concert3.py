"""Concert v3 (32 s, REDRED film audio 23.97-55.97 s; the tracked chorus = practice video 0:40.0 = song 35.81 s = clip 11.84 s). Key-pose dance on the measured beat grid (no per-frame tracking),
overlapping action by per-bone key offsets, continuous bone roll + quaternion sign matching (no flips),
slow hero entrance for Suhaa, packed front row, motion blur. Reuses venue/crowd/fx helpers from anim_concert2.
  blender -b --factory-startup -P tools/anim_concert3.py -- build
  blender -b gfx_output/anim_concert2/scene_v3.blend -P tools/anim_concert3.py -- check
  blender -b gfx_output/anim_concert2/scene_v3.blend -P tools/anim_concert3.py -- stills 30,120,200,345,400,560 [pct]
  blender -b gfx_output/anim_concert2/scene_v3.blend -P tools/anim_concert3.py -- frames a b [pct]
"""
import sys, os, math, json, random
import bpy
from mathutils import Vector, Matrix, Quaternion, noise

ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
sys.path.insert(0, os.path.join(ROOT, "tools"))
import anim_concert as base
import anim_concert2 as c2
from anim_concert import mat, empty, upd, spot

OUT = c2.OUT
FPS, END = 24, 768
base.END = c2.END = END
FRONT, STAGE_Z, STAGE_Y, BAR_Y = c2.FRONT, c2.STAGE_Z, c2.STAGE_Y, c2.BAR_Y
BEATS = json.load(open(os.path.join(OUT, "beats_v3.json")))
c2.CH = json.load(open(os.path.join(ROOT, "gfx_output", "anim_concert", "ref", "choreo_full.json"))); c2._smooth(2)  # light smoothing keeps the steps
P = 0.4893  # beat period (s), ~122.6 BPM
BEATS = [round(BEATS[0] - P * k, 3) for k in range(2, 0, -1)] + BEATS
while BEATS[-1] + P < 32.1:  # librosa loses the grid in the chorus; keep the measured period
    BEATS.append(round(BEATS[-1] + P, 3))
fr = lambda t: int(round(t * FPS)) + 1
sec = fr

# story marks (s)
T_DROP, T_SIDE, T_SIL, T_WALK, T_HERO, T_FORM, T_CHORUS, T_HIT2, T_END = 2.5, 2.9, 3.0, 5.5, 10.0, 11.0, 11.84, 30.93, 31.99
CH0 = 35.81 - 23.97  # clip time of choreo.json frame 0


def env(t):
    if T_DROP + 0.12 <= t < T_HERO:
        return 0.02
    return 1.0


c2.env = env


def ease(u):
    u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)


# ---------------------------------------------------------------- pose model
def nv(*a):
    return Vector(a).normalized()


def rotz(v, ang):
    c, s = math.cos(ang), math.sin(ang); return Vector((c * v.x - s * v.y, s * v.x + c * v.y, v.z))


def legs(knee_deg, wide=0.1, step=0.0, side=1):
    """thigh/shin directions for a bend (feet stay under the hip as thigh and shin tilt equally)."""
    b = math.radians(knee_deg) / 2
    th = nv(wide * side, math.sin(b) + step, -math.cos(b)); sh = nv(0.02 * side, -math.sin(b) + step * 0.3, -math.cos(b))
    return th, sh


def arm(kind, side, amp=1.0, ph=0.0):
    """(upper, lower) directions for an arm shape; side=+1 avatar right (.P)."""
    s = side
    if kind == "chest":    # bent ~90 deg, fists near the chest
        return nv(0.25 * s, 0.25, -0.95), nv(-0.35 * s, 0.9, 0.25 + 0.15 * ph)
    if kind == "low":      # relaxed hang, slight bend
        return nv(0.18 * s, 0.05, -1), nv(0.12 * s, 0.35, -0.95)
    if kind == "hit":      # shoulder hit: elbow out and up
        return nv(0.8 * s, 0.15, -0.35 * amp), nv(0.2 * s, 0.6, 0.75)
    if kind == "up":       # diagonal point up
        return nv(0.55 * s, 0.25, 0.8), nv(0.6 * s, 0.35, 0.72)
    if kind == "across":   # arm wave across the body
        return nv(-0.3 * s, 0.75, -0.2 + 0.4 * ph), nv(-0.6 * s, 0.7, 0.2 + 0.3 * ph)
    if kind == "out":      # arm out to the side
        return nv(0.95 * s, 0.2, 0.1 + 0.3 * ph), nv(0.95 * s, 0.25, 0.2 + 0.3 * ph)
    if kind == "hip":      # hand on hip
        return nv(0.75 * s, -0.25, -0.6), nv(-0.55 * s, 0.25, -0.25)
    if kind == "present":  # palm toward the centre, low
        return nv(0.25 * s, 0.7, -0.5), nv(0.15 * s, 0.95, -0.1)
    if kind == "swing":    # walking swing, ph in -1..1
        return nv(0.15 * s, 0.3 * ph, -1), nv(0.1 * s, 0.3 * ph + 0.28, -0.95)
    raise KeyError(kind)


def pose(knee=20, lean=0.12, tilt=0.0, twist=0.0, head_tilt=0.0, nod=0.0, head_turn=0.0, armR=("chest",), armL=("chest",),
         wide=0.1, stepR=0.0, stepL=0.0, hip_roll=0.0):
    p = {}
    p["LowerTorso"] = (nv(tilt + hip_roll, 0.05, 1), rotz(Vector((0, 1, 0)), twist * -0.4))
    p["UpperTorso"] = (nv(tilt * 0.4 - hip_roll * 0.5, lean, 1), rotz(Vector((0, 1, 0)), twist))
    hf = rotz(Vector((0, 1, 0)), twist + head_turn); hf.z = -nod
    p["Head"] = (nv(head_tilt, -nod * 0.5, 1), hf.normalized())
    for s, sd, spec, st in ((".P", 1, armR, stepR), (".N", -1, armL, stepL)):
        u, l = arm(spec[0], sd, *spec[1:])
        p["UpperArm" + s], p["LowerArm" + s], p["Hand" + s] = (u, None), (l, None), (l, None)
        th, sh = legs(knee, wide, st, sd)
        p["UpperLeg" + s], p["LowerLeg" + s] = (th, None), (sh, None)
        p["Foot" + s] = (nv(0.05 * sd, 1, -0.08), Vector((0, 0, 1)))
    return p


ORDER = ["LowerTorso", "UpperTorso", "Head", "UpperArm.P", "LowerArm.P", "Hand.P", "UpperArm.N", "LowerArm.N", "Hand.N",
         "UpperLeg.P", "LowerLeg.P", "Foot.P", "UpperLeg.N", "LowerLeg.N", "Foot.N"]
MAXDEG = 11.0
LAG = {"LowerTorso": 0, "UpperTorso": 1, "Head": 2, "UpperArm": 2, "LowerArm": 3, "Hand": 4, "UpperLeg": 0, "LowerLeg": 0, "Foot": 0}


class Rig:
    """Applies poses with continuous roll (each bone's side axis is carried over from its last pose) and signs."""
    def __init__(self, a, scale=1.0, offset=0, seed=0):
        self.a, self.scale, self.offset = a, scale, offset
        self.z = {}; self.q = {}; self.qf = {}; self.rnd = random.Random(seed)
        for pb in a.pose.bones:
            pb.rotation_mode = "QUATERNION"
        a.rotation_euler = (0, 0, math.pi); upd()
        self.foot0 = min((a.matrix_world @ a.pose.bones[b].tail).z for b in ("Foot.P", "Foot.N"))
        self.loc = {}

    def aim(self, bone, d, hint=None):
        pb = self.a.pose.bones.get(bone)
        if pb is None:
            return
        upd(); y = Vector(d).normalized()
        cands = ([Vector(hint)] if hint is not None else []) + ([self.z[bone]] if bone in self.z else []) + [Vector((0, 1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0))]
        for h in cands:
            z = h - h.dot(y) * y
            if z.length > 0.25:
                break
        z.normalize(); x = y.cross(z); self.z[bone] = z.copy()
        m = Matrix((x, y, z)).transposed().to_4x4(); m.translation = pb.head; pb.matrix = m

    def set(self, p):
        for pb in self.a.pose.bones:
            pb.rotation_quaternion = Quaternion()
        for b in ORDER:
            d, h = p[b]
            if b.startswith(("UpperArm", "LowerArm", "Hand")):
                h = None
            self.aim(b, d, h)
        upd()

    def key(self, f, p, xy, yaw=0.0, dz=0.0, hold=False, lag=True):
        """Pose -> keys: torso at f, chain children later (overlap), roots at f."""
        self.set(p)
        f = f + self.offset
        a = self.a
        a.rotation_euler = (0, 0, math.pi + yaw); a.location = (xy[0], xy[1], STAGE_Z); upd()
        low = min((a.matrix_world @ a.pose.bones[b].tail).z for b in ("Foot.P", "Foot.N"))
        a.location.z = STAGE_Z + (STAGE_Z + self.foot0 - low) + dz
        a.keyframe_insert("location", frame=f); a.keyframe_insert("rotation_euler", index=2, frame=f)
        for pb in a.pose.bones:
            q = pb.rotation_quaternion.copy(); prev = self.q.get(pb.name)
            lag_ = LAG.get(pb.name.split(".")[0], 0) if lag else 0; kf = max(1, f + lag_)
            if prev is not None:
                if q.dot(prev) < 0:
                    q.negate()
                ang = math.degrees(prev.rotation_difference(q).angle); gap = max(1, kf - self.qf[pb.name])
                if ang > MAXDEG * gap:  # speed limit: never faster than MAXDEG per frame (bezier peaks ~1.5x)
                    q = prev.slerp(q, MAXDEG * gap / ang)
            self.q[pb.name] = q; self.qf[pb.name] = kf; pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=kf)


# ---------------------------------------------------------------- choreography
def beat_index(t):
    return min(range(len(BEATS)), key=lambda k: abs(BEATS[k] - t))


def groove_keys(r, t0, t1, xy, amp=1.0, mirror=1, style="chorus", yaw=0.0, head_turn=0.0):
    """Key a groove from t0 to t1 on beats (down) and half-beats (up)."""
    times = [b for b in BEATS if t0 - 1e-3 <= b < t1]
    for j, b in enumerate(times):
        k = beat_index(b); count = k % 8
        n = noise.noise(Vector((b * 0.4, r.offset * 3.1, 0.0)))
        for half, tt in ((False, b), (True, b + P / 2)):
            if tt >= t1:
                break
            knee = (34 if not half else 14) * amp
            m = mirror * (1 if (k // 8) % 2 == 0 else -1)
            aR, aL = ("chest", amp, 0.0 if not half else 1.0), ("chest", amp, 0.0 if not half else 1.0)
            tilt, twist, head_tilt, lean, nod = 0.04 * m * (1 if k % 2 else -1), 0.0, 0.0, 0.18, 0.0
            if style in ("shoulder", "chorus") and count in (0, 1, 2, 3):
                if not half:
                    if (k % 2 == 0) == (m > 0):
                        aR = ("hit", amp)
                    else:
                        aL = ("hit", amp)
                    tilt *= 2; twist = math.radians(18) * (1 if k % 2 else -1) * m * amp
            if style == "chorus" and count in (4, 5, 6, 7):
                ph = (count - 4) / 3 + (0.15 if half else 0)
                if m > 0:
                    aR = ("across", amp, ph); aL = ("out", amp, 1 - ph)
                else:
                    aL = ("across", amp, ph); aR = ("out", amp, 1 - ph)
                twist = math.radians(20) * m * (ph - 0.5)
            if count in (1, 3, 5, 7) and not half:  # chest pop on 2 and 4
                lean = 0.35
            nod = 0.12 if not half else -0.02
            head_tilt = 0.06 * (1 if k % 2 else -1) * m + 0.03 * n
            p = pose(knee=knee, lean=lean, tilt=tilt, twist=twist, head_tilt=head_tilt, nod=nod, head_turn=head_turn + 0.05 * n,
                     armR=aR, armL=aL, wide=0.12, hip_roll=0.05 * m * (1 if k % 2 else -1))
            r.key(fr(tt), p, xy, yaw)



def track_keys(r, t0, t1, xy, yaw=0.0):
    """Real REDRED chorus: clip time t -> choreo frame (t - CH0)*24, no looping. Keys every 2 frames.
    Arms/torso/head at full track weight; legs 85% track + a light knee bounce on the beat."""
    V = c2.V
    for f in range(fr(t0), fr(t1) + 1, 2):
        t = (f - 1) / FPS
        g = max(1, min(int(round((t - CH0) * FPS)), int(round((T_HIT2 + 0.1 - CH0) * FPS))) + 1)  # freeze on the final hit
        k = beat_index(t); ph = (t - BEATS[k]) / P  # -0.5..0.5, 0 on the beat
        knee = 10 + 8 * (0.5 + 0.5 * math.cos(2 * math.pi * ph))
        p = pose(knee=knee, wide=0.12)
        sp = V("spine", g)
        p["LowerTorso"] = (Vector((0, 0, 1)).lerp(sp, 0.5), V("hip_fwd", g))
        p["UpperTorso"] = (sp, V("fwd", g))
        p["Head"] = (V("head_up", g), V("head_fwd", g))
        for s_, kk in ((".P", "R"), (".N", "L")):
            u, l = V("uarm" + kk, g), V("larm" + kk, g)
            p["UpperArm" + s_], p["LowerArm" + s_], p["Hand" + s_] = (u, None), (l, None), (l, None)
            th, sh = p["UpperLeg" + s_][0], p["LowerLeg" + s_][0]
            p["UpperLeg" + s_] = (th.lerp(V("uleg" + kk, g), 0.85).normalized(), None)
            p["LowerLeg" + s_] = (sh.lerp(V("lleg" + kk, g), 0.85).normalized(), None)
        r.key(f, p, xy, yaw, lag=False)  # tracked timing already has natural overlap; lag made arms late

def hold_keys(r, t0, t1, p, xy, yaw=0.0, step=P, breathe=0.03):
    t = t0
    while t < t1:
        q = dict(p); n = noise.noise(Vector((t * 0.5, r.offset * 2.3, 1.0)))
        q["Head"] = (q["Head"][0] + Vector((0.03 * n, 0, 0)), q["Head"][1])
        q["UpperTorso"] = (q["UpperTorso"][0] + Vector((0.02 * n, breathe * math.sin(t * 2.4), 0)), q["UpperTorso"][1])
        r.key(fr(t), q, xy, yaw); t += step


def walk_keys(r, t0, t1, a_xy, b_xy, spm=80, stride_amp=17, yaw0=0.0, yaw1=0.0, hero=False):
    """Walk from a_xy to b_xy (world), keyed every 2 frames. One foot always down."""
    f0, f1 = fr(t0), fr(t1)
    for f in range(f0, f1 + 1, 2):
        t = (f - 1) / FPS; u = (t - t0) / max(1e-3, t1 - t0)
        ph = math.sin(2 * math.pi * (t - t0) * spm / 120.0)  # one stride = 2 steps
        A = math.radians(stride_amp) * min(1.0, u * 6, (1 - u) * 6)
        p = pose(knee=12, lean=0.06, armR=("swing", 1.0, -ph * 0.9), armL=("swing", 1.0, ph * 0.9), wide=0.05)
        for s, sd in ((".P", 1), (".N", -1)):
            k = ph * sd
            th = nv(0.04 * sd, math.sin(A * k), -1); sh = nv(0.02 * sd, math.sin(A * k) - 0.35 * max(0.0, -k) * A * 2.5, -1)
            p["UpperLeg" + s], p["LowerLeg" + s] = (th, None), (sh, None)
        roll = 0.07 * ph
        p["LowerTorso"] = (nv(roll, 0.03, 1), rotz(Vector((0, 1, 0)), 0.1 * ph))
        p["UpperTorso"] = (nv(-roll * 0.6, 0.05 if hero else 0.1, 1), rotz(Vector((0, 1, 0)), -0.09 * ph))
        p["Head"] = (nv(0.0, -0.07 if hero else 0.0, 1), Vector((0, 1, 0.07 if hero else 0)))
        xy = (a_xy[0] + (b_xy[0] - a_xy[0]) * u, a_xy[1] + (b_xy[1] - a_xy[1]) * u)
        r.key(f, p, xy, yaw0 + (yaw1 - yaw0) * ease(u), dz=-0.025 * abs(ph) ** 0.5 if A > 0.05 else 0.0)


# positions (world x, y)
V_POS = [(-2.4, FRONT + 0.9), (-1.2, FRONT + 0.45), (0.0, FRONT), (1.2, FRONT + 0.45), (2.4, FRONT + 0.9)]
SIDE_POS = [(-3.9, FRONT + 0.7), (-2.8, FRONT + 1.2), (2.7, FRONT + 1.2), (3.8, FRONT + 0.7), (4.8, FRONT + 1.3)]
FORM_POS = [(-2.5, FRONT + 0.8), (-1.3, FRONT + 0.4), (0.0, FRONT + 2.0), (1.3, FRONT + 0.4), (2.5, FRONT + 0.8)]  # Suhaa clear at the front
SUHAA_START, SUHAA_MARK = (0.0, FRONT + 3.0), (0.0, FRONT - 0.1)


def dancer(r, i):
    amp = (0.97, 1.02, 1.0, 1.03, 0.96)[i]; mir = (1, -1, 1, -1, 1)[i]
    side = -1 if SIDE_POS[i][0] < 0 else 1
    look = math.radians(55) * -side  # yaw toward centre stage (yaw>0 turns world-left)
    groove_keys(r, 0.0, T_DROP - 0.7, V_POS[i], amp, mir)  # >=0.7 s to reach the hit pose (forearm jerks otherwise)
    hit = pose(knee=26, lean=0.1, tilt=0.06 * mir, armR=("up",) if mir > 0 else ("chest",), armL=("chest",) if mir > 0 else ("up",), nod=0.1)
    r.key(fr(T_DROP), hit, V_POS[i]); r.key(fr(T_DROP + 0.3), hit, V_POS[i])
    walk_keys(r, T_SIDE + 0.1, T_SIDE + 1.6, V_POS[i], SIDE_POS[i], spm=96, stride_amp=15, yaw0=0, yaw1=look)
    watch = pose(knee=16, lean=0.05, head_turn=math.radians(25) * -side, nod=-0.05, armR=("low",), armL=("low",))
    hold_keys(r, T_SIDE + 2.0, T_HERO - 0.2, watch, SIDE_POS[i], look, step=P * 2)
    walk_keys(r, T_HERO, T_FORM + 0.3, SIDE_POS[i], FORM_POS[i], spm=110, stride_amp=15, yaw0=look, yaw1=0)
    track_keys(r, T_FORM + 0.6, T_END, FORM_POS[i])  # holds choreo frame 0 until T_CHORUS, then the real chorus


def suhaa(r):
    stand = pose(knee=8, lean=0.0, hip_roll=0.08, tilt=0.04, armR=("low",), armL=("low",), nod=-0.05)
    hold_keys(r, 0.0, T_WALK - 0.05, stand, SUHAA_START, step=P * 2, breathe=0.02)
    walk_keys(r, T_WALK, T_HERO - 0.35, SUHAA_START, SUHAA_MARK, spm=80, stride_amp=17, hero=True)
    hero = pose(knee=10, lean=-0.03, hip_roll=0.12, tilt=0.06, head_tilt=-0.06, nod=-0.1, head_turn=math.radians(-10),
                armR=("hip",), armL=("low",))
    hold_keys(r, T_HERO, T_CHORUS - 0.9, hero, SUHAA_MARK, step=P * 2, breathe=0.015)
    track_keys(r, T_CHORUS - 0.4, T_END, SUHAA_MARK)  # 0.5 s blend from hero pose into choreo frame 0
    for o in [x for x in [r.a] + list(r.a.children_recursive) if not x.hide_viewport]:  # hidden until the silhouette
        for f, h in ((1, True), (fr(T_SIL) - 1, True), (fr(T_SIL), False)):
            o.hide_render = h; o.keyframe_insert("hide_render", frame=f)


def fabric(arms):
    """Cloth read: soft sheen + higher roughness on clothing materials (skin/face left alone)."""
    done = set()
    for a in arms:
        for o in a.children_recursive:
            for s in getattr(o, "material_slots", []):
                m = s.material
                if not m or m in done or not m.use_nodes or "face" in m.name.lower():
                    continue
                b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                if b is None:
                    continue
                done.add(m)
                for k, v in (("Sheen Weight", 0.35), ("Sheen Roughness", 0.5)):
                    if k in b.inputs:
                        b.inputs[k].default_value = v
                if not b.inputs["Roughness"].is_linked:
                    b.inputs["Roughness"].default_value = max(0.65, b.inputs["Roughness"].default_value)


def smooth_all():
    """Bezier + auto-clamped handles everywhere on the characters (no overshoot)."""
    for o in bpy.data.objects:
        if o.type != "ARMATURE":
            continue
        ad = o.animation_data
        if not ad or not ad.action:
            continue
        act = ad.action
        fcs = list(act.fcurves) if hasattr(act, "fcurves") else [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
        for fc in fcs:
            if fc.data_path.endswith("hide_render"):
                continue
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"; kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
            fc.update()


# ---------------------------------------------------------------- lights / camera
def lights(suhaa_obj):
    L = {}
    spb = P * FPS

    def cue(obj, keys, const=False):
        for t, e in keys:
            obj.data.energy = e; obj.data.keyframe_insert("energy", frame=max(1, fr(t)))
        if const:
            act = obj.data.animation_data.action
            fcs = list(act.fcurves) if hasattr(act, "fcurves") else [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
            for fc in fcs:
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
    for k, x in enumerate((-6, -3, 0, 3, 6)):  # beams: pan steps + energy pops on beats, off in the dark section
        s_ = spot(f"BeamW{k}", (x, STAGE_Y + 0.6, 7.5), (x * 0.4, -6, 0.5), 5000, (1, 0.97, 0.92), 12, 0.15); L[f"beam{k}"] = s_
        s_.data.volume_factor = 2.0
        r0 = s_.rotation_euler[1]; pops = []
        for j, b in enumerate(BEATS):
            if b < 0 or b > T_END:
                continue
            s_.rotation_euler[1] = r0 + (0.3 if (j + k) % 2 else -0.3); s_.keyframe_insert("rotation_euler", index=1, frame=fr(b))
            e = env(b) * (0.7 if b > T_CHORUS else 1.0); pops += [(b, 6500 * e), (b + 8 / FPS, 2400 * e)]  # chorus shots are tighter: less glare
        cue(s_, pops)
    for k, x in enumerate((-1.5, 1.5)):  # two beams through the entrance haze toward camera during the silhouette
        s_ = spot(f"HazeBeam{k}", (x, FRONT + 6.5, 6.5), (x * 0.3, FRONT - 6, 1.2), 0, (0.85, 0.9, 1.0), 9, 0.15); s_.data.volume_factor = 2.5
        cue(s_, [(0, 0), (T_SIL - 0.4, 0), (T_SIL + 1.5, 9000), (T_HERO, 9000), (T_HERO + 0.6, 2500)])
    for k, x in enumerate((-7, 7)):
        L[f"red{k}"] = spot(f"StageRed{k}", (x, STAGE_Y + 5, 7.5), (x * 0.3, STAGE_Y + 2, STAGE_Z), 7000, (1, 0.05, 0.04), 38, 0.5, 0.4)
    L["key"] = spot("StageKey", (0, STAGE_Y - 3.5, 6.5), (0, FRONT, STAGE_Z + 0.8), 5200, (1.0, 0.95, 0.88), 50, 0.45, 0.6)
    for k, (x, col) in enumerate(((-3.0, (0.75, 0.85, 1.0)), (3.0, (1, 0.15, 0.1)))):
        L[f"rim{k}"] = spot(f"Rim{k}", (x, STAGE_Y + 6.0, 6.0), (-x * 0.3, FRONT + 0.6, STAGE_Z + 1.2), 11000, col, 46, 0.4, 0.4)
    L["back"] = spot("EntranceBack", (0, FRONT + 9.0, STAGE_Z + 1.6), (0, FRONT - 2, STAGE_Z + 1.0), 0, (0.85, 0.9, 1.0), 24, 0.3, 0.2)
    L["face"] = spot("SuhaaFace", (0, STAGE_Y - 4.0, 5.0), (0, SUHAA_MARK[1], STAGE_Z + 1.1), 0, (1.0, 0.86, 0.6), 11, 0.3, 0.2)
    L["blue"] = spot("SideBlue", (0, FRONT + 3, 7.5), (0, FRONT + 0.8, STAGE_Z), 0, (0.2, 0.35, 1.0), 80, 0.6, 0.6)
    L["strobe"] = bpy.data.objects.new("Strobe", bpy.data.lights.new("Strobe", "AREA")); bpy.context.scene.collection.objects.link(L["strobe"])
    L["strobe"].data.size = 12; L["strobe"].location = (0, STAGE_Y + 1.0, 8.0); L["strobe"].data.energy = 0
    for k, (y, col) in enumerate(((-4, (1.0, 0.35, 0.3)), (-11, (0.6, 0.65, 1.0)))):
        ld = bpy.data.lights.new(f"CrowdFill{k}", "AREA"); ld.shape = "RECTANGLE"; ld.size, ld.size_y = 20, 6; ld.energy = 260; ld.color = col
        o = bpy.data.objects.new(f"CrowdFill{k}", ld); bpy.context.scene.collection.objects.link(o)
        o.location = (0, y + 1, 4.5); o.rotation_euler = (math.radians(-12), 0, 0)
    for nm in ("key", "red0", "red1", "rim0", "rim1"):
        e = L[nm].data.energy
        cue(L[nm], [(0, e), (T_DROP + 0.1, e), (T_DROP + 0.13, 0), (T_HERO - 0.01, 0), (T_HERO + 0.75, e * 1.15), (T_HERO + 1.5, e),
                    (T_HIT2 - 0.04, e), (T_HIT2, e * 1.3), (T_HIT2 + 0.4, e)])
    cue(L["blue"], [(0, 0), (T_DROP + 0.13, 0), (T_DROP + 0.5, 2800), (T_HERO, 2800), (T_HERO + 0.5, 0)])
    cue(L["back"], [(0, 0), (T_SIL - 0.2, 0), (T_SIL + 3.0, 80000), (T_HERO, 80000), (T_HERO + 0.8, 6000)])
    cue(L["face"], [(0, 0), (T_HERO - 0.01, 0), (T_HERO + 0.75, 3600), (T_FORM, 2600), (T_CHORUS, 1200)])
    sk = [(0, 0)]
    for k in range(4):
        t = T_DROP + k * 0.042 * 2; sk += [(t, 6000), (t + 0.042, 0)]
    sk += [(T_HERO, 7000), (T_HERO + 0.05, 0), (T_HIT2, 7000), (T_HIT2 + 0.05, 0), (T_HIT2 + 0.12, 5000), (T_HIT2 + 0.17, 0),
           (T_HIT2 + 0.25, 6000), (T_HIT2 + 0.3, 0)]
    cue(L["strobe"], sorted(sk), const=True)
    w = bpy.context.scene.world or bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.002, 0.002, 0.003, 1)


def camera(suhaa_obj):
    cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    tgt = empty("CamTarget", (0, 0, 0)); c = cam.constraints.new("TRACK_TO"); c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    foc = empty("Focus", (0, FRONT, 2.4)); cd.dof.use_dof = True; cd.dof.focus_object = foc
    sy0, sy1 = SUHAA_START[1], SUHAA_MARK[1]
    shots = [  # (t, cam, target, lens, focus, fstop)
        (0.0, (0, -8.0, 3.0), (0, FRONT, 2.4), 62, (0, FRONT, 2.4), 5.6),
        (T_SIL - 0.05, (0, -7.4, 3.0), (0, FRONT + 0.6, 2.4), 68, (0, FRONT, 2.4), 5.6),
        (T_SIL, (0, -7.0, 4.0), (0, sy0 - 0.5, 2.6), 70, (0, sy0, 2.6), 4.0),
        (T_WALK - 0.05, (0, -6.0, 3.8), (0, sy0 - 0.3, 2.6), 85, (0, sy0, 2.6), 4.0),
        (T_WALK, (0.9, 5.0, 2.0), (0, sy0, 2.5), 50, (0, sy0, 2.5), 2.8),
        (T_HERO - 0.05, (0.6, 4.2, 2.0), (0, sy1, 2.4), 60, (0, sy1, 2.4), 2.8),
        (T_HERO + 0.75, (0.55, 4.4, 2.0), (0, sy1, 2.45), 62, (0, sy1, 2.45), 2.8),
        (T_HERO + 0.8, (2.5, -8.0, 3.1), (0, FRONT, 2.2), 58, (0, FRONT, 2.2), 5.6),
        (T_CHORUS - 0.05, (2.0, -7.8, 3.1), (0, FRONT, 2.2), 60, (0, FRONT, 2.2), 5.6),
        (T_CHORUS, (0, -8.0, 3.0), (0, FRONT + 0.3, 2.3), 80, (0, FRONT, 2.4), 5.6),
        (17.5, (-3.0, -8.0, 3.0), (0, FRONT + 0.3, 2.3), 82, (0, FRONT, 2.4), 5.6),
        (24.0, (2.5, -7.6, 3.0), (0, FRONT + 0.3, 2.3), 80, (0, FRONT, 2.4), 5.6),
        (T_HIT2, (3.0, -8.0, 3.0), (0, FRONT + 0.3, 2.4), 85, (0, FRONT, 2.4), 5.6),
        (T_END, (0.0, -9.0, 3.2), (0, FRONT, 2.5), 52, (0, FRONT, 2.4), 5.6)]
    for t, p, look, lens, fo, fs in shots:
        f = fr(t); cam.location = p; cam.keyframe_insert("location", frame=f)
        tgt.location = look; tgt.keyframe_insert("location", frame=f); cd.lens = lens; cd.keyframe_insert("lens", frame=f)
        foc.location = fo; foc.keyframe_insert("location", frame=f); cd.dof.aperture_fstop = fs; cd.dof.keyframe_insert("aperture_fstop", frame=f)
    for o in (cam, tgt, foc, cd):  # linear: slow drifts, hard cuts between adjacent frames
        act = o.animation_data.action
        fcs = list(act.fcurves) if hasattr(act, "fcurves") else [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
        for fc in fcs:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def build():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    a = base.build_suhaa(); a.name = "Suhaa"
    for o in a.children_recursive:
        if o.type == "MESH" and o.dimensions.x > 1.5:
            o.hide_render = o.hide_viewport = True
    c2.venue(); back_crowd(); front_row3()
    old = c2.sec; c2.sec = lambda s_: fr(s_ + (T_HIT2 - 10.1)); c2.fx(); c2.sec = old  # CO2 + confetti on the 22.3 s hit
    scr = bpy.data.materials["ScreenM"]; scr.node_tree.animation_data_clear()
    es = scr.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for t, v in ((0, 1.6), (T_DROP + 0.1, 1.6), (T_DROP + 0.13, 0.12), (T_HERO - 0.01, 0.12), (T_HERO + 0.6, 2.4), (T_FORM, 1.6), (T_CHORUS + 0.5, 0.8),
                 (T_HIT2 - 0.04, 0.8), (T_HIT2, 1.8), (T_HIT2 + 0.5, 1.0)):
        es.default_value = v; es.keyframe_insert("default_value", frame=fr(t))
    mp = next(n for n in scr.node_tree.nodes if n.type == "MAPPING").inputs["Location"]
    mp.default_value = (0, 0, 0); mp.keyframe_insert("default_value", frame=1)
    mp.default_value = (0, 0, 6.0); mp.keyframe_insert("default_value", frame=END)
    lights(a)
    arms = [a]
    for i, name in enumerate(c2.STAGE):
        d = c2.load_avatar(name); arms.append(d)
        dancer(Rig(d, offset=(0, 1, 0, 2, 1)[i], seed=i), i)
    suhaa(Rig(a, offset=0, seed=9))
    fabric(arms); smooth_all()
    camera(a)
    base.render_setup(); sc = bpy.context.scene; sc.frame_end = END; sc.view_settings.exposure = 0.35
    sc.render.use_motion_blur = True
    try:
        sc.render.motion_blur_shutter = 0.5
    except Exception:
        pass
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "scene_v3.blend"))
    print("built v3")


def back_crowd():
    c2.back_crowd()
    o = bpy.data.objects["BackCrowd"]; me = o.data
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me)
    kill = [v for v in bm.verts if v.co.y > -12 and abs(v.co.x) < 10]  # nothing between the camera and the front row  # keep the camera's own space clear
    bmesh.ops.delete(bm, geom=kill, context="VERTS"); bm.to_mesh(me); bm.free()


def front_row3():
    c2.front_row()  # two packed rows; add a third behind
    rnd = random.Random(21)
    pool = sorted({os.path.join(ROOT, "gfx_output", "avatar_cache", n) for n in os.listdir(os.path.join(ROOT, "gfx_output", "avatar_cache"))
                   if n.endswith(".blend") and (n.startswith("fan_") or n[:-6] in ("Bio_IsHere", "DI3STINY", "ImmortalNico", "Qsi2408", "sttvr_l1ght"))})
    for k in range(18):
        x, y = -5.3 + 0.62 * k + rnd.uniform(-0.1, 0.1), BAR_Y - 1.6 + rnd.uniform(-0.1, 0.1)
        with bpy.data.libraries.load(pool[(k * 5 + 2) % len(pool)]) as (src, dst):
            dst.objects = src.objects
        arm = None
        for o in dst.objects:
            if o is not None:
                bpy.context.scene.collection.objects.link(o); arm = o if o.type == "ARMATURE" else arm
        if arm:
            arm.location = (x, y, 0); arm.rotation_euler = (0, 0, rnd.uniform(-0.4, 0.4))
            sc = rnd.uniform(0.95, 1.05); arm.scale = (0.28 * sc * (-1 if k % 2 else 1), 0.28 * sc, 0.28 * sc)
            base.wave_fcurve(arm, "location", 2, 0.05, P * FPS, rnd.uniform(0, 6.28), 0.05)


# ---------------------------------------------------------------- motion check (no render)
def check():
    sc = bpy.context.scene
    arms = [o for o in sc.objects if o.type == "ARMATURE" and (o.name == "Suhaa" or o.animation_data and o.animation_data.action and len(o.pose.bones) and o.location.y > STAGE_Y)]
    worst = []; slide = []
    prev = {}
    pfoot = {}
    for f in range(1, END + 1):
        sc.frame_set(f)
        for a in arms:
            for pb in a.pose.bones:
                m = (a.matrix_world @ pb.matrix).to_quaternion()
                k = (a.name, pb.name)
                if k in prev:
                    d = math.degrees(2 * math.acos(min(1.0, abs(m.dot(prev[k])))))
                    worst.append((d, a.name, pb.name, f))
                prev[k] = m
            for fb in ("Foot.P", "Foot.N"):
                w = a.matrix_world @ a.pose.bones[fb].tail
                k = (a.name, fb)
                if k in pfoot:
                    slide.append(((w - pfoot[k]).length, a.name, fb, f))
                pfoot[k] = w
    worst.sort(reverse=True)
    over = [w for w in worst if w[0] > 30]
    print("CHECK top bone turns/frame:")
    for w in worst[:12]:
        print("  %.1f deg %s %s f%d" % w)
    print("CHECK frames over 30deg:", len(over))
    arm = [w[0] for w in worst if fr(T_CHORUS) <= w[3] and w[2].startswith(("UpperArm", "LowerArm"))]
    print("CHECK chorus arm motion mean %.2f deg/frame" % (sum(arm) / max(1, len(arm))))
    from collections import Counter
    c = Counter((w[3] // 6) * 6 for w in over)
    print("CHECK over-30 by 6-frame bucket:", sorted(c.items()))
    c2_ = Counter(w[2] for w in over); print("CHECK over-30 by bone:", c2_.most_common(8))
    import statistics
    print("CHECK median turn %.2f deg, p99 %.2f" % (statistics.median(w[0] for w in worst), sorted(w[0] for w in worst)[int(len(worst) * 0.99)]))
    # match gate: armature-space bone directions vs the raw (unsmoothed) choreo over the chorus
    raw = json.load(open(os.path.join(ROOT, "gfx_output", "anim_concert", "ref", "choreo_full.json")))
    MAP = {"UpperTorso": "spine", "Head": "head_up", "UpperArm.P": "uarmR", "LowerArm.P": "larmR", "UpperArm.N": "uarmL",
           "LowerArm.N": "larmL", "UpperLeg.P": "ulegR", "LowerLeg.P": "llegR", "UpperLeg.N": "ulegL", "LowerLeg.N": "llegL"}
    cs = {b: [] for b in MAP}; part = {1: [], 2: []}
    for f in range(fr(T_CHORUS), fr(T_HIT2) + 1):
        g = int(round(((f - 1) / FPS - CH0) * FPS))
        if g >= raw["frames"]:
            break
        sc.frame_set(f)
        for a in arms:
            for b, key in MAP.items():
                pb = a.pose.bones[b]
                c_ = (pb.tail - pb.head).normalized().dot(Vector(raw[key][g])); cs[b].append(c_)
                if "Arm" in b:
                    part[1 if g < raw.get("seam", 1e9) else 2].append(c_)
    per = {b: sum(v) / len(v) for b, v in cs.items()}
    for b, v in per.items():
        print("CHECK match %-11s %.3f" % (b, v))
    m = sum(per.values()) / len(per)
    for k, v in part.items():
        print("CHECK arm match part %d: %.3f" % (k, sum(v) / max(1, len(v))))
    print("CHECK match mean %.3f (gate 0.60) %s; jitter frames over 30: %d (gate 0) %s"
          % (m, "PASS" if m >= 0.6 else "FAIL", len(over), "PASS" if not over else "FAIL"))


def stills(frames, pct=50):
    sc = bpy.context.scene; sc.render.resolution_percentage = pct
    for f in frames:
        sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "stills_v3", f"f{f:03d}.png")
        bpy.ops.render.render(write_still=True)


def frames(a, b, pct=100, sub="frames_v3"):
    sc = bpy.context.scene; sc.render.resolution_percentage = pct
    sc.frame_start, sc.frame_end = a, b; sc.render.filepath = os.path.join(OUT, sub, "f")
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    cmd = argv[0] if argv else "build"
    if cmd == "build":
        build()
    elif cmd == "check":
        check()
    elif cmd == "stills":
        stills([int(x) for x in argv[1].split(",")], int(argv[2]) if len(argv) > 2 else 50)
    elif cmd == "frames":
        frames(int(argv[1]), int(argv[2]), int(argv[3]) if len(argv) > 3 else 100, argv[4] if len(argv) > 4 else "frames_v3")
