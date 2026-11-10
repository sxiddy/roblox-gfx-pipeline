"""Per-frame motion baking for Roblox R15 avatars rigged by build_exact_gfx.py (bones LowerTorso, UpperTorso, Head,
UpperArm/LowerArm/Hand/UpperLeg/LowerLeg/Foot .P/.N; P = right, avatar faces +Y in armature space).

Layers, evaluated for every frame and keyed on every bone:
  1. clips   - real Roblox animations (library/anims/*.json from rbx_anim_json.py), cross-faded by weight
  2. acts    - acting poses (aim directions, like anim_door.pose_key items) slerped in with eased weights
  3. life    - breathing, idle weight shift, head micro-moves, talking head bobs
"""
import json, math, os
import bpy
from mathutils import Matrix, Quaternion, Vector

ANIMS = os.path.join(os.path.dirname(__file__), "..", "library", "anims")
R15 = {"LowerTorso": "LowerTorso", "UpperTorso": "UpperTorso", "Head": "Head"}
for side, s in (("Right", "P"), ("Left", "N")):
    for part in ("UpperArm", "LowerArm", "Hand", "UpperLeg", "LowerLeg", "Foot"):
        R15[side + part] = f"{part}.{s}"
# Roblox axes (+X right, +Y up, -Z forward) -> armature axes (+X right, +Z up, +Y forward)
M = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))


