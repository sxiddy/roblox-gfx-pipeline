"""Concert v2 (12 s, one continuous camera move, owner's REDRED mp3):
  0-2.2 s   five blocky Roblox members dance the opening (choreo tracked from the owner's reference video with MediaPipe)
  2.2-3.2   they step aside, stage dims
  3.2-4.2   backlight snaps on upstage; Suhaa walks out of the dark into the centre gap
  4.2-12    all six do the main choreo, travel forward (8.1), final wide shape (10.1) with CO2 jets + confetti
Members wear outfits read from the reference video (original faces, no likeness). Crowd: ~500 blocky fans + cached real
project avatars in the front row. Runs in its own headless Blender:
  blender -b --factory-startup -P tools/anim_concert2.py -- build
  blender -b gfx_output/anim_concert2/scene.blend -P tools/anim_concert2.py -- stills 1,60,90,130,200,260 [pct]
  blender -b gfx_output/anim_concert2/scene.blend -P tools/anim_concert2.py -- frames [a b]
"""
import sys, os, math, json, random, glob
import bpy
from mathutils import Vector, Matrix, Quaternion

ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
sys.path.insert(0, os.path.join(ROOT, "tools"))
import anim_concert as base
from anim_concert import mat, cube, empty, wave_fcurve, upd, spot

OUT = os.path.join(ROOT, "gfx_output", "anim_concert2")
os.makedirs(OUT, exist_ok=True)
FPS, END, BPM = 24, 285, 120
STAGE_Y, STAGE_Z = 5.5, 1.3
FRONT = STAGE_Y + 2.4          # members' front line
BAR_Y = 1.0                    # barricade
CH = json.load(open(os.path.join(ROOT, "gfx_output", "anim_concert", "ref", "choreo.json")))


def _smooth(r=4):
    """Gaussian-smooth every tracked direction over +-r frames and renormalise."""
    w = [math.exp(-(k / (r / 1.6)) ** 2) for k in range(-r, r + 1)]
    for key, v in list(CH.items()):
        if not isinstance(v, list):
            continue
        n = len(v); out = []
        for i in range(n):
            acc = Vector(); ws = 0.0
            for k, wk in zip(range(-r, r + 1), w):
                acc += wk * Vector(v[min(n - 1, max(0, i + k))]); ws += wk
            out.append(list((acc / ws).normalized()))
        CH[key] = out


_smooth()
V = lambda key, f: Vector(CH[key][max(0, min(CH["frames"] - 1, f - 1))])
BEAT = lambda t: t * BPM / 60.0
LAGS = {"LowerTorso": 0, "UpperTorso": 1, "Head": 2, "UpperArm": 2, "LowerArm": 3, "Hand": 4, "UpperLeg": 0, "LowerLeg": 0, "Foot": 0}
sec = lambda s: int(round(s * FPS)) + 1


def basis(z, y_hint):
    z = Vector(z).normalized(); y = Vector(y_hint); y = y - y.dot(z) * z
    if y.length < 1e-3:
        y = Vector((0, 1, 0)) if abs(z.y) < 0.9 else Vector((0, 0, 1)); y = y - y.dot(z) * z
    y.normalize(); x = y.cross(z)
    return Matrix((x, y, z)).transposed()


def ease(u):
    u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)


def path(keys, t):
    """keys = [(time, x, y)], eased between keys."""
    if t <= keys[0][0]:
        return keys[0][1:]
    for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = ease((t - t0) / (t1 - t0)); return tuple(p + (q - p) * u for p, q in zip(a, b))
    return keys[-1][1:]


# ---------------------------------------------------------------- members (outfits read from the reference video)
STAGE = ["street_8169968523", "street_8482641605", "street_10961195698", "street_8935233157", "street_8736472562"]  # left to right:
# male streetwear avatars of real Roblox users (avatar-3d exports rigged by cache_avatar.py)


def load_avatar(name):
    with bpy.data.libraries.load(os.path.join(ROOT, "gfx_output", "avatar_cache", name + ".blend")) as (src, dst):
        dst.objects = src.objects
    arm = None
    for o in dst.objects:
        if o is not None:
            bpy.context.scene.collection.objects.link(o)
            arm = o if o.type == "ARMATURE" else arm
    return arm


def drive_member2(parts, keys, lag=0):
    root = parts["root"]; Lt, Ls = parts["Lt"], parts["Ls"]
    for f in range(1, END + 1):
        g = f - lag; t = f / FPS
        spine, fwd, hfwd = V("spine", g), V("fwd", g), V("hip_fwd", g)
        Rh = basis(spine, fwd); parts["hip"].rotation_quaternion = Rh.to_quaternion()
        Rn = basis(V("head_up", g).lerp(spine, 0.4), V("head_fwd", g))
        parts["neck"].rotation_quaternion = (Rh.transposed() @ Rn).to_quaternion()
        lows = []
        for s in ("R", "L"):
            Ru = basis(-V("uarm" + s, g), fwd); Rl = basis(-V("larm" + s, g), fwd)
            parts["sh" + s].rotation_quaternion = (Rh.transposed() @ Ru).to_quaternion()
            parts["el" + s].rotation_quaternion = (Ru.transposed() @ Rl).to_quaternion()
            Rt = basis(-V("uleg" + s, g), hfwd); Rs = basis(-V("lleg" + s, g), hfwd)
            parts["leg" + s].rotation_quaternion = Rt.to_quaternion()
            parts["kn" + s].rotation_quaternion = (Rt.transposed() @ Rs).to_quaternion()
            lows.append((parts["hipj"][s] + Rt @ Vector((0, 0, -Lt)) + Rs @ Vector((0, 0, -Ls))).z)
        x, y = path(keys, t)
        root.location = (x, y, STAGE_Z - min(lows))
        for o in (root, parts["hip"], parts["neck"], parts["shR"], parts["shL"], parts["elR"], parts["elL"],
                  parts["legR"], parts["legL"], parts["knR"], parts["knL"]):
            o.keyframe_insert("rotation_quaternion", frame=f)
        root.keyframe_insert("location", frame=f)


SKIN = (0.95, 0.82, 0.7)


