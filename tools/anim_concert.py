"""10 s single-shot concert animation: Suhaa_Official (new avatar) front row at a Cortis-style show; five blocky Roblox
performers dance on stage. One continuous camera move: high behind the crowd -> crane down behind her shoulder ->
orbit round her side -> into the photo pit -> push in on her face. No Roblox anim clips (owner: they look weird);
all motion is procedural (beat bounce, breathing, overlapping arms, eased acting poses).
Runs in its OWN headless Blender (never the shared GUI instance on port 9876):

  blender -b --factory-startup -P tools/anim_concert.py -- build
  blender -b gfx_output/anim_concert/scene.blend -P tools/anim_concert.py -- stills 1,72,144,200,240
  blender -b gfx_output/anim_concert/scene.blend -P tools/anim_concert.py -- frames [start end]
"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix

ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
OUT = os.path.join(ROOT, "gfx_output", "anim_concert")
sys.path.insert(0, os.path.join(ROOT, "tools"))
FPS, END, BPM = 24, 285, 120  # 11.9 s song (owner's mp3), ~120 BPM
SONG = r"C:\Users\Siddharth D\Downloads\lv_0_20261027003944.mp3"
STAGE_Y, STAGE_Z = 5.5, 1.3
os.makedirs(OUT, exist_ok=True)


def upd():
    bpy.context.view_layer.update()


def beat(f):
    return (f / FPS) * BPM / 60.0


def mat(name, color=(0.5, 0.5, 0.5), rough=0.6, metal=0.0, emit=None, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = strength
    return m


def cube(name, size, loc, m, parent=None, bevel=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.scale = size; o.location = loc; me.materials.append(m)
    if bevel:
        mod = o.modifiers.new("bev", "BEVEL"); mod.width = bevel; mod.segments = 3
    if parent:
        o.parent = parent
    return o


def empty(name, loc, parent=None):
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e); e.location = loc
    if parent:
        e.parent = parent
    return e


def wave_fcurve(obj, path, index, amp, period_frames, phase=0.0, offset=None):
    """Loop a value with a sine F-Modifier (cheap for many crowd objects)."""
    obj.keyframe_insert(path, index=index, frame=1)
    fc = obj.animation_data.action.fcurves.find(path, index=index) if hasattr(obj.animation_data.action, "fcurves") else None
    if fc is None:  # Blender 5 layered actions
        fc = next(c for c in obj.animation_data.action.layers[0].strips[0].channelbag(obj.animation_data.action.slots[0]).fcurves
                  if c.data_path == path and c.array_index == index)
    m = fc.modifiers.new("FNGENERATOR"); m.function_type = "SIN"; m.amplitude = amp
    m.phase_multiplier = 2 * math.pi / period_frames; m.phase_offset = phase
    m.value_offset = getattr(obj, path)[index] if offset is None else offset
    m.use_additive = False


# ---------------------------------------------------------------- Suhaa
def build_suhaa():
    G = {"__name__": "bx", "AVATAR_DIR": os.path.join(ROOT, "avatars", "Suhaa_Official_new"), "POSE": "idle"}
    exec(open(os.path.join(ROOT, "tools", "build_exact_gfx.py"), encoding="utf-8").read(), G)
    for o in list(bpy.data.objects):
        if o.name in ("Backdrop", "Halo") or o.type in ("LIGHT", "CAMERA"):
            bpy.data.objects.remove(o, do_unlink=True)
    a = bpy.data.objects["Avatar"]; upd()
    for o in a.children:  # her "#1 CORTIS FAN" speech-bubble accessory: slogan text, keep out of the film
        if o.name.split(".")[0] == "Handle4":
            o.hide_render = o.hide_viewport = True
    low = min((o.matrix_world @ Vector(c)).z for o in a.children_recursive if o.type == "MESH" for c in o.bound_box)
    a.location.z -= low; upd()
    return a


def suhaa_motion(a):
    from anim_motion import Actor
    lean = [("UpperTorso", (0, 0.16, 1), (0, 1, 0)), ("LowerTorso", (0, 0, 1), (0, 1, 0))]
    rest_arm = []
    for sfx, sx in ((".P", 1), (".N", -1)):  # forearms on the rail
        rest_arm += [("UpperArm" + sfx, (0.12 * sx, 0.45, -0.88)), ("LowerArm" + sfx, (-0.45 * sx, 0.89, 0.05)),
                     ("Hand" + sfx, (-0.45 * sx, 0.89, 0.0), (0, 0, 1))]
        rest_arm += [("UpperLeg" + sfx, (0, 0, -1)), ("LowerLeg" + sfx, (0, 0, -1)), ("Foot" + sfx, (0, 1, 0), (0, 0, 1))]
    act = Actor(a, base=lean + rest_arm, personality={"breath": 1.3, "sway": 1.4, "head": 1.2})
    look_stage = [("Head", (0.05, -0.2, 0.98), (0.1, 1, 0.22))]
    act.act(1, 238, look_stage, fade=10)
    # 0.8 s - 6.5 s: right arm up holding the lightstick, waving on the beat (keyed per frame below via arm_wave)
    up_items = lambda s: [("UpperArm.P", (0.28 + 0.12 * s, 0.25, 0.93)), ("LowerArm.P", (0.2 + 0.35 * s, 0.2, 0.92)),
                          ("Hand.P", (0.2 + 0.35 * s, 0.2, 0.92), (0, 1, 0))]
    # 6.8 s on: looks down at the lens side, small smile-bob, chin up
    act.act(245, END + 10, [("Head", (0.12, -0.08, 0.99), (0.35, 1, 0.12))], fade=12)
    frames = range(1, END + 1)
    for f in frames:
        act.pose_at(f, FPS)
        w = __import__("anim_motion").window(f, 24, 185, 10)
        if w > 0:
            s = math.sin(math.pi * beat(f))  # one side-to-side per beat
            act._apply_items(up_items(s), w)
        upd()
        for pb in a.pose.bones:
            pb.keyframe_insert("rotation_quaternion", frame=f); pb.keyframe_insert("location", frame=f)
        # whole-body beat bounce (legs are behind the barricade panel)
        a.location.z = a["z0"] + 0.025 * abs(math.sin(math.pi * beat(f)))
        a.keyframe_insert("location", index=2, frame=f)


def lightstick(a):
    """Red lightstick held in her right hand (bone child)."""
    upd(); pb = a.pose.bones["Hand.P"]; tip = a.matrix_world @ pb.tail; d = (a.matrix_world.to_3x3() @ (pb.tail - pb.head)).normalized()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.34, vertices=16)
    s = bpy.context.active_object; s.name = "StickSuhaa"
    s.data.materials.append(mat("StickSuhaaM", (0.0, 0.0, 0.0), 0.3, emit=(1.0, 0.06, 0.05), strength=18))
    mw = Matrix.Translation(tip + d * 0.12) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    s.parent = a; s.parent_type = "BONE"; s.parent_bone = "Hand.P"; upd(); s.matrix_world = mw


# ---------------------------------------------------------------- blocky Roblox performers
LOOKS = [  # shirt, pants, hair, jacket(None) - original streetwear looks, no likeness of real people
    ((0.9, 0.9, 0.9), (0.08, 0.08, 0.1), (0.05, 0.04, 0.04), (0.05, 0.05, 0.06)),
    ((0.06, 0.06, 0.07), (0.2, 0.26, 0.38), (0.75, 0.68, 0.55), None),
    ((0.75, 0.08, 0.07), (0.07, 0.07, 0.08), (0.04, 0.03, 0.03), None),
    ((0.12, 0.12, 0.14), (0.55, 0.55, 0.57), (0.32, 0.18, 0.1), (0.85, 0.85, 0.86)),
    ((0.9, 0.9, 0.9), (0.18, 0.22, 0.32), (0.05, 0.05, 0.06), (0.65, 0.07, 0.06)),
]
SKIN = (0.93, 0.8, 0.68)


def performer(i, x, y, look, scale=1.35):
    """Blocky Roblox performer with elbows and knees. Root faces the crowd (-Y); local +X = performer's right."""
    shirt, pants, hair, jacket = look; S = 0.28 * scale
    root = empty(f"Perf{i}", (x, y, STAGE_Z)); root.rotation_euler = (0, 0, math.radians(180))
    m_sh, m_pa, m_ha, m_sk = mat(f"P{i}Shirt", shirt, 0.7), mat(f"P{i}Pants", pants, 0.8), mat(f"P{i}Hair", hair, 0.5), mat(f"P{i}Skin", SKIN, 0.5)
    m_arm = mat(f"P{i}Jk", jacket, 0.6) if jacket else m_sh
    hip = empty(f"Perf{i}_Hip", (0, 0, 2 * S), root)
    cube(f"Perf{i}_Torso", (2 * S, 1 * S, 2 * S), (0, 0, S), m_arm, hip)
    if jacket:
        cube(f"Perf{i}_Tee", (0.9 * S, 1.02 * S, 1.9 * S), (0, 0, S), m_sh, hip)
    head = empty(f"Perf{i}_Neck", (0, 0, 2 * S), hip)
    cube(f"Perf{i}_Head", (1.2 * S, 1.2 * S, 1.2 * S), (0, 0, 0.6 * S), m_sk, head, bevel=0.06 * S)
    cube(f"Perf{i}_Hair", (1.32 * S, 1.32 * S, 0.5 * S), (0, 0.05 * S, 1.15 * S), m_ha, head, bevel=0.08 * S)
    cube(f"Perf{i}_HairBack", (1.32 * S, 0.4 * S, 0.9 * S), (0, 0.5 * S, 0.75 * S), m_ha, head, bevel=0.06 * S)
    eye = mat(f"P{i}Eye", (0.02, 0.02, 0.02), 0.4)
    for ex in (-0.25, 0.25):
        cube(f"Perf{i}_Eye{ex}", (0.12 * S, 0.02 * S, 0.2 * S), (ex * S, -0.61 * S, 0.62 * S), eye, head)
    parts = {"root": root, "hip": hip, "head": head, "S": S}
    for side, sx in (("R", 1), ("L", -1)):
        sh = empty(f"Perf{i}_Sh{side}", (sx * 1.5 * S, 0, 1.85 * S), hip)
        cube(f"Perf{i}_UArm{side}", (0.95 * S, 0.95 * S, 1.0 * S), (0, 0, -0.45 * S), m_arm, sh)
        el = empty(f"Perf{i}_El{side}", (0, 0, -0.95 * S), sh)
        cube(f"Perf{i}_LArm{side}", (0.9 * S, 0.9 * S, 0.8 * S), (0, 0, -0.4 * S), m_arm, el)
        cube(f"Perf{i}_Hand{side}", (0.85 * S, 0.85 * S, 0.3 * S), (0, 0, -0.95 * S), m_sk, el)
        lg = empty(f"Perf{i}_Leg{side}", (sx * 0.5 * S, 0, 2 * S), root)
        cube(f"Perf{i}_ULeg{side}", (1 * S, 1 * S, 1.05 * S), (0, 0, -0.5 * S), m_pa, lg)
        kn = empty(f"Perf{i}_Kn{side}", (0, 0, -S), lg)
        cube(f"Perf{i}_LLeg{side}", (0.98 * S, 0.98 * S, 0.9 * S), (0, 0, -0.45 * S), m_pa, kn)
        cube(f"Perf{i}_Shoe{side}", (1.04 * S, 1.2 * S, 0.3 * S), (0, -0.08 * S, -0.88 * S), mat(f"P{i}Shoe", (0.92, 0.92, 0.92), 0.5), kn)
        parts.update({"sh" + side: sh, "el" + side: el, "leg" + side: lg, "kn" + side: kn})
    return root, parts


