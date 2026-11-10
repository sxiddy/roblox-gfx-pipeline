"""Late-night gamer corner GFX for Suhaa_Official (idea from the owner's gamer-chair reference, own unique set).
REFERENCE READ: dim bedroom, big chair in the left foreground, avatar seated 3/4 and leaning back with one hand on a glowing keyboard,
face lit by a large monitor on the right, warm sepia grade, props around the desk, camera slightly high from her front side.
MINE: black chair with hot-pink trim, ultrawide monitor showing the owner's REAL Discord view (her #suhie channel with the train GFX
post), orange 'flame' neon on the wall (server logo idea), pink/orange LED desk edge, plush, mug, candle, floating embers.
POSE PLAN: sits in the chair, torso leaning back a little, head turned ~50 deg toward the monitor (screen-right = world -X), left arm
(.N) reaching the keyboard, right arm (.P) resting on the armrest. CAMERA: from front-left, slightly above eye level, 40mm,
head_frac ~0.2, head left-of-centre, monitor right. GRADE: warm amber highlights, blue shadows, vignette, grain, soft bloom."""
import sys, importlib, math, random
sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import bpy
from mathutils import Vector, Matrix
import gfx_kit as k; importlib.reload(k)
ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
OUT = ROOT + r"\gfx_output\Suhaa_Official"
PREFIX = ("Gm",)


def stage_pose():
    k.apply_pose("sit")
    k.aim("LowerTorso", (0, -0.05, 1)); k.aim("UpperTorso", (0.08, -0.05, 1), (0.35, 1, 0))
    k.aim("Head", (0.05, 0.1, 0.99), (0.85, 0.5, 0.0))
    for sfx, sx in ((".P", 1), (".N", -1)):
        k.aim("UpperLeg" + sfx, (0.1 * sx, 1, 0.0)); k.aim("LowerLeg" + sfx, (0.0, 0.08, -1)); k.aim("Foot" + sfx, (0, 1, -0.2), (0, 0, 1))
    k.aim("UpperArm.N", (0.45, 0.3, -0.8)); k.aim("LowerArm.N", (0.5, 0.8, -0.15)); k.aim("Hand.N", (0.5, 0.8, -0.15), (0, 0, 1))
    k.aim("UpperArm.P", (0.55, 0.35, -0.75)); k.aim("LowerArm.P", (0.57, 0.82, -0.03)); k.aim("Hand.P", (0.57, 0.82, -0.05), (0, 0, 1))
    k.upd()


def stage_camera(head_frac=0.135, head_xy=(0.72, 0.5), view_dir=(0.3, 1, 0.22), lens=30, roll=2):
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    if not sc.camera:
        cd = bpy.data.cameras.new("Cam"); co = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(co); sc.camera = co
    print(k.frame_head(head_frac, head_xy=head_xy, view_dir=view_dir, lens=lens, roll=roll)); k.show_camera()


def low(parts):
    return min((o.matrix_world @ Vector(c)).z for o in k.arm().children if o.name.split(".")[0] in parts for c in o.bound_box)


