"""15 s animation: Bio_IsHere knocks on Suhaa_Official's door, she asks "Are you Bio?", he says yes, she lets him in
and the door closes. Runs in its OWN headless Blender (never the shared GUI instance on port 9876):

  blender -b -P tools/anim_door.py -- build            -> gfx_output/anim_door/scene.blend
  blender -b gfx_output/anim_door/scene.blend -P tools/anim_door.py -- stills 0,90,...
  blender -b gfx_output/anim_door/scene.blend -P tools/anim_door.py -- frames [start end]

Subtitles, sound and the final mp4 are made by tools/anim_post.py from the rendered frames.
"""
import sys, os, math, json, glob
import bpy
from mathutils import Vector, Matrix

ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
OUT = os.path.join(ROOT, "gfx_output", "anim_door_v2")
LIB = os.path.join(ROOT, "library")
sys.path.insert(0, os.path.join(ROOT, "tools"))
FPS, END = 24, 360
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- avatars
def build_avatar(name, folder):
    """Run the shared builder (it wipes the scene), strip its stage, rename the armature."""
    G = {"__name__": "bx", "AVATAR_DIR": os.path.join(ROOT, "avatars", folder), "POSE": "idle"}
    exec(open(os.path.join(ROOT, "tools", "build_exact_gfx.py"), encoding="utf-8").read(), G)
    for o in list(bpy.data.objects):
        if o.name in ("Backdrop", "Halo") or o.type in ("LIGHT", "CAMERA"):
            bpy.data.objects.remove(o, do_unlink=True)
    a = bpy.data.objects["Avatar"]; a.name = name
    for o in a.children_recursive:
        o.name = f"{name}_{o.name}"
    return a


def upd():
    bpy.context.view_layer.update()


def feet_to_floor(a):
    upd()
    low = min((o.matrix_world @ Vector(c)).z for o in a.children_recursive if o.type == "MESH" for c in o.bound_box)
    a.location.z -= low; upd()


def head_z(a):
    upd(); h = next(o for o in a.children if o.name.endswith("_Head"))
    return max((h.matrix_world @ Vector(c)).z for c in h.bound_box) - 0.17


# ---------------------------------------------------------------- posing + keys (directions in the avatar's own frame:
# +Y = where it faces, +X = its right side P, +Z = up; they stay valid however the armature object is turned)
def aim(a, bone, d, hint=(0, 1, 0)):
    upd(); pb = a.pose.bones[bone]
    y = Vector(d).normalized(); h = Vector(hint); z = h - h.dot(y) * y
    if z.length < 0.2:
        h = Vector((0, 0, 1)) if abs(y.z) < 0.9 else Vector((0, 1, 0)); z = h - h.dot(y) * y
    z.normalize(); x = y.cross(z)
    m = Matrix((x, y, z)).transposed().to_4x4(); m.translation = pb.head
    pb.matrix = m


RELAX = [("UpperArm.P", (0.12, 0.03, -1)), ("LowerArm.P", (0.04, 0.1, -1)),
         ("UpperArm.N", (-0.12, 0.03, -1)), ("LowerArm.N", (-0.04, 0.1, -1))]
# Bio is the cool guy: left hand in his front pocket, hips shifted, leaning back a touch, chin up, one knee loose
COOL = [("LowerTorso", (0.07, 0, 1)), ("UpperTorso", (-0.06, -0.07, 1), (0.12, 1, 0)), ("Head", (0.06, -0.06, 1), (0.18, 1, 0.06)),
        ("UpperArm.N", (-0.1, -0.06, -1)), ("LowerArm.N", (0.3, 0.4, -0.85)),
        ("UpperArm.P", (0.16, 0.0, -1)), ("LowerArm.P", (0.1, 0.12, -1)),
        ("UpperLeg.P", (0.13, 0.02, -1)), ("UpperLeg.N", (-0.03, 0.1, -1)), ("LowerLeg.N", (0.03, -0.06, -1))]
# Suhaa is the kind host: hands loosely together in front, soft head tilt
KIND = [("UpperArm.P", (0.06, 0.25, -1)), ("LowerArm.P", (-0.55, 0.75, -0.25)),
        ("UpperArm.N", (-0.06, 0.25, -1)), ("LowerArm.N", (0.55, 0.75, -0.25)), ("Head", (-0.12, 0.04, 1))]