# Choreography (owner's breakdown, 5 sections over 0-12 s). A pose = joint angles in degrees:
#   lean (torso forward), tw (torso twist), side (torso side tilt), head (nod down),
#   aF/aO/eB/eU per arm (shoulder forward raise, outward raise, elbow forward bend, elbow upward flex),
#   tF/kB/hO per leg (thigh forward, knee bend, hip outward), x/y (stage offset in metres, +y = toward crowd).
def P(*ds, **k):
    base = dict(lean=0, tw=0, side=0, head=0, x=0, y=0,
                aFR=5, aOR=8, eBR=10, eUR=0, aFL=5, aOL=8, eBL=10, eUL=0,
                tFR=0, kBR=0, hOR=4, tFL=0, kBL=0, hOL=4)
    for d in ds:
        base.update(d)
    base.update(k); return base


def mirror_arms(**k):
    out = {}
    for key, v in k.items():
        out[key + "R"] = v; out[key + "L"] = v
    return out


CROUCH = dict(lean=14, tFR=30, kBR=55, tFL=30, kBL=55)
WIDE = dict(hOR=16, hOL=16, tFR=22, kBR=40, tFL=22, kBL=40)
CHOREO = [  # (time s, pose) - transitions are fast (snap), holds between
    (0.00, P(CROUCH, **mirror_arms(aF=20, aO=10, eB=70))),                                   # 1 knees bent, leaning
    (0.20, P(CROUCH, **mirror_arms(aF=25, aO=12, eB=80))),                                   # 2-3 quick steps (step layer)
    (1.10, P(CROUCH, x=-0.12, side=-6, **mirror_arms(aF=20, aO=14, eB=75))),                 # 4 weight shift sideways
    (1.40, P(CROUCH, x=0.12, side=6, **mirror_arms(aF=20, aO=14, eB=75))),
    (1.71, P(lean=0, tFR=8, kBR=12, tFL=8, kBL=12, **mirror_arms(aF=60, aO=70, eB=10))),     # 5 arms up and out
    (2.10, P(CROUCH, **mirror_arms(aF=15, aO=8, eB=85))),                                    # 6 land, arms in
    (2.40, P(CROUCH, y=0.15, **mirror_arms(aF=30, aO=5, eB=110))),                           # 7-8 steps to centre, arms to chest
    (3.24, P(CROUCH, y=0.25, side=-5, **mirror_arms(aF=30, aO=5, eB=110))),                  # 9 bounce weight shift
    (3.72, P(WIDE, y=0.3, lean=2, **mirror_arms(aF=20, aO=20, eB=90))),                      # 10 settle wide
    (4.21, P(WIDE, y=0.3, **mirror_arms(aF=35, aO=60, eB=125))),                             # 11-12 hands to chest/face, elbows out
    (4.70, P(WIDE, y=0.3, **mirror_arms(aF=30, aO=75, eB=95))),                              # 13 sharp forearm gesture
    (5.20, P(WIDE, y=0.3, **mirror_arms(aF=10, aO=88, eU=80))),                              # 14 elbows open, forearms to shoulder level
    (5.67, P(WIDE, y=0.3, **mirror_arms(aF=5, aO=95, eU=55))),                               # 15 wide bent-elbow
    (6.20, P(WIDE, y=0.3, side=-8, x=-0.1, tFR=30, kBR=55, **mirror_arms(aF=5, aO=95, eU=55))),   # 16-17 pulse, side
    (6.70, P(WIDE, y=0.3, side=8, x=0.1, tFL=30, kBL=55, **mirror_arms(aF=5, aO=95, eU=55))),
    (6.95, P(WIDE, y=0.3, **mirror_arms(aF=35, aO=60, eB=125))),                             # 18 arms in to chest
    (7.20, P(WIDE, y=0.3, **mirror_arms(aF=5, aO=95, eU=60))),                               # 18 reopen
    (7.45, P(WIDE, y=0.3, side=-8, x=-0.1, **mirror_arms(aF=5, aO=98, eU=50))),              # 19 repeat sharp out + side
    (7.70, P(WIDE, y=0.3, side=8, x=0.1, **mirror_arms(aF=5, aO=98, eU=50))),
    (8.13, P(CROUCH, y=0.35, **mirror_arms(aF=15, aO=10, eB=90))),                           # 21-25 travel forward (run layer)
    (9.90, P(CROUCH, y=1.15, **mirror_arms(aF=15, aO=10, eB=90))),
    (10.14, P(lean=10, hOR=22, hOL=22, tFR=28, kBR=50, tFL=10, kBL=20, x=0.25, y=1.2, side=10,
              **mirror_arms(aF=20, aO=60, eB=20))),                                             # 26-28 step out, swing arms
    (10.60, P(lean=32, hOR=24, hOL=24, tFR=28, kBR=52, tFL=26, kBL=48, x=0.3, y=1.2, side=6,
              **mirror_arms(aF=0, aO=90, eB=0))),                                               # 29-30 broad line, hinge forward
    (11.40, P(lean=30, hOR=24, hOL=24, tFR=28, kBR=52, tFL=26, kBL=48, x=0.3, y=1.2, side=6,
              **mirror_arms(aF=0, aO=88, eB=0))),
    (11.89, P(lean=8, hOR=12, hOL=12, tFR=12, kBR=20, tFL=12, kBL=20, x=0.3, y=1.2,
              **mirror_arms(aF=10, aO=20, eB=40))),                                             # 31 return upright
]
STEPS = [(0.2, 1.1, 4), (2.4, 3.2, 4), (8.13, 9.9, 2)]  # (from, to, steps per second... per beat): quick-step layer
SNAP = 0.14  # seconds per transition: sharp, not floaty