def _glow_img(name, path, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(t.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = strength
    b.inputs["Base Color"].default_value = (0, 0, 0, 1); return m


def stage_set():
    for o in [o for o in bpy.data.objects if o.name.startswith(PREFIX)]:
        bpy.data.objects.remove(o, do_unlink=True)
    a = k.arm(); a.location = (0.0, -0.1, 0.0); k.upd()
    a.location.z = -low(("Foot_P", "Foot_N")) + 0.002; k.upd()
    seat = low(("LowerTorso", "UpperLeg_P", "UpperLeg_N")) - 0.003
    print("seat top", round(seat, 3))

    def cube(n, sz, loc, mat, rot=(0, 0, 0)):
        o = k.cube("Gm" + n, sz, loc, mat); o.rotation_euler = tuple(math.radians(r) for r in rot); return o
    black = k.material("GmBlack", (0.02, 0.018, 0.025), 0.5)
    pink = k.material("GmPink", (0.95, 0.25, 0.55), 0.45)
    desk = k.material("GmDesk", (0.10, 0.09, 0.12), 0.18)
    k.plane("GmWall", (12, 5), (0, -1.7, 2.2), k.material("GmWallM", (0.04, 0.03, 0.05), 0.9), rot=(90, 0, 0))
    k.plane("GmFloor", (12, 10), (0, 0, 0), k.material("GmFloorM", (0.03, 0.028, 0.036), 0.5))
    bpy.ops.mesh.primitive_cylinder_add(radius=1.6, depth=0.01, location=(0, 0.1, 0.006), vertices=64)
    r_ = bpy.context.active_object; r_.name = "GmRug"; r_.data.materials.append(k.material("GmRugM", (0.07, 0.05, 0.09), 0.95))
    # chair: black seat/back, pink trim, headrest and armrest pads, post + five-star base
    cube("ChairSeat", (0.8, 0.75, 0.1), (0, -0.1, seat - 0.05), black)
    cube("ChairBack", (0.78, 0.12, 1.3), (0, -0.55, seat + 0.57), black, (-6, 0, 0))
    cube("ChairTrimL", (0.06, 0.13, 1.3), (0.37, -0.55, seat + 0.57), pink, (-6, 0, 0)); cube("ChairTrimR", (0.06, 0.13, 1.3), (-0.37, -0.55, seat + 0.57), pink, (-6, 0, 0))
    cube("Headrest", (0.4, 0.14, 0.22), (0, -0.49, seat + 0.98), black, (-6, 0, 0)); cube("HeadrestTrim", (0.42, 0.05, 0.025), (0, -0.43, seat + 1.1), pink, (-6, 0, 0))
    for sx in (-0.5,):
        cube("Arm%d" % sx, (0.12, 0.55, 0.07), (sx, -0.1, seat + 0.28), pink); cube("ArmPost%d" % sx, (0.05, 0.05, 0.28), (sx, -0.25, seat + 0.14), black)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=seat - 0.1, location=(0, -0.15, (seat - 0.1) / 2 + 0.06), vertices=16)
    bpy.context.active_object.name = "GmPost"; bpy.context.active_object.data.materials.append(black)
    for i in range(5):
        ang = i * 72
        c_ = cube("Star%d" % i, (0.55, 0.06, 0.04), (math.cos(math.radians(ang)) * 0.27, -0.15 + math.sin(math.radians(ang)) * 0.27, 0.07), black, (0, 0, ang))
    # desk (to her right, world -X) with LED edge, ultrawide monitor showing the real Discord view, glowing keyboard, props
    cube("DeskTop", (2.6, 1.4, 0.05), (1.5, -0.2, 0.62), desk)
    cube("DeskPanel", (0.05, 1.3, 0.6), (2.75, -0.2, 0.3), black); cube("DeskPanel2", (0.05, 1.3, 0.6), (0.3, -0.2, 0.3), black)
    k.led_strip([(0.22, 0.5, 0.6), (0.22, -0.9, 0.6)], (1.0, 0.25, 0.5), 20, 0.012).name = "GmLEDa"
    k.led_strip([(0.22, 0.5, 0.6), (2.8, 0.5, 0.6)], (1.0, 0.45, 0.1), 18, 0.012).name = "GmLEDb"
    ang = 37
    cube("MonBez", (1.48, 0.04, 0.87), (1.1, 0.1, 1.25), black, (0, 0, ang - 180))
    n = Vector((-math.sin(math.radians(ang - 180 + 180)), math.cos(math.radians(ang - 180 + 180)), 0))
    k.plane("GmMon", (1.4, 0.7875), (1.1 - 0.6 * 0.03, 0.1 + 0.8 * 0.03, 1.25), _glow_img("GmMonM", OUT + r"\gm_screen_footage.png", 2.4), rot=(90, 0, ang + 180))
    cube("MonStand", (0.1, 0.1, 0.5), (2.0, -0.6, 0.85), black)
    kb = cube("Keyboard", (0.5, 0.17, 0.025), (0.5, 0.19, 0.655), black, (0, 0, -18))
    kg = k.plane("GmKeys", (0.46, 0.14), (0.5, 0.19, 0.669), k.material("GmKeysM", (0, 0, 0), 0.5, emit=(0.9, 0.35, 0.6), strength=0.5), rot=(0, 0, -18))
    cube("DeskMat", (0.75, 0.34, 0.004), (0.6, 0.25, 0.649), k.material("GmMatM", (0.05, 0.02, 0.05), 0.6), (0, 0, -12))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(0.95, 0.38, 0.675), segments=24, ring_count=12)
    ms = bpy.context.active_object; ms.name = "GmMouse"; ms.scale = (0.7, 1.2, 0.45); ms.rotation_euler[2] = math.radians(-10); ms.data.materials.append(k.material("GmMouseM", (0.03, 0.03, 0.04), 0.25, emit=(0.9, 0.3, 0.6), strength=0.4)); bpy.ops.object.shade_smooth()
    # props: mug with steam-less glow, candle, plush, speaker
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.11, location=(2.7, 0.2, 0.69), vertices=24)
    bpy.context.active_object.name = "GmMug"; bpy.context.active_object.data.materials.append(k.material("GmMugM", (0.9, 0.4, 0.15), 0.3))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.09, location=(2.55, -0.4, 0.69), vertices=24)
    bpy.context.active_object.name = "GmCandle"; bpy.context.active_object.data.materials.append(k.material("GmCandleM", (0.95, 0.9, 0.8), 0.6))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=(2.55, -0.4, 0.755), segments=16, ring_count=8)
    fl = bpy.context.active_object; fl.name = "GmFlame"; fl.scale = (1, 1, 1.8); fl.data.materials.append(k.material("GmFlameM", (1, 0.6, 0.2), 0.5, emit=(1.0, 0.55, 0.15), strength=30))
    for i, (x, y, r, col) in enumerate(((3.0, -0.6, 0.12, (0.95, 0.6, 0.75)), (2.95, -0.45, 0.07, (0.2, 0.2, 0.28)))):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(x, y, 0.645 + r * 0.9), segments=32, ring_count=16)
        o = bpy.context.active_object; o.name = "GmPlush%d" % i; o.data.materials.append(k.material("GmPlushM%d" % i, col, 0.95)); bpy.ops.object.shade_smooth()
    # flame neon on the wall behind the chair (server logo idea): orange outline + blue/yellow inner stroke
    pts = []
    for i in range(0, 101):
        t = i / 100
        x = 0.45 * math.sin(math.pi * t) ** 1.2 * (1 - 0.35 * t) * (1 if t < 0.5 else 1)
        z = 1.6 * t
        pts.append((x, z))
    right = [(-1.7 + x * 0.9, -1.66, 1.3 + z) for x, z in pts]; left = [(-1.7 - x * 0.9 * 0.85, -1.66, 1.3 + z) for x, z in reversed(pts)]
    k.led_strip(right + left, (1.0, 0.4, 0.08), 26, 0.016).name = "GmFlameOut"
    inner = [(-1.7 + x * 0.45, -1.655, 1.3 + z * 0.62) for x, z in pts]; inner += [(-1.7 - x * 0.4, -1.655, 1.3 + z * 0.62) for x, z in reversed(pts)]
    k.led_strip(inner, (0.15, 0.4, 1.0), 14, 0.011).name = "GmFlameIn"
    k.bokeh_lights(Vector((-0.4, -1.1, 1.5)), count=40, spread=(2.4, 0.5, 1.2), colors=((1.0, 0.5, 0.12), (1.0, 0.75, 0.3)), strength=9, seed=9)
    for o in [o for o in bpy.data.objects if o.name.startswith("Bokeh")]: o.name = "Gm" + o.name
    k.show_camera()


def stage_light():
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)
    H = k.head_center()
    k.area("MonitorGlow", Vector((1.2, 0.6, 1.2)), H, 40, 1.6, (0.78, 0.86, 1.0), 120)
    k.area("FlameRim", Vector((-1.7, -1.4, 2.0)), H, 120, 0.9, (1.0, 0.5, 0.15), 100)
    k.area("KeyGlow", Vector((1.0, 0.35, 0.8)), H, 5, 0.5, (1.0, 0.65, 0.85), 130)
    k.area("CandleWarm", Vector((2.4, -0.3, 0.85)), H, 4, 0.3, (1.0, 0.6, 0.25), 150)
    k.area("Fill", H + Vector((-2.0, 2.0, 0.4)), H, 8, 2.0, (0.5, 0.55, 0.9), 150)
    k.world((0.03, 0.035, 0.07), 0.15, haze=0.0012)
    k.setup_cycles(64, look="AgX - Punchy", exposure=0.1, dof_fstop=2.4)
    bpy.context.scene.camera.data.dof.focus_distance = (H - bpy.context.scene.camera.location).length
    k.show_camera()