def member(i, look, S=0.28 * 0.82):
    """Root local = avatar space (+X right, +Y forward, +Z up). Root is turned 180 deg so the member faces the crowd."""
    n = f"M{i}"; root = empty(n, (0, FRONT, STAGE_Z)); root.rotation_euler = (0, 0, math.pi)
    top, pants, skin, hair = mat(n + "Top", look["top"], 0.7), mat(n + "Pants", look["pants"], 0.85), mat(n + "Skin", SKIN, 0.5), mat(n + "Hair", look["hair"], 0.45)
    shoe, sole = mat(n + "Shoe", (0.92, 0.92, 0.9), 0.5), mat(n + "Sole", (0.1, 0.1, 0.1), 0.6)
    hip = empty(n + "_Hip", (0, 0, 2 * S), root)
    cube(n + "_Torso", (2 * S, S, 2 * S), (0, 0, S), top, hip, bevel=0.03 * S)
    if look.get("tee"):  # open jacket over a tee
        cube(n + "_Tee", (0.8 * S, 1.02 * S, 1.9 * S), (0, 0, S), mat(n + "Tee", look["tee"], 0.7), hip)
    if look.get("print"):
        cube(n + "_Print", (1.1 * S, 0.04 * S, 0.8 * S), (0, 0.5 * S, 1.15 * S), mat(n + "Print", look["print"], 0.6), hip)
    if look.get("stripe"):  # track jacket zip
        cube(n + "_Zip", (0.08 * S, 0.04 * S, 1.95 * S), (0, 0.51 * S, S), mat(n + "Stripe", look["stripe"], 0.5), hip)
    neck = empty(n + "_Neck", (0, 0, 2 * S), hip)
    cube(n + "_Head", (1.2 * S, 1.2 * S, 1.2 * S), (0, 0, 0.6 * S), skin, neck, bevel=0.07 * S)
    eye, mouth = mat(n + "Eye", (0.02, 0.02, 0.02), 0.3), mat(n + "Mouth", (0.35, 0.12, 0.12), 0.5)
    for ex in (-0.24, 0.24):
        cube(f"{n}_Eye{ex}", (0.13 * S, 0.03 * S, 0.22 * S), (ex * S, 0.6 * S, 0.62 * S), eye, neck)
        cube(f"{n}_Brow{ex}", (0.22 * S, 0.03 * S, 0.05 * S), (ex * S, 0.6 * S, 0.85 * S), eye, neck)
    cube(n + "_Mouth", (0.25 * S, 0.03 * S, 0.04 * S), (0, 0.6 * S, 0.33 * S), mouth, neck)
    cube(n + "_HairTop", (1.34 * S, 1.34 * S, 0.45 * S), (0, -0.04 * S, 1.2 * S), hair, neck, bevel=0.1 * S)
    cube(n + "_HairBack", (1.34 * S, 0.35 * S, 1.0 * S if look["style"] == "long" else 0.75 * S), (0, -0.52 * S, 0.8 * S), hair, neck, bevel=0.06 * S)
    for sx in (-1, 1):
        cube(f"{n}_HairSide{sx}", (0.18 * S, 1.1 * S, 0.7 * S), (sx * 0.64 * S, -0.05 * S, 0.85 * S), hair, neck, bevel=0.04 * S)
    if look["style"] == "fringe":
        cube(n + "_Fringe", (1.2 * S, 0.2 * S, 0.35 * S), (0, 0.58 * S, 1.02 * S), hair, neck, bevel=0.05 * S)
    elif look["style"] == "side":
        cube(n + "_Fringe", (0.85 * S, 0.2 * S, 0.3 * S), (0.18 * S, 0.58 * S, 1.05 * S), hair, neck, bevel=0.05 * S)
    else:
        cube(n + "_Fringe", (1.2 * S, 0.2 * S, 0.45 * S), (0, 0.58 * S, 0.98 * S), hair, neck, bevel=0.05 * S)
    parts = {"root": root, "hip": hip, "neck": neck, "S": S}
    for side, sx in (("R", 1), ("L", -1)):
        sh = empty(f"{n}_Sh{side}", (sx * 1.5 * S, 0, 1.85 * S), hip)
        cube(f"{n}_UArm{side}", (0.95 * S, 0.95 * S, 1.0 * S), (0, 0, -0.45 * S), top, sh, bevel=0.02 * S)
        el = empty(f"{n}_El{side}", (0, 0, -0.95 * S), sh)
        cube(f"{n}_LArm{side}", (0.92 * S, 0.92 * S, 0.8 * S), (0, 0, -0.4 * S), top, el, bevel=0.02 * S)
        cube(f"{n}_Hand{side}", (0.8 * S, 0.8 * S, 0.32 * S), (0, 0, -0.95 * S), skin, el, bevel=0.04 * S)
        if look.get("stripe"):
            sm = bpy.data.materials[n + "Stripe"]
            cube(f"{n}_StrU{side}", (0.06 * S, 0.97 * S, 1.0 * S), (sx * 0.47 * S, 0, -0.45 * S), sm, sh)
            cube(f"{n}_StrL{side}", (0.06 * S, 0.94 * S, 0.8 * S), (sx * 0.47 * S, 0, -0.4 * S), sm, el)
        lg = empty(f"{n}_Leg{side}", (sx * 0.5 * S, 0, 2 * S), root)
        cube(f"{n}_ULeg{side}", (S, S, 1.05 * S), (0, 0, -0.5 * S), bpy.data.materials[n + "Pants"], lg)
        if look.get("pockets"):
            cube(f"{n}_Pocket{side}", (0.06 * S, 0.5 * S, 0.45 * S), (sx * 0.53 * S, 0, -0.6 * S), bpy.data.materials[n + "Pants"], lg, bevel=0.02 * S)
        kn = empty(f"{n}_Kn{side}", (0, 0, -S), lg)
        cube(f"{n}_LLeg{side}", (0.98 * S, 0.98 * S, 0.9 * S), (0, 0, -0.45 * S), bpy.data.materials[n + "Pants"], kn)
        cube(f"{n}_Shoe{side}", (1.04 * S, 1.3 * S, 0.24 * S), (0, 0.1 * S, -0.88 * S), shoe, kn, bevel=0.05 * S)
        cube(f"{n}_Sole{side}", (1.06 * S, 1.32 * S, 0.06 * S), (0, 0.1 * S, -1.0 * S), sole, kn)
        parts.update({"sh" + side: sh, "el" + side: el, "leg" + side: lg, "kn" + side: kn})
    for o in [root, hip, neck] + [parts[k] for k in parts if k[:2] in ("sh", "el", "le", "kn")]:
        o.rotation_mode = "QUATERNION"
    root.rotation_quaternion = Quaternion((0, 0, 1), math.pi)
    return parts