def ease(u):
    u = max(0.0, min(1.0, u)); return 1 - (1 - u) ** 3  # fast out, settle in


def choreo_at(t):
    for (t0, p0), (t1, p1) in zip(CHOREO, CHOREO[1:]):
        if t0 <= t < t1:
            u = ease((t - t0) / min(SNAP, t1 - t0))
            # value moves from previous pose to this key's pose quickly right after t0
            prev = CHOREO[max(0, CHOREO.index((t0, p0)) - 1)][1]
            return {k: prev[k] + (p0[k] - prev[k]) * u for k in p0}
    return dict(CHOREO[-1][1])


def leg_drop(S, tF, kB):
    """How far the hips sink for a thigh/knee angle pair (keeps feet on the deck)."""
    a, b = math.radians(tF), math.radians(kB - tF)
    return S * (1 - math.cos(a)) + 0.9 * S * (1 - math.cos(b))


def dance(root, parts, i):
    S = parts["S"]; x0, y0 = root.location.x, root.location.y; r = math.radians
    for f in range(1, END + 1):
        t = f / FPS + 0.012 * i  # tiny human offset per dancer
        p = choreo_at(t); b = t * BPM / 60.0
        pulse = abs(math.sin(math.pi * b)) ** 2  # knee bounce on every beat
        for t0, t1, rate in STEPS:  # quick steps: alternate feet lifting, opposite arm pump
            if t0 <= t < t1:
                ph = math.sin(2 * math.pi * b * rate / 2)
                p["tFR"] += 28 * max(0, ph); p["kBR"] += 45 * max(0, ph)
                p["tFL"] += 28 * max(0, -ph); p["kBL"] += 45 * max(0, -ph)
                p["aFR"] += 25 * ph; p["aFL"] -= 25 * ph
        for s in ("R", "L"):
            p["kB" + s] += 14 * pulse; p["tF" + s] += 7 * pulse
        drop = min(leg_drop(S, p["tFR"], p["kBR"]), leg_drop(S, p["tFL"], p["kBL"]))
        # root: performer's +X is world -X and forward (-local Y) is world -Y, root rotated 180
        root.location = (x0 - p["x"], y0 - p["y"], STAGE_Z - drop)
        root.rotation_euler = (0, 0, math.radians(180 + p["tw"]))
        parts["hip"].rotation_euler = (r(p["lean"]), r(-p["side"]), 0)
        parts["head"].rotation_euler = (r(p["head"] - 0.4 * p["lean"]), 0, 0)
        for s, sx in (("R", 1), ("L", -1)):
            parts["sh" + s].rotation_euler = (r(-p["aF" + s]), r(-sx * p["aO" + s]), 0)
            parts["el" + s].rotation_euler = (r(-p["eB" + s]), r(-sx * p["eU" + s]), 0)
            parts["leg" + s].rotation_euler = (r(-p["tF" + s]), r(-sx * p["hO" + s]), 0)
            parts["kn" + s].rotation_euler = (r(p["kB" + s]), 0, 0)
        for o in (parts["hip"], parts["head"], parts["shR"], parts["shL"], parts["elR"], parts["elL"],
                  parts["legR"], parts["legL"], parts["knR"], parts["knL"]):
            o.keyframe_insert("rotation_euler", frame=f)
        root.keyframe_insert("rotation_euler", frame=f); root.keyframe_insert("location", frame=f)

