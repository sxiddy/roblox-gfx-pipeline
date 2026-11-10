"""Autumn forest lantern: she holds a glowing lantern, golden backlight, falling leaves, warm bokeh, soft haze.
Run after build_exact_gfx.py via run_halloween.py."""
import math, random, sys
import bpy
from mathutils import Vector

sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import importlib, gfx_kit as k, halloween_kit as h
importlib.reload(k); importlib.reload(h)

scene = bpy.context.scene
OUT = globals().get("OUT", r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\gfx_output\sttvr_l1ght\lantern")
PCT = globals().get("PCT", 50); SAMPLES = globals().get("SAMPLES", 64)
rnd = random.Random(21)
h.keep_only_avatar()
scene.render.resolution_x = scene.render.resolution_y = 1080
if not scene.camera:
    cd = bpy.data.cameras.new("Cam"); co = bpy.data.objects.new("Cam", cd); scene.collection.objects.link(co); scene.camera = co

# ---- pose plan: standing, head tilted, lantern held out at her right side, other hand up near her chin
A = k.aim; k.reset_pose()
A("LowerTorso", (0.02, -0.04, 1)); A("UpperTorso", (-0.02, 0.0, 1))
A("Head", (-0.22, 0.12, 0.96), (0.1, 1, 0))
A("UpperArm.P", (0.5, 0.4, -0.78)); A("LowerArm.P", (0.15, 0.95, 0.2)); A("Hand.P", (0.1, 0.9, -0.1), (0, 0, 1))
A("UpperArm.N", (-0.15, 0.25, -0.95)); A("LowerArm.N", (0.5, 0.55, 0.35)); A("Hand.N", (0.6, 0.5, 0.2), (0, 0, 1))
A("UpperLeg.P", (0.05, 0, -1)); A("UpperLeg.N", (-0.05, 0.03, -1))
k.upd()

# ---- materials
ground = k.pbr("brown_mud_leaves_01", 0.5, tint=(0.5, 0.26, 0.1))
bark = k.material("Bark", (0.06, 0.035, 0.02), 0.95)

# ---- set: forest floor, trunks fading into warm haze
bpy.ops.mesh.primitive_plane_add(size=80); g = bpy.context.active_object; g.name = "Ground"; g.data.materials.append(ground)
for i in range(30):
    d = rnd.uniform(2.5, 16); x = rnd.uniform(-0.55, 0.55) * (d + 1.5)
    if abs(x) < 0.5 and d < 6: x += math.copysign(0.9, x or 1)
    h.bare_tree(x, -d, rnd.uniform(6, 10), rnd.uniform(0.1, 0.26), bark, rnd)

# ---- lantern in her right hand
a = k.arm(); hand = a.matrix_world @ a.pose.bones["Hand.P"].tail
roots = k.import_model("props", "Lantern_01", loc=(0, 0, 0), scale=1.0)
bpy.context.view_layer.update()
meshes = [o for r in roots for o in [r] + list(r.children_recursive) if o.type == "MESH"]
zs = [(o.matrix_world @ Vector(c)).z for o in meshes for c in o.bound_box]
height = max(zs) - min(zs); sc = 0.36 / height
for r in roots:
    r.scale = (sc,) * 3
bpy.context.view_layer.update()
zs = [(o.matrix_world @ Vector(c)).z for o in meshes for c in o.bound_box]; top = max(zs)
for r in roots:
    r.location = hand - Vector((0, 0, top - r.location.z)) + Vector((0, 0.02, 0.03))
lamp_pos = hand + Vector((0, 0.0, -0.16))
for m in meshes:  # make glass/flame parts glow
    for slot in m.material_slots:
        mt = slot.material
        if mt and mt.use_nodes:
            b = mt.node_tree.nodes.get("Principled BSDF")
            if b and any(t in mt.name.lower() for t in ("glass", "flame", "light", "bulb")):
                b.inputs["Emission Color"].default_value = (1, 0.55, 0.15, 1); b.inputs["Emission Strength"].default_value = 6
for m in meshes:  # any bright (white) lantern glass becomes a warm flame glow
    for slot in m.material_slots:
        mt = slot.material
        if mt and mt.use_nodes:
            bs = mt.node_tree.nodes.get("Principled BSDF")
            if bs:
                bc = bs.inputs["Base Color"].default_value; print("LANTERN MAT", mt.name, tuple(round(c, 2) for c in bc))
                if "brass" in mt.name.lower():
                    bs.inputs["Base Color"].default_value = (0.3, 0.17, 0.05, 1); bs.inputs["Metallic"].default_value = 0.9; bs.inputs["Roughness"].default_value = 0.45
                elif "glass" in mt.name.lower():
                    bs.inputs["Emission Color"].default_value = (1, 0.5, 0.1, 1); bs.inputs["Emission Strength"].default_value = 2.5
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=lamp_pos); fl = bpy.context.active_object; fl.name = "Flame"; fl.scale = (1, 1, 1.5)
fl.data.materials.append(h.emissive("FlameM", (1, 0.4, 0.05), 18)); fl.visible_shadow = False
ld = bpy.data.lights.new("LampL", "POINT"); ld.energy = 320; ld.color = (1.0, 0.55, 0.18); ld.shadow_soft_size = 0.05
lo = bpy.data.objects.new("LampL", ld); scene.collection.objects.link(lo); lo.location = lamp_pos

# ---- camera + atmosphere
k.world((0.09, 0.04, 0.015), strength=0.8)
H = k.head_center()
res = k.frame_head(head_frac=0.3, head_xy=(0.5, 0.33), view_dir=(0.1, 1, 0.04), lens=50); print("frame", res)
scene.camera.data.clip_end = 300
h.fog("Fog_air", (0, -6, 4), (40, 40, 8), 0.011, color=(1.0, 0.6, 0.3), aniso=0.5)
h.fog("Mist_low", (0, 0, 0.2), (40, 30, 0.7), 0.25, color=(1.0, 0.65, 0.35), noise=2.4, fade_height=True)
h.leaves(22, (0, -0.4, 1.1), (1.8, 0.7, 1.3), colors=((1, 0.42, 0.05), (0.95, 0.25, 0.02), (0.8, 0.35, 0.05)), strength=1.0, size=(0.015, 0.035))
h.leaves(25, (0, -6, 2), (6, 4, 3), seed=7, strength=3.0, size=(0.04, 0.08))
h.leaves(80, (0, 0.2, 0), (3, 2.5, 0), seed=3, strength=0.8, ground=0.01, size=(0.03, 0.08))
h.embers(140, (0, -9, 2.5), (8, 5, 3), seed=4, color=(1, 0.38, 0.04), size=(0.03, 0.08), strength=14)  # bokeh discs

for o in [o for o in scene.objects if o.type == "LIGHT" and o.name != "LampL"]:
    bpy.data.objects.remove(o, do_unlink=True)
k.area("SunBack", H + Vector((2.5, -6.0, 2.6)), H, 1400, 5, (1.0, 0.62, 0.28), 120)
k.area("WarmFill", H + Vector((-1.8, 3.0, 0.8)), H, 20, 3.5, (1.0, 0.7, 0.45), 150)

k.setup_cycles(SAMPLES, look="None", exposure=0.0, dof_fstop=1.8)
scene.cycles.volume_bounces = 1
bpy.ops.wm.save_as_mainfile(filepath=OUT + "_scene.blend", copy=True)
k.render(OUT + ".png", PCT, SAMPLES); print("RENDERED", OUT + ".png")