def drive_member(parts, keys, lag=0):
    S = parts["S"]; root = parts["root"]
    for f in range(1, END + 1):
        g = f - lag; t = f / FPS
        spine, fwd, hfwd = V("spine", g), V("fwd", g), V("hip_fwd", g)
        Rh = basis(spine, fwd); parts["hip"].rotation_quaternion = Rh.to_quaternion()
        Rn = basis(V("head_up", g).lerp(spine, 0.4), V("head_fwd", g))
        parts["neck"].rotation_quaternion = (Rh.transposed() @ Rn).to_quaternion()
        lows = []
        for s, sx in (("R", 1), ("L", -1)):
            Ru = basis(-V("uarm" + s, g), fwd); Rl = basis(-V("larm" + s, g), fwd)
            parts["sh" + s].rotation_quaternion = (Rh.transposed() @ Ru).to_quaternion()
            parts["el" + s].rotation_quaternion = (Ru.transposed() @ Rl).to_quaternion()
            Rt = basis(-V("uleg" + s, g), hfwd); Rs = basis(-V("lleg" + s, g), hfwd)
            parts["leg" + s].rotation_quaternion = Rt.to_quaternion()
            parts["kn" + s].rotation_quaternion = (Rt.transposed() @ Rs).to_quaternion()
            foot = Vector((sx * 0.5 * S, 0, 2 * S)) + Rt @ Vector((0, 0, -S)) + Rs @ Vector((0, 0, -1.03 * S))
            lows.append(foot.z)
        x, y = path(keys, t)
        root.location = (x, y, STAGE_Z - min(lows))
        for o in (root, parts["hip"], parts["neck"], parts["shR"], parts["shL"], parts["elR"], parts["elL"],
                  parts["legR"], parts["legL"], parts["knR"], parts["knL"]):
            o.keyframe_insert("rotation_quaternion", frame=f)
        root.keyframe_insert("location", frame=f)


# ---------------------------------------------------------------- Suhaa: walks out of the dark, then joins the choreo
def aim(a, bone, d, hint=(0, 1, 0)):
    pb = a.pose.bones[bone]; upd()
    y = Vector(d).normalized(); h = Vector(hint); z = h - h.dot(y) * y
    if z.length < 0.2:
        h = Vector((0, 0, 1)) if abs(y.z) < 0.9 else Vector((0, 1, 0)); z = h - h.dot(y) * y
    z.normalize(); x = y.cross(z)
    m = Matrix((x, y, z)).transposed().to_4x4(); m.translation = pb.head
    pb.matrix = m


SUHAA_PATH = [(0.0, 0.0, FRONT + 3.2), (2.5, 0.0, FRONT + 3.2), (4.7, 0.0, FRONT - 0.35), (8.13, 0.0, FRONT - 0.35),
              (9.9, 0.0, FRONT - 1.25), (12.0, 0.0, FRONT - 1.25)]
WALK = (2.5, 4.7)  # unhurried strut, ~1.6 m/s


def drive_suhaa(a, keys=None, lag=0, walk=True, amp=1.0, head_bias=0.0, groove_ph=0.0):
    for pb in a.pose.bones:
        pb.rotation_mode = "QUATERNION"
    a.rotation_euler = (0, 0, math.pi)
    upd(); foot0 = min((a.matrix_world @ a.pose.bones[b].tail).z for b in ("Foot.P", "Foot.N"))  # rest: mesh low = 0
    for f in range(1, END + 1):
        t = f / FPS
        for pb in a.pose.bones:
            pb.rotation_quaternion = Quaternion()
        upd()
        w = ease((t - 4.6) / 0.5) if walk else 1.0  # blend from walk into the choreo
        if walk and t < 5.1:  # confident strut, 2 steps per beat-pair
            ph = math.sin(2 * math.pi * (t - WALK[0]) * 1.6) if WALK[0] <= t <= WALK[1] else 0.0
            for s, sx in ((".P", 1), (".N", -1)):
                k = ph * sx
                aim(a, "UpperTorso", (0, 0.08, 1)); aim(a, "Head", (0, -0.05, 1), (0, 1, 0))
                aim(a, "UpperLeg" + s, (0.04 * sx, 0.45 * k, -1)); aim(a, "LowerLeg" + s, (0, 0.45 * k - 0.35 * max(0, -k), -1))
                aim(a, "Foot" + s, (0, 1, 0), (0, 0, 1))
                aim(a, "UpperArm" + s, (0.18 * sx, -0.45 * k, -0.9)); aim(a, "LowerArm" + s, (0.1 * sx, -0.3 * k + 0.25, -0.9))
                aim(a, "Hand" + s, (0.1 * sx, -0.3 * k + 0.25, -0.9), (0, 0, 1))
        if w > 0:
            g0 = f - lag
            G = lambda b: min(END, max(1, g0 - LAGS[b]))  # follow-through: extremities trail the hips
            bt = BEAT(t) + groove_ph; sw = math.sin(math.pi * bt)
            q0 = {pb.name: pb.rotation_quaternion.copy() for pb in a.pose.bones}
            down = Vector((0, 0, -1))
            A = lambda v: down.lerp(v, amp).normalized()  # per-dancer amplitude around arms-down
            gL, gU, gH = G("LowerTorso"), G("UpperTorso"), G("Head")
            aim(a, "LowerTorso", Vector((0, 0, 1)).lerp(V("spine", gL), 0.4) + Vector((0.09 * sw, 0, 0)), V("hip_fwd", gL))  # weight shift
            aim(a, "UpperTorso", V("spine", gU) + Vector((-0.06 * sw, 0.18, 0)), V("fwd", gU))  # forward lean + counter-roll  # counter-roll
            nod = 0.12 * (1 - abs(math.sin(math.pi * bt))) ** 3
            aim(a, "Head", V("head_up", gH).lerp(V("spine", gH), 0.5) + Vector((head_bias, -nod, 0)), V("head_fwd", gH))
            for s, k in ((".P", "R"), (".N", "L")):
                aim(a, "UpperArm" + s, A(V("uarm" + k, G("UpperArm")))); aim(a, "LowerArm" + s, A(V("larm" + k, G("LowerArm"))))
                flick = 0.3 * (0.5 + 0.5 * math.sin(math.pi * 2 * bt - 1.2))
                aim(a, "Hand" + s, A(V("larm" + k, G("Hand"))) + Vector((0, flick, 0)), (0, 0, 1))
                aim(a, "UpperLeg" + s, V("uleg" + k, min(END, max(1, g0))) + Vector((0.12 * (1 if s == ".P" else -1), 0.12, 0)))  # wide stance, knees forward
                ll = V("lleg" + k, min(END, max(1, g0))) + Vector((0, -0.32, 0))  # deep loose knee bend like the CORTIS film, never locked
                aim(a, "LowerLeg" + s, ll)
                aim(a, "Foot" + s, V("foot" + k, min(END, max(1, g0))) + Vector((0, 0.6, 0)), (0, 0, 1))
            if w < 1:
                for pb in a.pose.bones:
                    pb.rotation_quaternion = q0[pb.name].slerp(pb.rotation_quaternion, w)
        x, y = path(keys or SUHAA_PATH, t)
        a.location = (x, y, STAGE_Z); upd()
        low = min((a.matrix_world @ a.pose.bones[b].tail).z for b in ("Foot.P", "Foot.N"))
        a.location.z += (STAGE_Z + foot0) - low
        if w > 0:  # groove: dip on every beat, sway over two beats
            bt = BEAT(t) + groove_ph
            a.location.z -= w * 0.07 * amp * (1 - abs(math.sin(math.pi * bt))) ** 2
            a.location.x += w * 0.06 * amp * math.sin(math.pi * bt)
        for pb in a.pose.bones:
            pb.keyframe_insert("rotation_quaternion", frame=f)
        a.keyframe_insert("location", frame=f)
    if not walk:
        return
    show = sec(2.6)  # she does not exist on stage until the lights are down and she walks out of the dark
    for o in [x for x in [a] + list(a.children_recursive) if not x.hide_viewport]:  # leave hidden accessories hidden
        for f, h in ((1, True), (show - 1, True), (show, False)):
            o.hide_render = h; o.keyframe_insert("hide_render", frame=f)