def smooth(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def window(f, a, b, fade=6):
    """1 inside [a, b], eased ramps of `fade` frames on both sides."""
    return smooth((f - a + fade) / fade) * smooth((b + fade - f) / fade)


class Clip:
    def __init__(self, name):
        d = json.load(open(os.path.join(ANIMS, name + ".json")))
        self.length = max(d["length"], 1e-3); self.tracks = {}
        for k in d["keys"]:
            for rb, cf in k["poses"].items():
                if rb in R15:
                    self.tracks.setdefault(R15[rb], []).append((k["t"], cf))

    def sample(self, t, loop=True):
        t = t % self.length if loop else min(t, self.length)
        out = {}
        for bone, keys in self.tracks.items():
            i = 0
            while i + 1 < len(keys) and keys[i + 1][0] <= t:
                i += 1
            t0, c0 = keys[i]; t1, c1 = keys[min(i + 1, len(keys) - 1)]
            u = 0.0 if t1 <= t0 else (t - t0) / (t1 - t0)
            q0, q1 = _q(c0), _q(c1)
            p = Vector(c0[:3]).lerp(Vector(c1[:3]), u)
            out[bone] = (q0.slerp(q1, u), M @ p)
        return out


def _q(cf):
    r = Matrix(((cf[3], cf[4], cf[5]), (cf[6], cf[7], cf[8]), (cf[9], cf[10], cf[11])))
    return (M @ r @ M.transposed()).to_quaternion()


class Actor:
    """Collects clip / act / life layers for one armature, then bakes them frame by frame."""

    def __init__(self, arm, base=(), personality=None):
        self.a = arm; self.clips = []; self.acts = []; self.base = list(base); self.talk = []
        self.p = {"breath": 1.0, "sway": 1.0, "head": 1.0, **(personality or {})}
        self.rest = {pb.name: pb.bone.matrix_local.to_3x3() for pb in arm.pose.bones}

    def clip(self, name, f0, f1, speed=1.0, offset=0.0, fade=6, weight=1.0, loop=True, bones=None):
        self.clips.append((Clip(name), f0, f1, speed, offset, fade, weight, loop, bones))

    def act(self, f0, f1, items, fade=6, weight=1.0):
        self.acts.append((f0, f1, items, fade, weight))

    def talking(self, f0, f1, energy=1.0):
        self.talk.append((f0, f1, energy))

    # --------------------------------------------------------------- evaluation
    def _aim(self, bone, d, hint):
        bpy.context.view_layer.update(); pb = self.a.pose.bones[bone]
        y = Vector(d).normalized(); h = Vector(hint); z = h - h.dot(y) * y
        if z.length < 0.2:
            h = Vector((0, 0, 1)) if abs(y.z) < 0.9 else Vector((0, 1, 0)); z = h - h.dot(y) * y
        z.normalize(); x = y.cross(z)
        m = Matrix((x, y, z)).transposed().to_4x4(); m.translation = pb.head
        pb.matrix = m

    def _apply_items(self, items, w):
        """Slerp each listed bone from its current rotation toward the aimed one by weight w (parents first)."""
        if w <= 0.001:
            return
        have = {i[0] for i in items}
        for item in items:
            bone, d, hint = item if len(item) == 3 else (*item, (0, 1, 0))
            pb = self.a.pose.bones[bone]; q0 = pb.rotation_quaternion.copy()
            self._aim(bone, d, hint); q1 = pb.rotation_quaternion.copy()
            pb.rotation_quaternion = q0.slerp(q1, w)
            hand = bone.replace("LowerArm", "Hand")
            if bone.startswith("LowerArm") and hand not in have:  # keep the hand in line with the forearm
                hb = self.a.pose.bones[hand]; hq0 = hb.rotation_quaternion.copy()
                self._aim(hand, d, (0, 0, 1) if abs(Vector(d).normalized().z) < 0.9 else (0, 1, 0))
                hb.rotation_quaternion = hq0.slerp(hb.rotation_quaternion.copy(), w)

    def pose_at(self, f, fps):
        a = self.a
        for pb in a.pose.bones:
            pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = Quaternion(); pb.location = Vector()
        # 1. clips, cross-faded
        rot = {}; loc = {}; wsum = {}
        for c, f0, f1, speed, off, fade, weight, loop, bones in self.clips:
            w = window(f, f0, f1, fade) * weight
            if w <= 0.001:
                continue
            for bone, (q, p) in c.sample(off + (f - f0) / fps * speed, loop).items():
                if bones and bone not in bones:
                    continue
                B = self.rest[bone]; ql = (B.inverted() @ q.to_matrix() @ B).to_quaternion()
                s = wsum.get(bone, 0.0) + w; k = w / s; wsum[bone] = s
                rot[bone] = rot.get(bone, Quaternion()).slerp(ql, k)
                if bone == "LowerTorso":
                    loc[bone] = loc.get(bone, Vector()).lerp(B.inverted() @ p, k)
        for bone, q in rot.items():
            pb = a.pose.bones[bone]
            pb.rotation_quaternion = Quaternion().slerp(q, min(1.0, wsum[bone]))
        if "LowerTorso" in loc:
            a.pose.bones["LowerTorso"].location = loc["LowerTorso"] * min(1.0, wsum["LowerTorso"])
        # 2. personality base pose (partly under clips: weight 0.55 while a clip drives that bone) and acting
        if self.base:
            for item in self.base:
                self._apply_items([item], 0.55 if item[0] in rot else 1.0)
        for f0, f1, items, fade, weight in self.acts:
            self._apply_items(items, window(f, f0, f1, fade) * weight)
        # 3. life: breathing, weight shift, head micro-moves, talking
        t = f / fps; p = self.p
        def add(bone, axis, ang):
            pb = a.pose.bones[bone]; pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(axis, ang)
        add("UpperTorso", (1, 0, 0), math.radians(1.6 * p["breath"]) * math.sin(2 * math.pi * t / 3.6))
        add("LowerTorso", (0, 1, 0), math.radians(1.4 * p["sway"]) * math.sin(2 * math.pi * t / 5.3 + 1.1))
        add("Head", (0, 0, 1), math.radians(2.5 * p["head"]) * math.sin(2 * math.pi * t / 4.1 + 0.4)
            + math.radians(1.2 * p["head"]) * math.sin(2 * math.pi * t / 1.7))
        add("Head", (1, 0, 0), math.radians(1.5 * p["head"]) * math.sin(2 * math.pi * t / 3.1 + 2.0))
        for f0, f1, e in self.talk:
            w = window(f, f0, f1, 4)
            if w > 0:  # syllable-rate nods and a slower tilt while the line plays
                add("Head", (1, 0, 0), w * e * math.radians(4.5) * math.sin(2 * math.pi * t * 3.3) ** 2)
                add("Head", (0, 1, 0), w * e * math.radians(3.0) * math.sin(2 * math.pi * t * 0.9))
                add("UpperTorso", (1, 0, 0), w * e * math.radians(1.5) * math.sin(2 * math.pi * t * 1.6))

    def bake(self, frames, fps):
        sc = bpy.context.scene
        for f in frames:
            self.pose_at(f, fps); bpy.context.view_layer.update()
            for pb in self.a.pose.bones:
                pb.keyframe_insert("rotation_quaternion", frame=f); pb.keyframe_insert("location", frame=f)
