"""Pilot: one close-up talking shot in the Ink Game look (docs/SUPERIOR_PLAN.md step 8). Own headless Blender:
    blender -b --factory-startup -P tools/pilot_shot.py -- build                (saves pilot/scene.blend)
    blender -b pilot/scene.blend -P tools/pilot_shot.py -- stills 12,30,44,60,100
    blender -b pilot/scene.blend -P tools/pilot_shot.py -- frames
Avatar Bio_IsHere, line "You really thought I wouldn't show up?", 24 fps, 110 frames, voice starts on frame 36.
Rotations below are in armature space: yaw + = his left, pitch + = chin up, roll + = tilt to his left shoulder."""
import math, os, random, sys
import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
OUT = os.path.join(ROOT, "gfx_output", "Bio_IsHere", "pilot")
WAV = os.path.join(OUT, "line.wav"); TEXT = "You really thought I wouldn't show up?"
END = 110; VOICE = 36; FPS = 24
argv = sys.argv[sys.argv.index("--") + 1:]; MODE = argv[0]
sys.path.insert(0, os.path.join(ROOT, "tools"))


def smooth(f, a, b):
    t = min(max((f - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def build():
    G = {"__name__": "bx", "AVATAR_DIR": os.path.join(ROOT, "avatars", "Bio_IsHere_2026-11-16"), "POSE": "idle"}
    exec(open(os.path.join(ROOT, "tools", "build_exact_gfx.py"), encoding="utf-8").read(), G)
    import gfx_kit as k, face_rig as fr, lipsync as ls
    for o in list(bpy.data.objects):
        if o.name in ("Backdrop", "Halo") or o.type == "LIGHT":
            bpy.data.objects.remove(o, do_unlink=True)
    # Planned hidden: Handle2 = his sparkle aura (0.63 x 0.6 x 0.7 m, 264 faces, on the Head). In a face close-up
    # its stars float across the cheek and mouth. Hidden for this shot only; the avatar is not changed.
    bpy.data.objects["Handle2"].hide_render = True
    print("FACE", fr.build())
    s = bpy.context.scene; s.render.fps = FPS; s.frame_start = 1; s.frame_end = END
    a = k.arm()
    # ---- face: lip sync and blinks
    fr.pose("neutral", frame=1)
    cues = ls.rhubarb(WAV, TEXT); last = ls.apply(cues, start_frame=VOICE)
    fr.blink(16); fr.blink(last + 12)
    # No smirk: rotating the whole mouth only tilts a straight zigzag mouth (owner: "why is the mouth slanting").
    stress = [VOICE + round(c[0] * FPS) for c in cues if c[2] >= 0.5]
    stress = [f for i, f in enumerate(stress) if i == 0 or f - stress[i - 1] >= 8]
    print("LAST", last, "STRESS", stress)

    # ---- body: every bone keyed every 2 frames from smooth functions, so nothing is ever frozen
    def nod(f):
        return sum(-3.2 * math.exp(-((f - (c + 1)) / 3.0) ** 2) for c in stress)
    def head(f):
        turn = smooth(f, 10, 26); over = 3.0 * math.exp(-((f - 27) / 4.0) ** 2)
        return (-8 + 36 * turn + over + 1.2 * math.sin(f / 31.0), 7 * turn + nod(f) + 0.8 * math.sin(f / 23.0 + 1),
                6 * turn + 1.0 * math.sin(f / 37.0))
    def chest(f):
        return (-15 + 4 * smooth(f, 6, 24) + 0.8 * math.sin(f / 41.0), 4 + 1.3 * math.sin(2 * math.pi * f / 96.0), 0.0)
    def hips(f):
        return (0.0, 0.0, 1.6 * math.sin(2 * math.pi * f / 130.0))
    def key(bone, ypr, f):
        pb = a.pose.bones[bone]; pb.rotation_mode = "QUATERNION"
        y, p, r = (math.radians(v) for v in ypr)
        R = (Matrix.Rotation(y, 3, "Z") @ Matrix.Rotation(p, 3, "X") @ Matrix.Rotation(r, 3, "Y"))
        B = pb.bone.matrix_local.to_3x3()
        pb.rotation_quaternion = (B.inverted() @ R @ B).to_quaternion()
        pb.keyframe_insert("rotation_quaternion", frame=f)
    for f in range(1, END + 1, 2):
        key("LowerTorso", hips(f), f); key("UpperTorso", chest(f), f); key("Head", head(f), f)

    # ---- camera: 85 mm, to his left, a little below eye level; solved on the pose he holds while talking
    s.frame_set(VOICE + 10)
    s.render.resolution_x = 1920; s.render.resolution_y = 1080
    k.frame_head(0.27, head_xy=(0.43, 0.45), view_dir=(-0.36, 1, -0.07), lens=85)
    cam = s.camera; H = k.head_center(); base = cam.location.copy(); fwd = (H - base).normalized()
    dist = (H - base).length; rot0 = cam.rotation_euler.copy(); rnd = random.Random(7)
    for f in range(1, END + 1, 6):                       # 4% push-in plus handheld drift (about 0.3 deg)
        cam.location = base + fwd * (dist * 0.04 * (f - 1) / (END - 1))
        cam.rotation_euler = (rot0.x + math.radians(rnd.uniform(-0.3, 0.3)), rot0.y + math.radians(rnd.uniform(-0.12, 0.12)),
                              rot0.z + math.radians(rnd.uniform(-0.3, 0.3)))
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    foc = bpy.data.objects.new("Focus", None); s.collection.objects.link(foc)
    foc.parent = a; foc.parent_type = "BONE"; foc.parent_bone = "Head"
    cam.data.dof.use_dof = True; cam.data.dof.focus_object = foc; cam.data.dof.aperture_fstop = 2.8

    # ---- set: one dark concrete wall behind him, far enough to blur
    wall = k.plane("Wall", (9, 6), (0, -2.6, H.z), k.pbr("concrete_layers_02", scale=0.6, tint=(0.3, 0.31, 0.33)), rot=(90, 0, 0))
    n = wall.matrix_world.to_3x3() @ Vector((0, 0, 1))
    if n.y < 0:
        wall.rotation_euler.z = math.pi
    # ---- light: warm soft key upper left of camera, cool rim behind right, low fill, a weak pool on the wall
    scr_left = fwd.cross(Vector((0, 0, 1))).normalized() * -1
    k.area("Key", H - fwd * 1.5 + scr_left * 1.3 + Vector((0, 0, 0.9)), H, 70, size=0.7, color=(1.0, 0.8, 0.58), spread=80)
    k.area("Rim", H + fwd * 1.5 - scr_left * 0.9 + Vector((0, 0, 0.6)), H, 520, size=0.5, color=(0.45, 0.72, 1.0))
    k.area("Fill", H - fwd * 1.6 - scr_left * 1.4 + Vector((0, 0, -0.1)), H, 2.5, size=1.6, color=(0.6, 0.75, 1.0))
    k.area("WallPool", Vector((H.x, -1.4, H.z + 1.4)) - scr_left * 1.2, Vector((H.x, -2.6, H.z + 0.2)) - scr_left * 0.8, 34, size=0.8, color=(1.0, 0.8, 0.6), spread=80)
    k.world(color=(0.012, 0.016, 0.022), strength=1.0)
    s.render.engine = "BLENDER_EEVEE"; s.eevee.taa_render_samples = 48; s.eevee.use_raytracing = True
    s.render.use_motion_blur = True; s.render.motion_blur_shutter = 0.5
    s.view_settings.view_transform = "AgX"; s.view_settings.look = "AgX - Punchy"
    print("HEAD", tuple(round(v, 2) for v in H), "CAMDIST", round(dist, 2), "STRAY", [o.name for o in bpy.data.objects if o.type == "MESH" and o.parent is None])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "scene.blend"))


def render(frames, pct):
    s = bpy.context.scene; s.render.resolution_percentage = pct; s.render.image_settings.file_format = "PNG"
    s.frame_set(1); s.render.filepath = os.path.join(OUT, "_throwaway.png"); bpy.ops.render.render(write_still=True)
    for f in frames:
        s.frame_set(f); s.render.filepath = os.path.join(OUT, "frames" if len(frames) > 20 else "stills", f"f_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
    print("RENDERED", len(frames))


if MODE == "build":
    build()
elif MODE == "stills":
    render([int(v) for v in argv[1].split(",")], 50)
elif MODE == "frames":
    render(list(range(1, END + 1)), 50)