# ---------------------------------------------------------------- venue, crowd, FX
def env(t):
    """Stage brightness: blackout for Suhaa's entrance (2.7-4.2 s) and a 2-frame cut before the CO2 (10.1 s)."""
    if 2.7 <= t < 4.2 or 10.0 <= t < 10.1:
        return 0.02
    return 1.0


def led_mat(name, scale=6.0, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1); b.inputs["Roughness"].default_value = 0.25
    tc = nt.nodes.new("ShaderNodeTexCoord"); ck = nt.nodes.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = scale
    ck.inputs["Color1"].default_value = (1, 0.05, 0.04, 1); ck.inputs["Color2"].default_value = (0.02, 0.0, 0.0, 1)
    nt.links.new(tc.outputs["Generated"], ck.inputs["Vector"]); nt.links.new(ck.outputs["Color"], b.inputs["Emission Color"])
    es = b.inputs["Emission Strength"]
    for k in range(int(END / FPS * BPM / 60) + 1):  # pulse on every beat
        f = 1 + k * FPS * 60 / BPM
        e = strength * env(f / FPS)
        es.default_value = e; es.keyframe_insert("default_value", frame=f)
        es.default_value = e * 0.15; es.keyframe_insert("default_value", frame=f + 9)
    return m


def venue():
    steel, dark = mat("BarSteel", (0.55, 0.56, 0.58), 0.3, 0.9), mat("BarDark", (0.07, 0.07, 0.08), 0.6, 0.6)
    cube("BarRail", (14, 0.09, 0.05), (0, BAR_Y, 1.1), steel)
    cube("BarPanel", (14, 0.03, 0.95), (0, BAR_Y + 0.03, 0.58), dark)
    for k in range(-7, 8):
        cube(f"BarPost{k}", (0.05, 0.06, 1.1), (k * 1.0, BAR_Y + 0.02, 0.55), steel)
    cube("Floor", (70, 70, 0.02), (0, 0, -0.01), mat("Floor", (0.015, 0.015, 0.017), 0.35))
    cube("StageDeck", (18, 9, STAGE_Z - 0.02), (0, STAGE_Y + 4.5, (STAGE_Z - 0.02) / 2), mat("Deck", (0.02, 0.02, 0.022), 0.4, 0.2))
    cube("LEDFloor", (16, 7, 0.02), (0, STAGE_Y + 4.0, STAGE_Z - 0.01), led_mat("LEDFloorM", 40, 0.6))
    cube("StageLip", (18, 0.04, 0.08), (0, STAGE_Y - 0.02, STAGE_Z - 0.1), mat("LipLED", (0, 0, 0), 0.3, emit=(1, 0.08, 0.06), strength=6))
    scr = base.screen_mat(); es = scr.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for t, v in ((0, 1.6), (2.4, 1.6), (2.7, 0.03), (4.17, 0.03), (4.21, 2.4), (4.8, 1.6), (9.96, 1.6), (10.0, 0), (10.08, 0), (10.1, 2.2)):
        es.default_value = v; es.keyframe_insert("default_value", frame=sec(t))
    cube("Screen", (14, 0.1, 6.0), (0, STAGE_Y + 8.6, STAGE_Z + 3.6), scr)
    for sx in (-1, 1):
        cube(f"SideScreen{sx}", (0.1, 4.0, 3.0), (sx * 10.5, STAGE_Y + 1.0, 5.0), scr)
        cube(f"Speaker{sx}", (1.0, 0.9, 3.2), (sx * 8.4, STAGE_Y - 0.6, 5.4), mat("Spk", (0.02, 0.02, 0.02), 0.6))
    tm = mat("Truss", (0.12, 0.12, 0.13), 0.45, 0.8)
    for ty in (STAGE_Y + 0.6, STAGE_Y + 5):
        cube(f"Truss{ty:.0f}", (18, 0.3, 0.3), (0, ty, 7.8), tm)
    # haze
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 6)); hz = bpy.context.active_object; hz.name = "Haze"; hz.scale = (44, 56, 12)
    hm = bpy.data.materials.new("HazeM"); hm.use_nodes = True; nt = hm.node_tree; nt.nodes.clear()
    vs = nt.nodes.new("ShaderNodeVolumePrincipled"); vs.inputs["Density"].default_value = 0.026; vs.inputs["Anisotropy"].default_value = 0.6
    mo = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(vs.outputs[0], mo.inputs["Volume"]); hz.data.materials.append(hm)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, FRONT + 3.2, STAGE_Z + 1.6)); h2 = bpy.context.active_object
    h2.name = "HazeEntrance"; h2.scale = (6, 4, 3.2); hm2 = hm.copy(); h2.data.materials.append(hm2)
    hm2.node_tree.nodes["Principled Volume"].inputs["Density"].default_value = 0.09