# ---------------------------------------------------------------- venue
def venue(a):
    upd()
    el = [a.matrix_world @ a.pose.bones["LowerArm" + s].head for s in (".P", ".N")]
    rail_top = el[0].z - 0.05; rail_y = (el[0].y + el[1].y) / 2 + 0.06
    steel, dark = mat("BarSteel", (0.55, 0.56, 0.58), 0.3, 0.9), mat("BarDark", (0.07, 0.07, 0.08), 0.6, 0.6)
    cube("BarRail", (10, 0.09, 0.05), (0, rail_y, rail_top - 0.025), steel)
    cube("BarPanel", (10, 0.03, rail_top - 0.12), (0, rail_y + 0.03, (rail_top - 0.12) / 2 + 0.06), dark)
    for k in range(-5, 6):
        cube(f"BarPost{k}", (0.05, 0.06, rail_top), (k * 1.0, rail_y + 0.02, rail_top / 2), steel)
        cube(f"BarFoot{k}", (0.06, 0.9, 0.04), (k * 1.0, rail_y + 0.3, 0.02), steel)
    floor = mat("Floor", (0.015, 0.015, 0.017), 0.35)
    cube("Floor", (60, 60, 0.02), (0, 0, -0.01), floor)
    # stage deck, front lip LED strip, back LED wall, truss with fixtures
    cube("StageDeck", (16, 9, STAGE_Z), (0, STAGE_Y + 4.5, STAGE_Z / 2), mat("Deck", (0.02, 0.02, 0.022), 0.4, 0.2))
    cube("StageLip", (16, 0.04, 0.08), (0, STAGE_Y - 0.02, STAGE_Z - 0.1), mat("LipLED", (0, 0, 0), 0.3, emit=(1, 0.08, 0.06), strength=6))
    scr = cube("Screen", (13, 0.1, 6.0), (0, STAGE_Y + 8.2, STAGE_Z + 3.6), screen_mat())
    cube("ScreenFrame", (13.4, 0.08, 6.4), (0, STAGE_Y + 8.27, STAGE_Z + 3.6), mat("ScrFrame", (0.01, 0.01, 0.01), 0.5))
    tm = mat("Truss", (0.12, 0.12, 0.13), 0.45, 0.8)
    for ty in (STAGE_Y + 0.6, STAGE_Y + 5):
        cube(f"Truss{ty:.0f}", (16, 0.3, 0.3), (0, ty, 7.6), tm)
    for side in (-1, 1):
        cube(f"TrussLeg{side}", (0.3, 0.3, 7.6), (side * 8, STAGE_Y + 0.6, 3.8), tm)
        cube(f"Speaker{side}", (1.0, 0.9, 3.2), (side * 7.4, STAGE_Y - 0.6, 5.2), mat("Spk", (0.02, 0.02, 0.02), 0.6))
    # crowd behind her: colourful blocky Roblox fans facing the stage (+Y), bouncing, with phones and red lightsticks
    rnd = random.Random(7)
    pal = lambda name, cols, rough: [mat(f"{name}{j}", c, rough) for j, c in enumerate(cols)]
    shirts = pal("FanShirt", [(0.85, 0.85, 0.86), (0.04, 0.04, 0.05), (0.7, 0.07, 0.06), (0.12, 0.25, 0.6), (0.9, 0.6, 0.75),
                              (0.15, 0.45, 0.25), (0.95, 0.75, 0.15), (0.45, 0.2, 0.6), (0.3, 0.3, 0.32), (0.1, 0.55, 0.65)], 0.75)
    pants = pal("FanPants", [(0.05, 0.05, 0.06), (0.15, 0.2, 0.35), (0.35, 0.35, 0.37), (0.55, 0.45, 0.32), (0.8, 0.8, 0.8)], 0.8)
    hairs = pal("FanHair", [(0.03, 0.025, 0.02), (0.25, 0.14, 0.07), (0.75, 0.62, 0.38), (0.85, 0.3, 0.45), (0.6, 0.6, 0.65), (0.1, 0.2, 0.5)], 0.5)
    skins = pal("FanSkin", [(0.95, 0.82, 0.7), (0.85, 0.65, 0.5), (0.6, 0.42, 0.3), (0.38, 0.25, 0.18), (0.98, 0.85, 0.3)], 0.5)
    hats = pal("FanHat", [(0.04, 0.04, 0.05), (0.85, 0.85, 0.86), (0.7, 0.07, 0.06)], 0.6)
    eye = mat("FanEye", (0.02, 0.02, 0.02), 0.4)
    phone_m = mat("PhoneM", (0, 0, 0), 0.4, emit=(0.85, 0.9, 1.0), strength=5)
    stick_m = mat("StickM", (0, 0, 0), 0.4, emit=(1.0, 0.05, 0.04), strength=14)
    n = 0
    for k in range(300):
        x = rnd.uniform(-9.5, 9.5); y = rnd.uniform(-1.1, -16)
        if abs(x) < 0.75 and y > -1.9:
            continue
        if 0.1 < x < 1.9 and -3.4 < y < -1.0:  # keep the lens path behind her shoulder clear
            continue
        s = 0.28 * rnd.uniform(0.95, 1.12); fan = empty(f"Crowd{n}", (x, y, 0))
        fan.rotation_euler.z = rnd.uniform(-0.3, 0.3)
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
            if side == up_side and r < 0.7:  # this arm up, holding a phone or a lightstick
                shp.rotation_euler = (math.radians(rnd.uniform(150, 175)), math.radians(side * rnd.uniform(-15, 5)), 0)
                if r < 0.25:
                    cube(f"Phone{n}", (0.075, 0.014, 0.14), (0, -0.05, -2.25 * s), phone_m, shp)
                else:
                    cube(f"Stick{n}", (0.05, 0.05, 0.3), (0, 0, -2.45 * s), stick_m, shp)
                    wave_fcurve(shp, "rotation_euler", 1, 0.35, 2 * FPS * 60 / BPM, rnd.uniform(0, 6.28), shp.rotation_euler[1])
        wave_fcurve(fan, "location", 2, 0.035, FPS * 60 / BPM, rnd.uniform(0, 6.28), 0.035)
        n += 1
    print("crowd", n, "rail top", round(rail_top, 3), "rail y", round(rail_y, 3))
    # haze volume over the whole hall
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 6)); hz = bpy.context.active_object; hz.name = "Haze"
    hz.scale = (40, 50, 12)
    hm = bpy.data.materials.new("HazeM"); hm.use_nodes = True; nt = hm.node_tree; nt.nodes.clear()
    vs = nt.nodes.new("ShaderNodeVolumePrincipled"); vs.inputs["Density"].default_value = 0.028; vs.inputs["Anisotropy"].default_value = 0.6
    mo = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(vs.outputs[0], mo.inputs["Volume"]); hz.data.materials.append(hm)