BASE = {"Bio": COOL, "Suhaa": KIND}


def pose_key(a, f, items=()):
    """Rest pose + the listed bones, keyed on every bone so poses never leak between keys."""
    for pb in a.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    upd()
    have = {i[0] for i in items}
    for item in [r for r in BASE.get(a.name, RELAX) if r[0] not in have] + list(items):
        bone, d, hint = item if len(item) == 3 else (*item, (0, 1, 0))
        aim(a, bone, d, hint)
        hand = bone.replace("LowerArm", "Hand")
        if bone.startswith("LowerArm") and hand not in have:
            aim(a, hand, d, (0, 0, 1) if abs(Vector(d).normalized().z) < 0.9 else (0, 1, 0))
    upd()
    for pb in a.pose.bones:
        pb.keyframe_insert("rotation_quaternion", frame=f); pb.keyframe_insert("location", frame=f)


def obj_key(o, f, loc=None, rz=None):
    if loc is not None:
        o.location.x, o.location.y = loc; o.keyframe_insert("location", frame=f)
    if rz is not None:
        o.rotation_euler.z = math.radians(rz); o.keyframe_insert("rotation_euler", frame=f)


def walk(a, f0, f1, extra=(), period=14, swing=0.5, cool=False):
    """Leg/arm swing keyed every 2 frames between f0 and f1 (object location is keyed separately)."""
    for f in range(f0, f1 + 1, 2):
        s = math.sin(2 * math.pi * (f - f0) / period)
        bend = max(0.0, -s) * 0.5
        legs = [("UpperLeg.P", (0.03, s * swing, -1)), ("LowerLeg.P", (0.0, s * swing - bend, -1)),
                ("UpperLeg.N", (-0.03, -s * swing, -1)), ("LowerLeg.N", (0.0, -s * swing - max(0.0, s) * 0.5, -1))]
        if cool:  # swagger: shoulders roll with the step, pocket hand stays, loose right arm, head bobs
            c = math.cos(4 * math.pi * (f - f0) / period)
            body = [("UpperTorso", (-0.05 + s * 0.05, -0.05, 1), (s * 0.18, 1, 0)), ("Head", (0.05, -0.05 + c * 0.04, 1), (0.1, 1, 0.05)),
                    ("UpperArm.P", (0.16, -s * 0.3, -1)), ("LowerArm.P", (0.08, -s * 0.3 + 0.2, -1))]
        else:
            body = [("UpperArm.P", (0.12, -s * 0.45, -1)), ("LowerArm.P", (0.05, -s * 0.45 + 0.15, -1)),
                    ("UpperArm.N", (-0.12, s * 0.45, -1)), ("LowerArm.N", (-0.05, s * 0.45 + 0.15, -1)), ("UpperTorso", (0, 0.04, 1))]
        pose_key(a, f, legs + body + list(extra))
    pose_key(a, f1 + 2)