def back_crowd(count=480):
    """No bodies behind the front row: only phones and red lightsticks glowing in the dark, so the rows read as endless."""
    import bmesh
    rnd = random.Random(5); me = bpy.data.meshes.new("BackCrowd"); bm = bmesh.new()
    for k in range(count):
        y = -rnd.uniform(0.9, 26) ** 1.0; x = rnd.uniform(-7, 7) * (1 + (-y) / 12)
        z = rnd.uniform(1.75, 2.45); red = rnd.random() < 0.55
        r = bmesh.ops.create_cube(bm, size=1.0)["verts"]
        sz = (0.045, 0.045, 0.28) if red else (0.07, 0.015, 0.13)
        for v in r:
            v.co = Vector((v.co.x * sz[0] + x, v.co.y * sz[1] + y, v.co.z * sz[2] + z))
        for fc in {f for v in r for f in v.link_faces}:
            fc.material_index = 1 if red else 0
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new("BackCrowd", me); bpy.context.scene.collection.objects.link(o)
    me.materials.append(mat("BCPhone", (0, 0, 0), 0.4, emit=(0.85, 0.9, 1.0), strength=4))
    me.materials.append(mat("BCStick", (0, 0, 0), 0.4, emit=(1.0, 0.05, 0.04), strength=10))
    wave_fcurve(o, "location", 2, 0.05, FPS * 60 / BPM, 0.0, 0.0)


CAM_PATH = [(1.2, -5.5), (0.7, -2.6), (0.3, 0.2)]


def crowd(count=520):
    rnd = random.Random(11)
    pal = lambda name, cols, rough: [mat(f"{name}{j}", c, rough) for j, c in enumerate(cols)]
    shirts = pal("FanShirt", [(0.85, 0.85, 0.86), (0.04, 0.04, 0.05), (0.7, 0.07, 0.06), (0.12, 0.25, 0.6), (0.9, 0.6, 0.75),
                              (0.15, 0.45, 0.25), (0.95, 0.75, 0.15), (0.45, 0.2, 0.6), (0.3, 0.3, 0.32), (0.1, 0.55, 0.65),
                              (0.9, 0.4, 0.1), (0.6, 0.8, 0.95)], 0.75)
    pants = pal("FanPants", [(0.05, 0.05, 0.06), (0.15, 0.2, 0.35), (0.35, 0.35, 0.37), (0.55, 0.45, 0.32), (0.8, 0.8, 0.8)], 0.8)
    hairs = pal("FanHair", [(0.03, 0.025, 0.02), (0.25, 0.14, 0.07), (0.75, 0.62, 0.38), (0.85, 0.3, 0.45), (0.6, 0.6, 0.65), (0.1, 0.2, 0.5)], 0.5)
    skins = pal("FanSkin", [(0.95, 0.82, 0.7), (0.85, 0.65, 0.5), (0.6, 0.42, 0.3), (0.38, 0.25, 0.18), (0.98, 0.85, 0.3)], 0.5)
    hats = pal("FanHat", [(0.04, 0.04, 0.05), (0.85, 0.85, 0.86), (0.7, 0.07, 0.06), (0.12, 0.25, 0.6)], 0.6)
    eye = mat("FanEye", (0.02, 0.02, 0.02), 0.4)
    phone_m = mat("PhoneM", (0, 0, 0), 0.4, emit=(0.85, 0.9, 1.0), strength=5)
    stick_m = mat("StickM", (0, 0, 0), 0.4, emit=(1.0, 0.05, 0.04), strength=14)
    n = 0
    for k in range(count * 2):
        if n >= count:
            break
        x = rnd.uniform(-11, 11); y = rnd.uniform(BAR_Y - 0.9, -19)
        if abs(x) < 5.6 and y > BAR_Y - 2.2:  # front-row slots for the real avatars
            continue
        if any((x - cx) ** 2 + (y - cy) ** 2 < 1.5 ** 2 for cx, cy in CAM_PATH):
            continue
        s = 0.28 * rnd.uniform(0.95, 1.12); fan = empty(f"Crowd{n}", (x, y, 0)); fan.rotation_euler.z = rnd.uniform(-0.3, 0.3)
        sh, pa, ha, sk = rnd.choice(shirts), rnd.choice(pants), rnd.choice(hairs), rnd.choice(skins)
        for sx in (-0.5, 0.5):
            cube(f"CrowdLeg{n}{sx}", (s, s, 2 * s), (sx * s, 0, s), pa, fan)
        cube(f"CrowdB{n}", (2 * s, s, 2 * s), (0, 0, 3 * s), sh, fan)
        cube(f"CrowdH{n}", (1.2 * s, 1.2 * s, 1.2 * s), (0, 0, 4.6 * s), sk, fan, bevel=0.05 * s)
        for ex in (-0.25, 0.25):
            cube(f"CrowdEye{n}{ex}", (0.12 * s, 0.02 * s, 0.2 * s), (ex * s, 0.61 * s, 4.65 * s), eye, fan)
        if rnd.random() < 0.3:
            cube(f"CrowdHat{n}", (1.3 * s, 1.5 * s, 0.35 * s), (0, 0.15 * s, 5.3 * s), rnd.choice(hats), fan, bevel=0.04 * s)
        else:
            cube(f"CrowdHair{n}", (1.32 * s, 1.32 * s, 0.5 * s), (0, -0.05 * s, 5.15 * s), ha, fan, bevel=0.07 * s)
            cube(f"CrowdHairB{n}", (1.32 * s, 0.4 * s, 0.9 * s), (0, -0.5 * s, 4.75 * s), ha, fan, bevel=0.05 * s)
        r = rnd.random(); up_side = rnd.choice((-1, 1))
        for side in (-1, 1):
            shp = empty(f"CrowdSh{n}{side}", (side * 1.5 * s, 0, 3.85 * s), fan)
            cube(f"CrowdArm{n}{side}", (s, s, 2 * s), (0, 0, -0.85 * s), sh, shp)
            cube(f"CrowdHand{n}{side}", (0.95 * s, 0.95 * s, 0.3 * s), (0, 0, -1.95 * s), sk, shp)
            if side == up_side and r < 0.72:
                shp.rotation_euler = (math.radians(rnd.uniform(150, 175)), math.radians(side * rnd.uniform(-15, 5)), 0)
                if r < 0.25:
                    cube(f"Phone{n}", (0.075, 0.014, 0.14), (0, -0.05, -2.25 * s), phone_m, shp)
                else:
                    cube(f"Stick{n}", (0.05, 0.05, 0.3), (0, 0, -2.45 * s), stick_m, shp)
                    wave_fcurve(shp, "rotation_euler", 1, 0.35, 2 * FPS * 60 / BPM, rnd.uniform(0, 6.28), shp.rotation_euler[1])
        wave_fcurve(fan, "location", 2, 0.04, FPS * 60 / BPM, rnd.uniform(0, 6.28), 0.04)
        n += 1
    print("crowd", n)