def screen_mat():
    """Animated LED wall: drifting red/white bars over black (no text)."""
    m = bpy.data.materials.new("ScreenM"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); wv = nt.nodes.new("ShaderNodeTexWave")
    rp = nt.nodes.new("ShaderNodeValToRGB"); wv.inputs["Scale"].default_value = 3.0; wv.inputs["Distortion"].default_value = 2.0
    wv.wave_profile = "SAW"
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
    nt.links.new(wv.outputs["Fac"], rp.inputs["Fac"]); nt.links.new(rp.outputs["Color"], b.inputs["Emission Color"])
    e = rp.color_ramp.elements; e[0].position = 0.55; e[0].color = (0, 0, 0, 1); e[1].position = 0.9; e[1].color = (1, 0.92, 0.88, 1)
    r = rp.color_ramp.elements.new(0.72); r.color = (1, 0.04, 0.03, 1)
    b.inputs["Emission Strength"].default_value = 1.6
    loc = mp.inputs["Location"]
    loc.default_value = (0, 0, 0); loc.keyframe_insert("default_value", frame=1)
    loc.default_value = (0, 0, 3.0); loc.keyframe_insert("default_value", frame=END)
    return m


# ---------------------------------------------------------------- lights
def spot(name, loc, target, energy, color, size_deg, blend=0.2, radius=0.05):
    ld = bpy.data.lights.new(name, "SPOT"); ld.energy = energy; ld.color = color; ld.spot_size = math.radians(size_deg)
    ld.spot_blend = blend; ld.shadow_soft_size = radius
    o = bpy.data.objects.new(name, ld); bpy.context.scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o