# ---------------------------------------------------------------- set helpers
def mat(name, color, rough=0.6, metal=0.0, emit=None, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = strength
    return m


def pbr(name, scale=1.0, tint=None):
    import gfx_kit as k
    return k.pbr(name, scale, tint)


def box(name, size, loc, m, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object
    o.name = name; o.scale = size; o.data.materials.append(m)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if parent:
        o.parent = parent; o.location = Vector(loc) - parent.location
    return o


def model(cat, name, loc, rz=0.0, scale=1.0):
    f = glob.glob(os.path.join(LIB, "models", cat, name, "*.gltf")) + glob.glob(os.path.join(LIB, "models", cat, name, "*.glb")) \
        + glob.glob(os.path.join(LIB, "models", cat, name, "*.blend"))
    if not f:
        print("missing model", name); return None
    before = set(bpy.data.objects)
    if f[0].endswith(".blend"):
        with bpy.data.libraries.load(f[0]) as (src, dst):
            dst.objects = src.objects
        for o in dst.objects:
            if o: bpy.context.scene.collection.objects.link(o)
    else:
        bpy.ops.import_scene.gltf(filepath=f[0])
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name + "_root", None); bpy.context.scene.collection.objects.link(root)
    for o in new:
        if o.parent is None: o.parent = root
    root.location = loc; root.rotation_euler.z = math.radians(rz); root.scale = (scale,) * 3
    return root


def area(name, loc, target, energy, size, color):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size; ld.color = color
    o = bpy.data.objects.new(name, ld); bpy.context.scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o


def point(name, loc, energy, color, radius=0.1):
    ld = bpy.data.lights.new(name, "POINT"); ld.energy = energy; ld.color = color; ld.shadow_soft_size = radius
    o = bpy.data.objects.new(name, ld); bpy.context.scene.collection.objects.link(o); o.location = loc; return o


def text(body, loc, size, m, rot=(0, 0, 0), font="montserrat"):
    bpy.ops.object.text_add(location=loc, rotation=tuple(math.radians(r) for r in rot)); o = bpy.context.active_object
    o.data.body = body; o.data.size = size; o.data.align_x = "CENTER"; o.data.align_y = "CENTER"; o.data.extrude = 0.004
    ff = glob.glob(os.path.join(LIB, "fonts", font, "*.ttf"))
    if ff: o.data.font = bpy.data.fonts.load(ff[0], check_existing=True)
    o.data.materials.append(m); return o


def camera(name, loc, target, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens; c = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(c); c.location = loc
    c.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return c


def look(c, f, loc, target):
    c.location = loc; c.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    c.keyframe_insert("location", frame=f); c.keyframe_insert("rotation_euler", frame=f)


# ---------------------------------------------------------------- performance v2
WALK_SPEED = 0.6                                   # walk clip playback rate (Roblox walk cycle 0.67 s)
STEP = 0.667 / WALK_SPEED * FPS / 2                # frames between footfalls
LINES = {"ask": 174, "bio": 222, "come": 266}      # voice start frames; lengths come from the voice clips


def perform(b, s, hinge, hb, hs, sc):
    import importlib, anim_motion as am; importlib.reload(am)
    rb = math.radians
    vlen = {k: int(math.ceil(json.load(open(os.path.join(OUT, "voice", "lengths.json")))[k] * FPS)) for k in LINES}
    ask0, bio0, come0 = LINES["ask"], LINES["bio"], LINES["come"]
    ask1, bio1, come1 = ask0 + vlen["ask"], bio0 + vlen["bio"], come0 + vlen["come"]

    # ---- Bio: cool guy. Swagger walk on the real Roblox walk, left hand stays in his pocket the whole time.
    A = am.Actor(b, base=COOL, personality={"breath": 1.0, "sway": 1.3, "head": 0.8})
    pocket = [("UpperArm.N", (-0.1, -0.06, -1)), ("LowerArm.N", (0.3, 0.4, -0.85))]
    A.act(0, END, pocket, fade=1)
    obj_key(b, 0, (2.8, 0.75), 90); obj_key(b, 46, (0.25, 0.75), 90)
    A.clip("walk", -6, 48, speed=WALK_SPEED, fade=8)
    obj_key(b, 58, (0.05, 0.5), 180)                                  # turns to face the door
    A.clip("idle2", 46, END, speed=0.8, fade=10)
    # knock: pull back (anticipation), three raps, settle
    back = [("UpperArm.P", (0.25, 0.3, -0.7)), ("LowerArm.P", (0.05, 0.2, 0.9)), ("Hand.P", (0.05, 0.2, 0.9), (0, 1, 0))]
    up = [("UpperArm.P", (0.2, 0.6, -0.55)), ("LowerArm.P", (-0.2, 0.55, 0.6)), ("Hand.P", (-0.2, 0.55, 0.6), (0, 1, 0))]
    hit = [("UpperArm.P", (0.2, 0.7, -0.5)), ("LowerArm.P", (-0.2, 0.95, 0.2)), ("Hand.P", (-0.2, 0.95, 0.2), (0, 0, 1))]
    A.act(60, 66, back, fade=4); A.act(69, 96, up, fade=4)
    for t in (76, 84, 92):
        A.act(t - 1, t, hit, fade=3)
    A.act(108, 126, [("Head", (0.18, -0.02, 1), (0.45, 1, 0.05))], fade=8)       # glances down the street while he waits
    A.act(132, 150, [("UpperTorso", (-0.08, -0.1, 1), (0.1, 1, 0))], fade=8)     # leans back, patient
    # reply: chin-up nod, then a two-finger salute off the brow
    A.talking(bio0, bio1, 0.8)
    A.act(bio0 + 2, bio0 + 10, [("Head", (0.04, -0.22, 0.97), (0.1, 0.97, 0.22))], fade=4)
    sal_a = [("UpperArm.P", (0.5, 0.3, 0.45)), ("LowerArm.P", (-0.45, 0.35, 0.8)), ("Hand.P", (-0.45, 0.35, 0.8), (0, 1, 0))]
    sal_b = [("UpperArm.P", (0.7, 0.35, 0.4)), ("LowerArm.P", (0.55, 0.6, 0.55)), ("Hand.P", (0.55, 0.6, 0.55), (0, 1, 0))]
    A.act(bio0 + 14, bio0 + 24, sal_a, fade=5); A.act(bio0 + 28, bio1 + 4, sal_b, fade=6)
    # walks in when invited
    walk_in0 = come1 - 4
    obj_key(b, walk_in0, (0.05, 0.5), 180); obj_key(b, walk_in0 + 36, (0.0, -1.75), 180)
    A.clip("walk", walk_in0 - 2, walk_in0 + 36, speed=WALK_SPEED, fade=8)
    A.bake(range(0, END), FPS)

    # ---- Suhaa: kind host. Idle, walks to the door, opens it, happy little bounce, asks, welcomes him in.
    S = am.Actor(s, base=KIND, personality={"breath": 1.1, "sway": 0.8, "head": 1.2})
    S.clip("idle2", 0, END, speed=0.9, offset=0.7, fade=1)
    obj_key(s, 0, (0.0, -2.6), 0); obj_key(s, 100, (0.0, -2.6), 0); obj_key(s, 136, (0.05, -1.08), 0)
    S.clip("walk", 98, 138, speed=WALK_SPEED * 1.25, fade=8)
    S.act(134, 156, [("UpperArm.N", (-0.35, 0.8, -0.3)), ("LowerArm.N", (-0.3, 0.9, -0.1))], fade=6)  # reaches for the knob
    hinge.rotation_euler.z = 0; hinge.keyframe_insert("rotation_euler", frame=140)
    hinge.rotation_euler.z = rb(-102); hinge.keyframe_insert("rotation_euler", frame=160)
    obj_key(s, 156, (0.05, -1.08)); obj_key(s, 170, (0.05, -0.42))
    S.clip("walk", 154, 172, speed=WALK_SPEED * 1.25, fade=6)
    S.act(166, 174, [("Head", (-0.2, 0.1, 1), (0, 1, 0.15)), ("UpperTorso", (0, 0.12, 1))], fade=4)  # happy bounce forward
    S.talking(ask0, ask1, 1.0)
    S.act(ask0, ask1, [("Head", (0.22, 0.05, 1), (0, 1, 0.05)), ("UpperArm.P", (0.2, 0.45, -0.75)),
                       ("LowerArm.P", (0.05, 0.95, 0.25))], fade=7)                  # friendly open palm, head tilt
    S.talking(come0, come1, 1.2)
    S.act(come0 + 2, come1 + 8, [("UpperArm.P", (0.6, 0.45, -0.45)), ("LowerArm.P", (0.6, 0.5, 0.2)),
                                 ("UpperArm.N", (-0.6, 0.45, -0.45)), ("LowerArm.N", (-0.6, 0.5, 0.2)),
                                 ("Head", (-0.15, 0.05, 1), (0, 1, 0.1))], fade=8)     # open arms, warm welcome
    obj_key(s, come1 + 4, (0.05, -0.42), 0); obj_key(s, come1 + 22, (0.95, -0.75), -90)  # steps aside
    S.clip("walk", come1 + 2, come1 + 24, speed=WALK_SPEED * 1.25, fade=6)
    close0 = walk_in0 + 30
    S.act(close0 - 2, close0 + 16, [("UpperArm.N", (-0.6, 0.6, -0.2)), ("LowerArm.N", (-0.5, 0.8, 0))], fade=6)
    hinge.rotation_euler.z = rb(-102); hinge.keyframe_insert("rotation_euler", frame=close0)
    hinge.rotation_euler.z = 0; hinge.keyframe_insert("rotation_euler", frame=close0 + 14)
    S.bake(range(0, END), FPS)

    # ---- cameras: wide push-in / inside two-shot for the whole conversation / wide ending
    cw = camera("CamWide", (1.6, 4.4, 1.5), (0.1, 0.0, 1.0), 32)
    look(cw, 0, (1.9, 4.6, 1.55), (0.6, 0.2, 1.0)); look(cw, 160, (1.15, 3.6, 1.45), (0.0, -0.2, 1.0))
    co = camera("CamOTS", (0.95, -1.5, hs + 0.15), (-0.3, 0.1, hb - 0.12), 30)
    look(co, 164, (1.0, -1.55, hs + 0.15), (-0.3, 0.1, hb - 0.12)); look(co, walk_in0, (0.88, -1.35, hs + 0.13), (-0.3, 0.1, hb - 0.1))
    ce = camera("CamEnd", (1.3, 3.9, 1.5), (0.0, -0.4, 1.0), 30)
    look(ce, walk_in0, (1.3, 3.9, 1.5), (0.0, -0.4, 1.0)); look(ce, END, (0.8, 3.2, 1.45), (0.0, -0.2, 1.1))
    for f, c in ((0, cw), (164, co), (walk_in0, ce)):
        m = sc.timeline_markers.new(c.name, frame=f); m.camera = c
    sc.camera = cw

    # ---- cues for anim_post (sound + subtitles), all in frames
    steps_bio = [round(i * STEP) for i in range(1, int(46 / STEP) + 1)] + \
                [round(walk_in0 + i * STEP) for i in range(1, int(36 / STEP) + 1)]
    st = STEP / 1.25
    steps_suhaa = [round(98 + i * st) for i in range(1, int(38 / st) + 1)] + [round(154 + i * st) for i in range(1, int(16 / st) + 1)] + \
                  [round(come1 + 2 + i * st) for i in range(1, int(20 / st) + 1)]
    cues = {"fps": FPS, "frames": END, "voice": {"ask": ask0, "bio": bio0, "come": come0},
            "knocks": [76, 84, 92], "door_open": 140, "door_close_start": close0, "door_shut": close0 + 14,
            "steps_bio_out": [f for f in steps_bio if f < 100], "steps_bio_in": [f for f in steps_bio if f >= 100],
            "steps_suhaa": steps_suhaa,
            "subs": [[70, 100, None, "[knocking]"], [140, 162, None, "[door creaks open]"],
                     [ask0, ask1 + 6, "Suhaa", "Are you Bio?"], [bio0, bio1 + 6, "Bio", "Yeah. That's me."],
                     [come0, come1 + 6, "Suhaa", "Aww, come on in!"], [close0 + 8, END - 1, None, "[door closes]"]],
            "cams": {"CamWide": 0, "CamOTS": 164, "CamEnd": walk_in0}}
    json.dump(cues, open(os.path.join(OUT, "cues.json"), "w"), indent=1)
    print("cues", cues["voice"], "walk_in", walk_in0, "close", close0)


# ---------------------------------------------------------------- build
def build():
    # Suhaa first, saved to a temp file, because the builder wipes the scene for Bio
    s = build_avatar("Suhaa", "Suhaa_Official_v2")
    tmp = os.path.join(OUT, "_suhaa.blend")
    bpy.data.libraries.write(tmp, {s, *s.children_recursive}, fake_user=True)
    b = build_avatar("Bio", "Bio_IsHere")
    with bpy.data.libraries.load(tmp) as (src, dst):
        dst.objects = [n for n in src.objects]
    for o in dst.objects:
        bpy.context.scene.collection.objects.link(o)
    s = bpy.data.objects["Suhaa"]
    for a in (b, s):
        a.location = (0, 0, 0); a.rotation_euler = (0, 0, 0); feet_to_floor(a)
    hb, hs = head_z(b), head_z(s)
    print("heights", round(hb, 2), round(hs, 2))

    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 0, END - 1; sc.render.fps = FPS

    # --- house front: wall with a door hole (x -0.47..0.47, z 0..2.15), the door hinged at x=-0.45
    wall = pbr("painted_plaster_wall", 0.8, tint=(0.6, 0.55, 0.52))
    box("WallL", (3.6, 0.2, 3.3), (-0.47 - 1.8, -0.1, 1.65), wall)
    box("WallR", (3.6, 0.2, 3.3), (0.47 + 1.8, -0.1, 1.65), wall)
    box("WallTop", (0.94, 0.2, 1.15), (0, -0.1, 2.15 + 0.575), wall)
    trim = mat("Trim", (0.85, 0.83, 0.8), 0.4)
    box("FrameL", (0.07, 0.24, 2.2), (-0.5, -0.1, 1.1), trim); box("FrameR", (0.07, 0.24, 2.2), (0.5, -0.1, 1.1), trim)
    box("FrameT", (1.07, 0.24, 0.08), (0, -0.1, 2.19), trim)
    hinge = bpy.data.objects.new("Hinge", None); sc.collection.objects.link(hinge); hinge.location = (-0.45, -0.06, 0)
    door_m = pbr("wood_cabinet_worn_long", 1.0, tint=(0.55, 0.22, 0.2))
    box("Door", (0.9, 0.05, 2.13), (0, -0.06, 1.075), door_m, parent=hinge)
    for zz in (0.55, 1.55):  # raised panels
        box("DoorPanel", (0.62, 0.012, 0.7), (0, 0.04 - 0.06 + 0.0, zz), door_m, parent=hinge)
    gold = mat("Brass", (0.9, 0.65, 0.3), 0.25, 1.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(0.33, 0.0, 1.0)); kn = bpy.context.active_object
    kn.name = "Knob"; kn.data.materials.append(gold); kn.parent = hinge; kn.location = Vector((0.33, 0.0, 1.0)) - hinge.location
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(0.33, -0.12, 1.0)); kn2 = bpy.context.active_object
    kn2.name = "KnobIn"; kn2.data.materials.append(gold); kn2.parent = hinge; kn2.location = Vector((0.33, -0.12, 1.0)) - hinge.location
    num = text("12", (0, 0.01, 1.85), 0.12, gold, rot=(90, 0, 0))
    num.parent = hinge; num.location = Vector((0.45, 0.07, 1.85))
    # windows each side, warm glow from inside
    glow = mat("WindowGlow", (0.01, 0.008, 0.006), 0.08, emit=(1.0, 0.62, 0.32), strength=0.8)
    curtain = mat("Curtain", (0.55, 0.32, 0.36), 0.9)
    curtain.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.0
    for x in (-1.75, 1.75):
        box("Window", (0.9, 0.05, 1.0), (x, 0.02, 1.45), glow)
        box("WinFrameH", (1.0, 0.08, 0.06), (x, 0.03, 1.97), trim); box("WinFrameH", (1.0, 0.08, 0.06), (x, 0.03, 0.93), trim)
        box("WinFrameV", (0.06, 0.08, 1.1), (x - 0.48, 0.03, 1.45), trim); box("WinFrameV", (0.06, 0.08, 1.1), (x + 0.48, 0.03, 1.45), trim)
        box("WinCross", (0.03, 0.06, 1.0), (x, 0.04, 1.45), trim); box("WinCross", (0.9, 0.06, 0.03), (x, 0.04, 1.45), trim)
        for cx in (x - 0.33, x + 0.33):  # half-drawn curtains in front of the glow
            box("Curtain", (0.26, 0.02, 0.98), (cx, 0.055, 1.45), curtain)
        box("Valance", (0.92, 0.025, 0.16), (x, 0.058, 1.87), curtain)
    box("Roof", (8.0, 1.0, 0.12), (0, 0.35, 3.3), mat("RoofDark", (0.12, 0.07, 0.06), 0.7))
    # porch, step, doormat, plants, lantern
    box("Porch", (3.2, 2.0, 0.08), (0, 1.0, -0.04), pbr("concrete_floor_02", 1.0, tint=(0.7, 0.68, 0.66)))
    box("Ground", (30, 30, 0.02), (0, 0, -0.1), pbr("gravel_embedded_concrete", 0.6, tint=(0.35, 0.37, 0.33)))
    box("Mat", (0.85, 0.5, 0.012), (0, 0.42, 0.006), mat("MatRed", (0.35, 0.08, 0.06), 0.95))
    text("WELCOME", (0, 0.42, 0.014), 0.11, mat("MatText", (0.9, 0.75, 0.55), 0.9), rot=(0, 0, 180))
    model("plants", "potted_plant_01", (-0.95, 0.35, 0), 0, 1.0)
    model("plants", "potted_plant_02", (0.95, 0.35, 0), 0, 1.0)
    model("props", "Lantern_01", (0.78, 0.12, 1.75), 0, 1.0)
    # interior: floor, walls, ceiling light, sofa, picture
    box("InFloor", (6, 4, 0.02), (0, -2.2, -0.01), pbr("laminate_floor_02", 1.2))
    inwall = mat("InWall", (0.78, 0.62, 0.62), 0.8)
    box("InBack", (6, 0.1, 3.0), (0, -4.0, 1.5), inwall)
    box("InSideL", (0.1, 4, 3.0), (-2.6, -2.1, 1.5), inwall); box("InSideR", (0.1, 4, 3.0), (2.6, -2.1, 1.5), inwall)
    box("InCeil", (6, 4, 0.1), (0, -2.1, 3.0), inwall)
    model("furniture", "sofa_02", (-0.6, -3.5, 0), 0, 1.0)
    model("decorative", "fancy_picture_frame_01", (0.6, -3.93, 1.6), 0, 1.0)
    model("lighting", "modern_ceiling_lamp_01", (0, -2.0, 2.95), 0, 1.0)

    # --- lights: moonlit night outside, warm porch lantern, warm interior
    w = sc.world or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.01, 0.03, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    sun = bpy.data.lights.new("Moon", "SUN"); sun.energy = 0.35; sun.color = (0.55, 0.65, 1.0); sun.angle = 0.05
    mo = bpy.data.objects.new("Moon", sun); sc.collection.objects.link(mo); mo.rotation_euler = (math.radians(50), 0, math.radians(150))
    point("Lantern", (0.78, 0.3, 1.9), 45, (1.0, 0.68, 0.35), 0.08)
    area("PorchFill", (1.5, 3.0, 2.6), (0, 0.4, 1.0), 35, 2.5, (0.55, 0.65, 1.0))
    area("InLight", (0, -2.0, 2.85), (0, -2.0, 0), 300, 1.6, (1.0, 0.75, 0.48))
    area("InBounce", (0, -1.2, 1.6), (0, 0.5, 1.2), 60, 1.0, (1.0, 0.7, 0.45))

    # --- performance v2: real Roblox clips + acting layers + breathing/sway/talking (tools/anim_motion.py)
    perform(b, s, hinge, hb, hs, sc)

    # --- render settings: EEVEE, 1920x1080, AgX
    sc.render.engine = "BLENDER_EEVEE"
    try:
        sc.eevee.taa_render_samples = 48; sc.eevee.use_raytracing = True
    except AttributeError:
        pass
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.view_settings.view_transform = "AGX" if "AGX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "AgX"
    sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -0.2
    sc.render.image_settings.file_format = "PNG"
    # speaker head positions per line for the subtitle tool
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "scene.blend"))
    print("built")


def render_frames(frames, folder="frames", pct=100):
    sc = bpy.context.scene; sc.render.resolution_percentage = pct
    os.makedirs(os.path.join(OUT, folder), exist_ok=True)
    for f in frames:
        sc.frame_set(f)
        for m in sorted(sc.timeline_markers, key=lambda m: m.frame):  # marker camera binding for single-frame renders
            if m.frame <= f: sc.camera = m.camera
        sc.render.filepath = os.path.join(OUT, folder, f"{f:04d}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["build"]
    if argv[0] == "build":
        build()
    elif argv[0] == "stills":
        render_frames([int(x) for x in argv[1].split(",")], "stills", 50)
    elif argv[0] == "frames":
        a, z = (int(argv[1]), int(argv[2])) if len(argv) > 2 else (0, END - 1)
        render_frames(range(a, z + 1), "frames", 100)