def front_row():
    """Packed front row along the barricade (two staggered rows, ~0.6 m apart): the only fans we show."""
    rnd = random.Random(7)
    slots = [(-6.2 + 0.62 * k + rnd.uniform(-0.08, 0.08), BAR_Y - 0.42 + rnd.uniform(-0.06, 0.06)) for k in range(21)]
    slots += [(-5.6 + 0.62 * k + rnd.uniform(-0.1, 0.1), BAR_Y - 1.0 + rnd.uniform(-0.1, 0.1)) for k in range(19)]
    pool = [q for q in sorted(glob.glob(os.path.join(ROOT, "gfx_output", "avatar_cache", "*.blend"))) if os.path.basename(q).startswith("fan_") or os.path.basename(q)[:-6] in ("Bio_IsHere", "DI3STINY", "ImmortalNico", "Qsi2408", "sttvr_l1ght")]
    order = (pool * 5)[:len(slots)]; order = order[::3] + order[1::3] + order[2::3]
    phone_m = mat("FRPhone", (0, 0, 0), 0.4, emit=(0.85, 0.9, 1.0), strength=5)
    stick_m = mat("FRStick", (0, 0, 0), 0.4, emit=(1.0, 0.05, 0.04), strength=12)
    spb = FPS * 60 / BPM
    for i, ((x, y), path_) in enumerate(zip(slots, order)):
        with bpy.data.libraries.load(path_) as (src, dst):
            dst.objects = src.objects
        arm = None
        for o in dst.objects:
            if o is None:
                continue
            bpy.context.scene.collection.objects.link(o)
            if o.type == "ARMATURE":
                arm = o
        if not arm:
            continue
        sc = rnd.uniform(0.95, 1.05)
        arm.location = (x, y, 0); arm.rotation_euler = (0, 0, rnd.uniform(-0.45, 0.45)); arm.scale = (0.28 * sc * (-1 if i % 2 else 1), 0.28 * sc, 0.28 * sc)  # cached exports are in studs: match the 0.28 stage scale; upd()
        for pb in arm.pose.bones:
            pb.rotation_mode = "QUATERNION"
        kind = rnd.choice(("one", "both", "phone", "pump", "pump", "stick", "rail"))
        sx = rnd.choice((1, -1)); sides = [(".P", 1), (".N", -1)] if kind == "both" else [(".P" if sx > 0 else ".N", sx)]

        def raise_(side, s_, h=1.0):
            aim(arm, "UpperArm" + side, (0.25 * s_, 0.2, 0.95 * h)); aim(arm, "LowerArm" + side, (0.15 * s_, 0.3, 0.94 * h))
            aim(arm, "Hand" + side, (0.15 * s_, 0.3, 0.94 * h), (0, 1, 0))
        if kind == "rail":
            for side, s_ in ((".P", 1), (".N", -1)):
                aim(arm, "UpperArm" + side, (0.1 * s_, 0.6, -0.8)); aim(arm, "LowerArm" + side, (0, 1, 0.1)); aim(arm, "Hand" + side, (0, 1, 0.1), (0, 0, 1))
        elif kind == "pump":
            side, s_ = sides[0]; ph = rnd.randint(0, 3)
            for k in range(int(END / spb) + 1):
                for fo, h in ((0, 1.0), (spb / 2, 0.15)):
                    raise_(side, s_, h)
                    for b in ("UpperArm", "LowerArm", "Hand"):
                        arm.pose.bones[b + side].keyframe_insert("rotation_quaternion", frame=1 + k * spb + fo + ph)
        else:
            for side, s_ in sides:
                raise_(side, s_)
            if kind in ("phone", "stick"):
                hb = arm.pose.bones.get("Hand" + sides[0][0])
                if hb:
                    p = cube(f"FRItem{i}", (0.27, 0.05, 0.5) if kind == "phone" else (0.18, 0.18, 1.07), (0, 0, 0), phone_m if kind == "phone" else stick_m)
                    p.parent = arm; p.parent_type = "BONE"; p.parent_bone = hb.name; p.location = (0, 0.18 if kind == "phone" else 0.43, 0)
        wave_fcurve(arm, "location", 2, 0.06, spb, rnd.uniform(0, 6.28), 0.06)
        print("front row", kind, os.path.basename(path_))