def lights(a, head):
    # stage-front truss: white beams sweeping over the crowd (and across her) on a slow sine
    for k, x in enumerate((-6, -3, 0, 3, 6)):
        s = spot(f"BeamW{k}", (x, STAGE_Y + 0.6, 7.3), (x * 0.4, -6, 0.5), 9000, (1, 0.97, 0.92), 6, 0.1)
        wave_fcurve(s, "rotation_euler", 1, 0.35, 4 * FPS * 60 / BPM, k * 1.2)
    for k, x in enumerate((-7, 7)):  # red washes from the back truss onto the stage
        spot(f"StageRed{k}", (x, STAGE_Y + 5, 7.3), (x * 0.3, STAGE_Y + 2, STAGE_Z), 6000, (1, 0.05, 0.04), 35, 0.5, 0.4)
    spot("StageKey", (0, STAGE_Y - 3, 6.5), (0, STAGE_Y + 2.5, STAGE_Z + 1), 5000, (0.95, 0.95, 1.0), 30, 0.4, 0.3)
    # her: cold white face spot from the stage side + red rim from the back + white rim beam
    spot("FaceSpot", head + Vector((-1.4, 4.5, 2.6)), head, 650, (0.85, 0.9, 1.0), 14, 0.6, 0.15)
    spot("RimRed", head + Vector((1.6, -4.0, 2.2)), head, 900, (1, 0.05, 0.04), 18, 0.5, 0.3)
    spot("RimWhite", head + Vector((-1.8, -3.5, 3.0)), head, 1300, (1, 0.97, 0.92), 12, 0.4, 0.1)
    # soft spill over the audience so their outfits read (stage light bouncing back into the hall)
    for k, (y, col) in enumerate(((-4, (1.0, 0.75, 0.7)), (-10, (0.75, 0.8, 1.0)))):
        ld = bpy.data.lights.new(f"CrowdFill{k}", "AREA"); ld.shape = "RECTANGLE"; ld.size, ld.size_y = 18, 5
        ld.energy = 480; ld.color = col
        o = bpy.data.objects.new(f"CrowdFill{k}", ld); bpy.context.scene.collection.objects.link(o)
        o.location = (0, y + 1, 4.5); o.rotation_euler = (math.radians(-12), 0, 0)
    w = bpy.context.scene.world or bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.002, 0.002, 0.003, 1)


