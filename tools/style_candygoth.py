"""Candy Goth Room GFX for Suhaa_Official (new avatar). Stage functions run in Blender via bl.py.
POSE PLAN: seated on a black bed hugging her knees (thighs forward+up, shins tucked back+down), both forearms wrapped
across the shins, torso leaning slightly forward, head tilted ~12 deg toward the camera with the tongue-out smirk.
CAMERA: tripod, 3/4 from her front-left, eye level of the head, 70mm, head_frac ~0.30, head upper-right third, roll 3.
SET: dark room, pink neon heart + violet frame on the back wall, fairy-light bokeh, black/pink plush pile.
LIGHT: soft white key from camera side, hot pink rim from behind-left, violet fill, neon practicals; crushed blacks."""
import sys, importlib, math
sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import bpy
from mathutils import Vector
import gfx_kit as k; importlib.reload(k)
ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
OUT = ROOT + r"\gfx_output\Suhaa_Official"


def stage_pose():
    k.apply_pose("sit")
    k.aim("LowerTorso", (0, 0.15, 1)); k.aim("UpperTorso", (0.04, 0.25, 0.97), (0.2, 1, 0))
    k.aim("Head", (0.2, 0.1, 0.97), (0.3, 1, 0.2))
    for s, sx in ((".P", 1), (".N", -1)):
        k.aim("UpperLeg" + s, (0.12 * sx, 0.8, 0.55)); k.aim("LowerLeg" + s, (0.0, -0.85, -0.52)); k.aim("Foot" + s, (0, 0.9, -0.2), (0, 0, 1))
        k.aim("UpperArm" + s, (0.2 * sx, 0.35, -0.9)); k.aim("LowerArm" + s, (-0.8 * sx, 0.5, 0.3)); k.aim("Hand" + s, (-0.9 * sx, 0.3, 0.1), (0, 0, 1))
    k.upd()


def stage_camera(head_frac=0.30, head_xy=(0.66, 0.36), view_dir=(0.45, 1, 0.0), lens=70, roll=3):
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    if not sc.camera:
        cd = bpy.data.cameras.new("Cam"); co = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(co); sc.camera = co
    print(k.frame_head(head_frac, head_xy=head_xy, view_dir=view_dir, lens=lens, roll=roll)); k.show_camera()


def low(parts):
    return min((o.matrix_world @ Vector(c)).z for o in k.arm().children if o.name.split(".")[0] in parts for c in o.bound_box)


def _sphere(name, r, loc, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=48, ring_count=24)
    o = bpy.context.active_object; o.name = name; o.scale = scale; o.data.materials.append(mat); bpy.ops.object.shade_smooth(); return o


def stage_set():
    for n in [o.name for o in bpy.data.objects if o.name.startswith(("Bed", "Wall", "Neon", "Plush", "Floor", "Pillow", "Blanket", "Bokeh", "LED", "Head_b"))]:
        bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    a = k.arm(); k.upd()
    pel = low(("LowerTorso",)); feet = low(("Foot_P", "Foot_N"))
    a.location.z += 0.40 - min(pel, feet) + 0.005; a.location.y = -0.55; k.upd()
    black = k.material("BedBlack", (0.025, 0.02, 0.03), 0.55)
    wallm = k.material("WallDark", (0.07, 0.04, 0.09), 0.85)
    pink = k.material("BlanketPink", (0.95, 0.5, 0.68), 0.9)
    k.plane("WallBack", (8, 4.5), (0, -1.4, 2.0), wallm, rot=(90, 0, 0))
    k.plane("Floor", (9, 9), (0, 0, 0), k.material("FloorDark", (0.05, 0.035, 0.06), 0.5))
    k.cube("BedBase", (2.6, 1.4, 0.38), (0, -0.7, 0.19), black)
    m = k.cube("BedMattress", (2.5, 1.3, 0.07), (0, -0.7, 0.415), black)
    bv = m.modifiers.new("b", "BEVEL"); bv.width = 0.03; bv.segments = 3; m.modifiers.new("s", "SUBSURF").levels = 2
    k.cube("BedHeadboard", (2.6, 0.12, 1.1), (0, -1.33, 0.75), black)
    b = k.cube("BlanketPink", (1.0, 1.2, 0.05), (-0.85, -0.65, 0.45), pink, rot_z=0)
    b.modifiers.new("s", "SUBSURF").levels = 2
    # plush pile + skull pillow-ish dark plushies
    for i, (x, y, col, r) in enumerate(((-0.95, -0.95, (0.95, 0.55, 0.72), 0.2), (-0.62, -1.0, (0.03, 0.03, 0.04), 0.16),
                                         (0.98, -0.9, (0.04, 0.03, 0.05), 0.2), (0.7, -1.05, (1.0, 0.75, 0.85), 0.14))):
        mat = k.material("PlushM%d" % i, col, 0.95)
        _sphere("Plush%d" % i, r, (x, y, 0.45 + r * 0.85), mat, (1.15, 0.95, 0.95))
        for ex in (-0.5, 0.5):
            _sphere("Plush%d_ear" % i, r * 0.35, (x + ex * r, y, 0.45 + r * 1.85), mat)
    # neon heart + violet frame on the wall
    pts = []
    for i in range(61):
        t = i / 60 * 2 * math.pi
        hx = 16 * math.sin(t) ** 3; hz = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((0.55 + hx * 0.028, -1.34, 2.2 + hz * 0.028))
    h = k.led_strip(pts, (1.0, 0.18, 0.55), 40, 0.014); h.name = "NeonHeart"
    f = k.led_strip([(-0.7, -1.34, 1.2), (-0.7, -1.34, 2.9), (1.9, -1.34, 2.9), (1.9, -1.34, 1.2), (-0.7, -1.34, 1.2)], (0.6, 0.25, 1.0), 25, 0.01); f.name = "NeonFrame"
    k.show_camera()


def stage_light():
    for o in [o for o in bpy.data.objects if o.type == "LIGHT" or o.name.startswith("Bokeh")]:
        bpy.data.objects.remove(o, do_unlink=True)
    H = k.head_center()
    k.area("Key", H + Vector((1.0, 1.7, 0.35)), H, 30, 1.6, (1.0, 0.93, 0.95), 150)
    k.area("PinkRim", H + Vector((-1.1, -0.9, 0.6)), H, 90, 0.7, (1.0, 0.25, 0.6), 100)
    k.area("VioletFill", H + Vector((1.8, -0.3, -0.2)), H, 25, 1.5, (0.55, 0.3, 1.0), 120)
    k.area("HeartGlow", Vector((0.55, -1.0, 2.2)), H, 55, 1.2, (1.0, 0.2, 0.55), 120)
    k.bokeh_lights(Vector((0.3, -1.3, 2.0)), count=55, spread=(1.8, 0.03, 0.9), colors=((1, 0.75, 0.5), (1, 0.5, 0.75), (0.7, 0.55, 1)), strength=14, seed=7)
    k.world((0.05, 0.03, 0.08), 0.15, haze=0.003)
    k.setup_cycles(64, look="AgX - Punchy", exposure=-0.2, dof_fstop=2.0)
    bpy.context.scene.camera.data.dof.focus_distance = (H - bpy.context.scene.camera.location).length
    k.show_camera()


def cleanup():
    for n in ("Halo", "Backdrop", "Handle3", "Handle2"):
        if n in bpy.data.objects: bpy.data.objects[n].hide_render = True; bpy.data.objects[n].hide_viewport = True