def fx():
    # CO2 jets at the stage lip, firing on the 10.1 s riser
    for k, x in enumerate((-5.2, -3.6, 3.6, 5.2)):
        bpy.ops.mesh.primitive_cone_add(radius1=0.15, radius2=0.9, depth=4.0, location=(x, STAGE_Y + 0.3, STAGE_Z + 2.0), vertices=24)
        c = bpy.context.active_object; c.name = f"CO2_{k}"
        m = bpy.data.materials.new(f"CO2M{k}"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        vs = nt.nodes.new("ShaderNodeVolumePrincipled"); vs.inputs["Color"].default_value = (1, 1, 1, 1)
        mo = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(vs.outputs[0], mo.inputs["Volume"]); c.data.materials.append(m)
        d = vs.inputs["Density"]
        for f, v in ((1, 0), (sec(10.1), 0), (sec(10.25), 2.5), (sec(11.0), 1.2), (sec(11.8), 0)):
            d.default_value = v; d.keyframe_insert("default_value", frame=f)
        for f, s in ((sec(10.1), 0.05), (sec(10.35), 1.0)):
            c.scale = (1, 1, s); c.location.z = STAGE_Z + 2.0 * s; c.keyframe_insert("scale", frame=f); c.keyframe_insert("location", frame=f)
    # confetti from the truss after the riser
    for col, name in (((1, 0.05, 0.04), "ConfRed"), ((0.95, 0.95, 0.95), "ConfWhite")):
        bpy.ops.mesh.primitive_plane_add(size=0.05, location=(0, -50, -50)); piece = bpy.context.active_object; piece.name = name + "Piece"
        piece.data.materials.append(mat(name + "M", col, 0.4, emit=col, strength=0.6))
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, STAGE_Y - 1.0, 8.5)); em = bpy.context.active_object; em.name = name + "Emit"
        em.scale = (12, 6, 1); em.hide_render = True
        ps = em.modifiers.new("conf", "PARTICLE_SYSTEM").particle_system; st = ps.settings
        st.count = 900; st.frame_start = sec(10.15); st.frame_end = sec(11.2); st.lifetime = 120
        st.normal_factor = -1.2; st.factor_random = 0.6; st.effector_weights.gravity = 0.15; st.drag_factor = 0.4
        st.render_type = "OBJECT"; st.instance_object = piece; st.particle_size = 1.0; st.size_random = 0.5
        st.use_rotations = True; st.rotation_factor_random = 1.0; st.angular_velocity_factor = 6.0
        em.show_instancer_for_render = False


def lights():
    L = {}
    spb = FPS * 60 / BPM

    def cue(obj, keys, const=False):
        for t, e in keys:
            obj.data.energy = e; obj.data.keyframe_insert("energy", frame=max(1, round(t * FPS) + 1))
        if const:
            for fc in obj.data.animation_data.action.layers[0].strips[0].channelbags[0].fcurves if hasattr(obj.data.animation_data.action, "layers") and obj.data.animation_data.action.layers else obj.data.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
    for k, x in enumerate((-6, -3, 0, 3, 6)):  # beams: beat-locked pan steps + energy pops on each beat
        s_ = spot(f"BeamW{k}", (x, STAGE_Y + 0.6, 7.5), (x * 0.4, -6, 0.5), 5000, (1, 0.97, 0.92), 6, 0.1); L[f"beam{k}"] = s_
        r0 = s_.rotation_euler[1]
        for b in range(int(END / spb) + 1):
            f = 1 + b * spb; s_.rotation_euler[1] = r0 + (0.32 if (b + k) % 2 else -0.32); s_.keyframe_insert("rotation_euler", index=1, frame=f)
        pops = []
        for b in range(int(END / spb) + 1):
            t = b * spb / FPS; e = env(t)
            pops += [(t, 6500 * e), (t + 0.3, 2600 * e)]
        cue(s_, pops)
    for k, x in enumerate((-7, 7)):
        L[f"red{k}"] = spot(f"StageRed{k}", (x, STAGE_Y + 5, 7.5), (x * 0.3, STAGE_Y + 2, STAGE_Z), 7000, (1, 0.05, 0.04), 38, 0.5, 0.4)
    L["key"] = spot("StageKey", (0, STAGE_Y - 3.5, 6.5), (0, FRONT, STAGE_Z + 0.8), 6200, (0.95, 0.95, 1.0), 48, 0.4, 0.3)
    for k, (x, col) in enumerate(((-3.0, (1, 0.9, 0.8)), (3.0, (1, 0.12, 0.08)))):  # back rims: separate black outfits from the screen
        L[f"rim{k}"] = spot(f"Rim{k}", (x, STAGE_Y + 6.0, 6.0), (-x * 0.3, FRONT, STAGE_Z + 1.2), 9000, col, 42, 0.35, 0.2)
    L["back"] = spot("EntranceBack", (0, FRONT + 8.0, STAGE_Z + 1.2), (0, FRONT - 2, STAGE_Z + 1.0), 0, (1, 0.97, 0.92), 22, 0.3, 0.1)
    L["face"] = spot("SuhaaFace", (0, STAGE_Y - 4.0, 5.0), (0, FRONT - 0.35, STAGE_Z + 1.1), 0, (0.92, 0.94, 1.0), 10, 0.25, 0.1)
    L["strobe"] = bpy.data.objects.new("Strobe", bpy.data.lights.new("Strobe", "AREA")); bpy.context.scene.collection.objects.link(L["strobe"])
    L["strobe"].data.size = 12; L["strobe"].location = (0, STAGE_Y + 1.0, 8.0); L["strobe"].data.energy = 0
    for k, (y, col) in enumerate(((-4, (1.0, 0.35, 0.3)), (-11, (0.6, 0.65, 1.0)))):  # weak: fans stay silhouettes
        ld = bpy.data.lights.new(f"CrowdFill{k}", "AREA"); ld.shape = "RECTANGLE"; ld.size, ld.size_y = 20, 6; ld.energy = 110; ld.color = col
        o = bpy.data.objects.new(f"CrowdFill{k}", ld); bpy.context.scene.collection.objects.link(o)
        o.location = (0, y + 1, 4.5); o.rotation_euler = (math.radians(-12), 0, 0)

    for nm in ("key", "red0", "red1", "rim0", "rim1"):  # blackout for the entrance, slam on the 4.2 s stab, cut before CO2
        e = L[nm].data.energy
        cue(L[nm], [(0, e), (2.3, e), (2.7, 0), (4.16, 0), (4.2, e * 1.25), (4.7, e), (9.96, e), (10.0, 0), (10.06, 0), (10.1, e * 1.2), (10.6, e)])
    cue(L["back"], [(0, 0), (2.55, 0), (2.6, 45000), (4.16, 45000), (4.6, 5000)])  # silhouette through haze
    cue(L["face"], [(0, 0), (4.16, 0), (4.2, 3200), (4.7, 1800)], const=True)
    sk = [(0, 0), (4.2, 7000), (4.25, 0), (4.33, 7000), (4.38, 0)]
    for k in range(6):  # strobe burst on the 8.1 s hit
        t = 8.13 + k * 0.083; sk += [(t, 6000), (t + 0.042, 0)]
    t = 9.2  # riser: flashes speeding up into the cut
    while t < 9.95:
        sk += [(t, 3000), (t + 0.042, 0)]; t += max(0.09, 0.25 - (t - 9.2) * 0.25)
    cue(L["strobe"], sorted(sk), const=True)
    w = bpy.context.scene.world or bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.002, 0.002, 0.003, 1)


