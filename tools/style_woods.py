"""Scene 2, Eerie Autumn Woods (docs/GFX_MASTER_PIPELINE.md): lantern held out at shoulder height on the far arm, near
hand at the chest, violet-indigo mist, gnarled trees, maple leaf cards with hero leaves at the lens. Run via run_halloween.py."""
import math, random, sys
import bpy
from mathutils import Vector

sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import importlib, gfx_kit as k, halloween_kit as h, halloween_v2 as v2
importlib.reload(k); importlib.reload(h); importlib.reload(v2)

scene = bpy.context.scene
OUT = globals().get("OUT"); PCT = globals().get("PCT", 50); SAMPLES = globals().get("SAMPLES", 64)
rnd = random.Random(41)
h.keep_only_avatar(); v2.avatar_materials()
scene.render.resolution_x = scene.render.resolution_y = 1080

# ---- pose: camera on +X, so the far arm is .N (-X): lantern out at shoulder height; head tilts toward it
A = k.aim; k.reset_pose()
A("LowerTorso", (0.04, 0, 1), (-0.1, 1, 0)); A("UpperTorso", (-0.06, 0.04, 1))
A("Head", (-0.16, 0.08, 0.98), (-0.15, 1, 0))
A("UpperArm.N", (-0.8, 0.35, -0.12)); A("LowerArm.N", (-0.3, 0.85, 0.2)); A("Hand.N", (-0.25, 0.75, -0.3), (0, 0, 1))
A("UpperArm.P", (0.15, 0.15, -0.97)); A("LowerArm.P", (-0.45, 0.65, 0.5)); A("Hand.P", (-0.5, 0.6, 0.4), (0, 0, 1))
A("UpperLeg.P", (0.06, 0.05, -1)); A("UpperLeg.N", (-0.05, -0.04, -1))
k.upd()

# ---- lantern (library model) at the far hand: dark brass, glass <= 2.5 emission, flame sphere, point light
a = k.arm(); hand = a.matrix_world @ a.pose.bones["Hand.N"].tail
roots = k.import_model("props", "Lantern_01"); bpy.context.view_layer.update()
meshes = [o for r in roots for o in [r] + list(r.children_recursive) if o.type == "MESH"]
zs = [(o.matrix_world @ Vector(c)).z for o in meshes for c in o.bound_box]; sc = 0.32 / (max(zs) - min(zs))
for r in roots:
    r.scale = (sc,) * 3
bpy.context.view_layer.update()
top = max((o.matrix_world @ Vector(c)).z for o in meshes for c in o.bound_box)
for r in roots:
    r.location = hand - Vector((0, 0, top - r.location.z)) + Vector((0, 0, 0.02))
bpy.context.view_layer.update()
for m in meshes:
    for s in m.material_slots:
        b = s.material.node_tree.nodes.get("Principled BSDF") if s.material and s.material.use_nodes else None
        if not b:
            continue
        if "brass" in s.material.name.lower():
            b.inputs["Base Color"].default_value = (0.28, 0.16, 0.05, 1); b.inputs["Metallic"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.35
        elif "glass" in s.material.name.lower():
            b.inputs["Emission Color"].default_value = (1, 0.55, 0.15, 1); b.inputs["Emission Strength"].default_value = 1.5
            b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.15; s.material.blend_method = "BLEND" if hasattr(s.material, "blend_method") else None
            m.visible_shadow = False
lamp = hand + Vector((0, 0, -0.17))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=lamp); fl = bpy.context.active_object; fl.name = "LanternFlame"; fl.scale = (1, 1, 1.6)
fl.data.materials.append(h.emissive("FlameM", (1, 0.45, 0.08), 22)); fl.visible_shadow = False

# ---- set: displaced leaf-litter ground, gnarled trees, leaf cards
bark = v2.bark_mat()
v2.ground(tint=(0.5, 0.28, 0.12))
v2.leaf_cards(260, (0, -1.5, 0), (4.5, 4.5, 0), seed=3, size=(0.05, 0.1), ground=0.0)
for i in range(16):
    d = rnd.uniform(2.5, 14); x = rnd.uniform(-0.6, 0.6) * (d + 2)
    if abs(x) < 0.8 and d < 6: x += math.copysign(1.1, x or 1)
    v2.gnarled_tree((x, -d, 0), rnd.uniform(4.5, 7.5), 200 + i, bark)
v2.leaf_cards(45, (0, -0.8, 1.2), (2.2, 1.6, 1.1), seed=5, size=(0.05, 0.09))

# ---- camera: three-quarter, 85 mm
res = k.frame_head(head_frac=0.3, head_xy=(0.5, 0.36), view_dir=(0.5, 1, 0.22), lens=85); print("frame", res)
cam = scene.camera; cam.data.clip_end = 300
v2.hero_leaves(cam, n=4)

# ---- atmosphere: canopy indigo world, violet-indigo mist, warm distant bokeh
k.world((0.06, 0.03, 0.012), strength=0.35)
h.fog("Mist", (0, -5, 2.0), (30, 26, 4.5), 0.045, color=(1.0, 0.62, 0.32), aniso=0.6, noise=1.4, fade_height=True)
h.embers(70, (0, -9, 2.2), (7, 4, 2.2), seed=4, color=(1, 0.45, 0.08), size=(0.025, 0.06), strength=10)

# ---- lights: lantern key, warm bounce, violet rear rim, dim sky glow behind the trees
for o in [o for o in scene.objects if o.type == "LIGHT"]:
    bpy.data.objects.remove(o, do_unlink=True)
H = k.head_center()
ld = bpy.data.lights.new("LanternL", "POINT"); ld.energy = 320; ld.color = (1.0, 0.58, 0.15); ld.shadow_soft_size = 0.02
lo = bpy.data.objects.new("LanternL", ld); scene.collection.objects.link(lo); lo.location = lamp
b = H + Vector((0.8, 1.6, -0.5)); k.area("WarmBounce", b, H, 14 * (b - H).length_squared, 1.0, (1.0, 0.76, 0.48), 150)
r = H + Vector((-0.6, -1.8, 1.1)); k.area("GoldRim", r, H, 40 * (r - H).length_squared, 0.8, (1.0, 0.65, 0.3), 90)
k.area("SkyGlow", Vector((0, -16, 7)), Vector((0, 0, 1)), 1300, 10, (1.0, 0.55, 0.25), 120)

v2.lint()
k.setup_cycles(SAMPLES, look="AgX - Punchy", exposure=0.0, dof_fstop=3.2)
scene.cycles.volume_bounces = 1
bpy.ops.wm.save_as_mainfile(filepath=OUT + "_scene.blend", copy=True)
k.render(OUT + ".png", PCT, SAMPLES); print("RENDERED", OUT + ".png")
