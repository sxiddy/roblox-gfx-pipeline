"""Pilot scene, shots 1, 2 and 4 (shot 3 is tools/pilot_shot.py). docs/SUPERIOR_PLAN.md step 8. Own headless Blender:
    blender -b --factory-startup -P tools/pilot_scene.py -- build s1      (saves pilot/s1/scene.blend, runs the gates)
    blender -b pilot/s1/scene.blend -P tools/pilot_scene.py -- stills s1 4,40
    blender -b pilot/s1/scene.blend -P tools/pilot_scene.py -- frames s1

Pose and camera plan (avatar Bio_IsHere, faces +Y, his right = +X; yaw + = his left, pitch + = chin up, roll + = his left):
  all shots  legs straight and planted, arms hang with a small bend (right forearm 14 deg forward, left 8 deg),
             chest turned 15 deg to his right, breathing 0.25 Hz, hips sway 1.6 deg, feet out of frame.
  s1 arrive  44 f. Tripod low at knee height, 26 deg to his right, 20 deg below the head, 35 mm, head 19% of the width
             at (0.56, 0.24): mid-thigh up. Head held 32 deg to his right (looking off). Blurred post near the lens, left.
  s2 notice  40 f. Side-on from his right (61 deg), eye level, 60 mm, head 20% at (0.42, 0.40): chest up. Head turns from
             32 deg right toward the front, still moving at the cut. Blink on the turn. Side wall + rust door behind.
  s4 line 2  Low medium close: 7 deg to his left, 26 deg below the head, 50 mm, head 30% at (0.5, 0.42). Chin 5 deg down
             to the lens, roll 7 deg, nods on the stressed words. Line "Then let's get started." from frame 14.
Light per shot, placed from the camera: warm soft key upper left, cool rim behind right, weak fill, a pool on the wall."""
import json, math, os, random, sys, wave
import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
PILOT = os.path.join(ROOT, "gfx_output", "Bio_IsHere", "pilot")
AVATAR = os.path.join(ROOT, "avatars", "Bio_IsHere_2026-11-16")
FPS = 24
argv = sys.argv[sys.argv.index("--") + 1:]; MODE, SHOT = argv[0], argv[1]
OUT = os.path.join(PILOT, SHOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

SHOTS = {
    "s1": dict(end=44, lens=35, head_frac=0.19, head_xy=(0.56, 0.24), view=(0.5, 1, -0.41), push=0.05, solve=22, blinks=(20,),
               cam={"elevation": [-26, -14], "azimuth": [20, 33], "lens": [34, 36]}),
    "s2": dict(end=40, lens=60, head_frac=0.20, head_xy=(0.42, 0.40), view=(1, 0.55, 0.0), push=0.03, solve=20, blinks=(17,),
               cam={"elevation": [-5, 5], "azimuth": [55, 67], "lens": [59, 61]}),
    "s4": dict(end=None, lens=50, head_frac=0.30, head_xy=(0.5, 0.42), view=(-0.12, 1, -0.5), push=0.05, solve=24, blinks=(6,),
               voice=14, wav=os.path.join(PILOT, "line2.wav"), text="Then let's get started.",
               cam={"elevation": [-32, -20], "azimuth": [-12, -2], "lens": [49, 51]}),
}
S = SHOTS[SHOT]
if S["end"] is None:
    with wave.open(S["wav"]) as w:
        S["end"] = S["voice"] + math.ceil(w.getnframes() / w.getframerate() * FPS) + 22
END = S["end"]


def smooth(f, a, b):
    t = min(max((f - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def build():
    os.makedirs(OUT, exist_ok=True)
    G = {"__name__": "bx", "AVATAR_DIR": AVATAR, "POSE": "idle"}
    exec(open(os.path.join(ROOT, "tools", "build_exact_gfx.py"), encoding="utf-8").read(), G)
    import gfx_kit as k, face_rig as fr, lipsync as ls, gate
    for o in list(bpy.data.objects):
        if o.name in ("Backdrop", "Halo") or o.type == "LIGHT":
            bpy.data.objects.remove(o, do_unlink=True)
    # Planned hidden in every shot of this scene: Handle2 = sparkle aura (0.63 x 0.6 x 0.7 m, 264 faces, on the Head).
    bpy.data.objects["Handle2"].hide_render = True
    print("FACE", fr.build())
    s = bpy.context.scene; s.render.fps = FPS; s.frame_start = 1; s.frame_end = END
    a = k.arm()
    fr.pose("neutral", frame=1)
    stress = []; last = 0
    if S.get("wav"):
        cues = ls.rhubarb(S["wav"], S["text"]); last = ls.apply(cues, start_frame=S["voice"])
        stress = [S["voice"] + round(c[0] * FPS) for c in cues if c[2] >= 0.5]
        stress = [f for i, f in enumerate(stress) if i == 0 or f - stress[i - 1] >= 8]
        fr.blink(min(END - 6, last + 10))
    for b in S["blinks"]:
        fr.blink(b)
    print("END", END, "LAST", last, "STRESS", stress)

    def nod(f):
        return sum(-3.2 * math.exp(-((f - (c + 1)) / 3.0) ** 2) for c in stress)
    drift = lambda f, p, ph=0.0: math.sin(f / p + ph)
    if SHOT == "s1":
        head = lambda f: (-32 + 1.5 * drift(f, 29), 4 + 0.8 * drift(f, 23, 1), -3 + 1.0 * drift(f, 37))
    elif SHOT == "s2":
        def head(f):
            t = smooth(f, 14, 46)
            return (-32 + 24 * t + 1.0 * drift(f, 31), 4 - 3 * t - 2.0 * math.exp(-((f - 16) / 4.0) ** 2), -3 + 4 * t)
    else:
        def head(f):
            lift = 3.0 * math.exp(-((f - 7) / 3.5) ** 2)
            return (7 + 1.2 * drift(f, 31), -5 + lift + nod(f) + 0.8 * drift(f, 23, 1), 7 + 1.0 * drift(f, 37))
    chest = lambda f: (-15 + (4 if SHOT == "s4" else 0) + 0.8 * drift(f, 41), 4 + 1.3 * math.sin(2 * math.pi * f / 96.0), 0.0)
    hips = lambda f: (0.0, 0.0, 1.6 * math.sin(2 * math.pi * f / 130.0 + 0.7))
    sway = lambda f, lag: 1.4 * math.sin(2 * math.pi * (f - lag) / 96.0)
    arms = {"UpperArm.P": lambda f: (0, 4 + sway(f, 2), -5), "LowerArm.P": lambda f: (0, 14 + sway(f, 3), 0),
            "UpperArm.N": lambda f: (0, 2 + sway(f, 2), 4), "LowerArm.N": lambda f: (0, 8 + sway(f, 3), 0)}

    def key(bone, ypr, f):
        pb = a.pose.bones[bone]; pb.rotation_mode = "QUATERNION"
        y, p, r = (math.radians(v) for v in ypr)
        R = (Matrix.Rotation(y, 3, "Z") @ Matrix.Rotation(p, 3, "X") @ Matrix.Rotation(r, 3, "Y"))
        B = pb.bone.matrix_local.to_3x3()
        pb.rotation_quaternion = (B.inverted() @ R @ B).to_quaternion()
        pb.keyframe_insert("rotation_quaternion", frame=f)
    for f in sorted(set(range(1, END + 1, 2)) | {END}):
        key("LowerTorso", hips(f), f); key("UpperTorso", chest(f), f); key("Head", head(f), f)
        for b, fn in arms.items():
            if b in a.pose.bones:
                key(b, fn(f), f)

    # ---- camera, solved on the pose of the shot's middle
    s.frame_set(S["solve"])
    s.render.resolution_x = 1920; s.render.resolution_y = 1080
    k.frame_head(S["head_frac"], head_xy=S["head_xy"], view_dir=S["view"], lens=S["lens"])
    cam = s.camera; H = k.head_center(); base = cam.location.copy(); fwd = (H - base).normalized()
    dist = (H - base).length; rot0 = cam.rotation_euler.copy(); rnd = random.Random(7 + len(SHOT) + ord(SHOT[1]))
    for f in sorted(set(range(1, END + 1, 6)) | {END}):
        cam.location = base + fwd * (dist * S["push"] * (f - S["solve"]) / (END - 1))
        cam.rotation_euler = (rot0.x + math.radians(rnd.uniform(-0.3, 0.3)), rot0.y + math.radians(rnd.uniform(-0.12, 0.12)),
                              rot0.z + math.radians(rnd.uniform(-0.3, 0.3)))
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    foc = bpy.data.objects.new("Focus", None); s.collection.objects.link(foc)
    foc.parent = a; foc.parent_type = "BONE"; foc.parent_bone = "Head"
    cam.data.dof.use_dof = True; cam.data.dof.focus_object = foc; cam.data.dof.aperture_fstop = 2.8
    s.frame_set(S["solve"])

    # ---- set: same dark concrete room as shot 3, with side walls, pipes and a rust door for depth
    conc = k.pbr("concrete_layers_02", scale=0.6, tint=(0.3, 0.31, 0.33))
    k.plane("Floor", (12, 12), (0, 0, 0), k.pbr("asphalt_02", 1.2, tint=(0.3, 0.3, 0.33)))
    k.cube("Wall", (9, 0.2, 10), (0, -2.7, H.z + 2), conc)
    k.cube("WallL", (0.2, 9, 10), (-3.4, 1, H.z + 2), conc); k.cube("WallR", (0.2, 9, 10), (3.4, 1, H.z + 2), conc)
    metal = k.material("DarkMetal", (0.04, 0.045, 0.05), 0.35, 0.9)
    for i, x in enumerate((1.7, 1.9, -2.3)):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=10, location=(x, -2.53, H.z + 2)); o = bpy.context.active_object
        o.name = f"Pipe{i}"; o.data.materials.append(metal)
    k.cube("Door", (0.06, 1.1, 2.2), (-3.28, 0.5, 1.1), k.pbr("rust_coarse_01", 0.8, tint=(0.4, 0.36, 0.33)))
    scr_left = fwd.cross(Vector((0, 0, 1))).normalized() * -1
    if SHOT == "s1":
        up = scr_left.cross(fwd).normalized() * -1
        bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=4, location=base + fwd * 0.55 + scr_left * 0.19 + up * 0.0)
        o = bpy.context.active_object; o.name = "PostNear"; o.data.materials.append(metal)

    # ---- light, placed from the camera like shot 3
    k.upd()
    hit, P, n, *_ = s.ray_cast(bpy.context.evaluated_depsgraph_get(), H + fwd * 1.0, fwd)
    if not hit:
        P = H + fwd * 2.7; n = -fwd
    n = Vector(n); n = -n if n.dot(fwd) > 0 else n
    Z = Vector((0, 0, 1))
    k.area("Key", H - fwd * 1.5 + scr_left * 1.3 + Z * 0.9, H, 70, size=0.7, color=(1.0, 0.8, 0.58), spread=80)
    k.area("Rim", H + fwd * 1.5 - scr_left * 0.9 + Z * 0.6, H, 520, size=0.5, color=(0.45, 0.72, 1.0))
    k.area("Fill", H - fwd * 1.6 - scr_left * 1.4 + Z * -0.1, H, 2.5, size=1.6, color=(0.6, 0.75, 1.0))
    k.area("WallPool", P + n * 1.2 + Z * 1.2 - scr_left * 1.2, P + Z * 0.2 - scr_left * 0.8, 34, size=0.8, color=(1.0, 0.8, 0.6), spread=80)
    k.world(color=(0.012, 0.016, 0.022), strength=1.0)
    s.render.engine = "BLENDER_EEVEE"; s.eevee.taa_render_samples = 48; s.eevee.use_raytracing = True
    s.render.use_motion_blur = True; s.render.motion_blur_shutter = 0.5
    s.view_settings.view_transform = "AgX"; s.view_settings.look = "AgX - Punchy"
    print("HEAD", tuple(round(v, 2) for v in H), "CAMDIST", round(dist, 2), "BG", tuple(round(v, 2) for v in P),
          "STRAY", [o.name for o in bpy.data.objects if o.type == "MESH" and o.parent is None])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "scene.blend"))

    job = {"name": "pilot_" + SHOT, "avatar_dir": AVATAR.replace("\\", "/"), "avatar_fresh_days": 1, "engine": "BLENDER_EEVEE",
           "allow_names": ["Floor", "Wall", "WallL", "WallR", "Door", "Pipe0", "Pipe1", "Pipe2", "PostNear", "Focus"],
           "support": "ground", "planned_hidden": ["Handle2"], "see_through": ["PostNear", "FaceRig"],
           "face": {"min_visible": 0.7, "max_turn": 75}, "head_frac": round(S["head_frac"] * 0.8, 3), "head_xy": list(S["head_xy"]), "tol": 0.05,
           "out_of_frame": ["Foot.P", "Foot.N"], "camera": S["cam"],
           "motion": {"frames": [1, END], "armatures": ["Avatar"], "max_deg": {"default": 25}, "max_frozen": 12, "slide_tol": 0.01}}
    jp = os.path.join(OUT, "job.json"); json.dump(job, open(jp, "w"), indent=1)
    print("GATE", gate.run(jp, ["scene", "body", "face", "frame", "camera", "motion"]))


def render(frames, pct, sub):
    s = bpy.context.scene; s.render.resolution_percentage = pct; s.render.image_settings.file_format = "PNG"
    s.frame_set(1); s.render.filepath = os.path.join(OUT, "_throwaway.png"); bpy.ops.render.render(write_still=True)
    for f in frames:
        s.frame_set(f); s.render.filepath = os.path.join(OUT, sub, f"f_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
    print("RENDERED", len(frames))


if MODE == "build":
    build()
elif MODE == "stills":
    render([int(v) for v in argv[2].split(",")], 50, "stills")
elif MODE == "frames":
    render(list(range(1, bpy.context.scene.frame_end + 1)), 50, "frames")