def camera(suhaa):
    cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    tgt = empty("CamTarget", (0, 0, 0)); c = cam.constraints.new("TRACK_TO"); c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    for t, p, look, lens in [
        (0.0, (1.2, -5.0, 2.3), (0, FRONT, 2.0), 26),
        (2.6, (0.8, -3.0, 2.1), (0, FRONT + 1.4, 2.0), 30),
        (3.2, (0.6, -2.6, 1.95), (0, FRONT + 2.2, 2.3), 30),
        (4.15, (0.3, -1.7, 2.0), (0, FRONT, 2.15), 33),
        (4.22, (0.33, -1.35, 2.03), (0, FRONT - 0.3, 2.05), 40),  # punch-in on the hit
        (4.3, (0.27, -1.3, 1.99), (0, FRONT - 0.3, 2.0), 40),
        (4.4, (0.3, -1.3, 2.0), (0, FRONT - 0.3, 2.0), 40),
        (8.1, (-1.5, -1.2, 2.0), (0, FRONT - 0.3, 2.0), 40),
        (10.1, (-0.7, -1.0, 1.95), (0, FRONT - 1.2, 2.1), 34),
        (11.9, (0.5, -1.1, 2.05), (0, FRONT - 1.2, 2.0), 30)]:
        f = sec(t); cam.location = p; cam.keyframe_insert("location", frame=f)
        tgt.location = look; tgt.keyframe_insert("location", frame=f); cd.lens = lens; cd.keyframe_insert("lens", frame=f)
    cd.dof.use_dof = True; cd.dof.focus_object = suhaa; cd.dof.focus_subtarget = "Head"; cd.dof.aperture_fstop = 3.2


def build():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    a = base.build_suhaa(); a.name = "Suhaa"
    for o in a.children_recursive:  # speech-bubble accessory (wide flat Handle): not part of the look
        if o.type == "MESH" and o.dimensions.x > 1.5:
            o.hide_render = o.hide_viewport = True
    venue(); back_crowd(); front_row(); fx(); lights()
    starts = [(-2.4, 0), (-1.2, 0), (0.0, 0), (1.2, 0), (2.4, 0)]
    ends = [(-3.0, 0.4), (-1.55, 0.25), (0.0, 1.6), (1.55, 0.25), (3.0, 0.4)]
    for i, name in enumerate(STAGE):
        (x0, y0), (x1, y1) = starts[i], ends[i]
        keys = [(0, x0, FRONT + y0), (2.2, x0, FRONT + y0), (3.2, x1, FRONT + y1), (8.13, x1, FRONT + y1), (9.9, x1, FRONT + y1 - 0.9), (12.0, x1, FRONT + y1 - 0.9)]
        drive_suhaa(load_avatar(name), keys, lag=(1, 12, 0, 12, 2)[i], walk=False, amp=(0.92, 1.1, 1.0, 1.06, 0.9)[i],
                    head_bias=(0.06, -0.04, 0.0, 0.05, -0.07)[i], groove_ph=(0.0, 0.12, 0.05, 0.1, 0.02)[i])
    drive_suhaa(a)
    camera(a)
    from bpy_extras.object_utils import world_to_camera_view as w2c
    sc = bpy.context.scene; seen = set()
    fans = [o for o in sc.objects if o.name.startswith("Crowd") and o.name[5:].isdigit()]
    for f in range(1, END + 1, 3):  # drop crowd fans the camera never sees (saves render time)
        sc.frame_set(f)
        for o in fans:
            v = w2c(sc, sc.camera, o.matrix_world @ Vector((0, 0, 0.7)))
            if -0.15 < v.x < 1.15 and -0.15 < v.y < 1.15 and v.z > 0:
                seen.add(o.name)
    for o in fans:
        if o.name not in seen:
            for c in [o] + list(o.children_recursive):
                bpy.data.objects.remove(c, do_unlink=True)
    sc.frame_set(1); print("crowd kept", len(seen))
    base.render_setup(); bpy.context.scene.frame_end = END; bpy.context.scene.view_settings.exposure = 0.35
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "scene.blend"))
    print("built")


def stills(frames, pct=50):
    sc = bpy.context.scene; sc.render.resolution_percentage = pct
    for f in frames:
        sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "stills", f"f{f:03d}.png")
        bpy.ops.render.render(write_still=True)


def frames(a, b, pct=100):
    sc = bpy.context.scene; sc.render.resolution_percentage = pct
    sc.frame_start, sc.frame_end = a, b; sc.render.filepath = os.path.join(OUT, "frames" if pct == 100 else "draft", "f")
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    cmd = argv[0] if argv else "build"
    if cmd == "build":
        build()
    elif cmd == "stills":
        stills([int(x) for x in argv[1].split(",")], int(argv[2]) if len(argv) > 2 else 50)
    elif cmd == "frames":
        frames(int(argv[1]) if len(argv) > 1 else 1, int(argv[2]) if len(argv) > 2 else END, int(argv[3]) if len(argv) > 3 else 100)