# ---------------------------------------------------------------- camera (one continuous move)
def camera(head):
    cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    tgt = empty("CamTarget", (0, 0, 0)); c = cam.constraints.new("TRACK_TO"); c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    h = Vector(head)
    keys = [  # frame, camera position, look target, lens
        (1, (1.2, -7.5, 3.6), (0.0, STAGE_Y + 6, 3.0), 30),
        (96, (0.85, -2.6, 2.25), (0.0, STAGE_Y + 3, 1.0), 30),   # holds on the stage through the main choreography
        (180, (1.55, -0.9, 1.6), h + Vector((-0.35, 1.3, 0.25)), 30),
        (238, (1.0, 1.75, 1.3), h, 40),
        (285, (0.55, 1.15, 1.22), h + Vector((0, 0, 0.02)), 55),
    ]
    for f, p, t, lens in keys:
        cam.location = p; cam.keyframe_insert("location", frame=f)
        tgt.location = t; tgt.keyframe_insert("location", frame=f)
        cd.lens = lens; cd.keyframe_insert("lens", frame=f)
    cd.dof.use_dof = True; cd.dof.focus_object = a_head_empty(head); cd.dof.aperture_fstop = 2.2
    return cam


def a_head_empty(head):
    return empty("FocusHead", head)


def render_setup():
    sc = bpy.context.scene
    try:
        sc.render.engine = "BLENDER_EEVEE"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080; sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, END
    ee = sc.eevee; ee.taa_render_samples = 48
    for attr, val in (("volumetric_end", 70.0), ("volumetric_tile_size", "4"), ("use_shadows", True), ("volumetric_samples", 96)):
        try:
            setattr(ee, attr, val)
        except Exception:
            pass
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - High Contrast"; sc.view_settings.exposure = 0.45
    sc.render.image_settings.file_format = "PNG"


def build():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    a = build_suhaa(); a["z0"] = a.location.z
    # base pose once (for barricade measurement + stick placement), then the motion bake
    from anim_motion import Actor
    tmp = Actor(a)
    suhaa_motion(a)
    bpy.context.scene.frame_set(1); upd()
    head = next(o for o in a.children if o.name.split(".")[0] == "Head")
    hc = head.matrix_world @ (sum((Vector(c) for c in head.bound_box), Vector()) / 8)
    venue(a)
    bpy.context.scene.frame_set(60); upd(); lightstick(a)
    xs = (-3.2, -1.6, 0.0, 1.6, 3.2)
    for i, x in enumerate(xs):
        root, parts = performer(i, x, STAGE_Y + 2.2 + (0.6 if i in (0, 4) else 0), LOOKS[i])
        dance(root, parts, i)
    lights(a, hc)
    camera(hc)
    render_setup()
    print("head", [round(v, 3) for v in hc])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "scene.blend"))


def stills(frames, pct=50):
    sc = bpy.context.scene; sc.render.resolution_percentage = pct
    for f in frames:
        sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "stills", f"f{f:03d}.png")
        bpy.ops.render.render(write_still=True)


def frames(a, b):
    sc = bpy.context.scene; sc.render.resolution_percentage = 100
    sc.frame_start, sc.frame_end = a, b; sc.render.filepath = os.path.join(OUT, "frames", "f")
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    cmd = argv[0] if argv else "build"
    if cmd == "build":
        build()
    elif cmd == "stills":
        stills([int(x) for x in argv[1].split(",")], int(argv[2]) if len(argv) > 2 else 50)
    elif cmd == "frames":
        frames(int(argv[1]) if len(argv) > 1 else 1, int(argv[2]) if len(argv) > 2 else END)
