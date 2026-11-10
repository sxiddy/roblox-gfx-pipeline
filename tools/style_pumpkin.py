"""Pumpkin patch at the gravestone: she sits on stone steps hugging a glowing jack-o'-lantern, big blue moon, orange vs blue light.
Run after build_exact_gfx.py via run_halloween.py."""
import math, random, sys
import bpy
from mathutils import Vector

sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import importlib, gfx_kit as k, halloween_kit as h
importlib.reload(k); importlib.reload(h)

scene = bpy.context.scene
OUT = globals().get("OUT", r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\gfx_output\sttvr_l1ght\pumpkin")
PCT = globals().get("PCT", 50); SAMPLES = globals().get("SAMPLES", 64)
rnd = random.Random(11)
h.keep_only_avatar()
scene.render.resolution_x = scene.render.resolution_y = 1080
if not scene.camera:
    cd = bpy.data.cameras.new("Cam"); co = bpy.data.objects.new("Cam", cd); scene.collection.objects.link(co); scene.camera = co

# ---- pose plan: seated on the top step, leaning back on the gravestone, hugging a pumpkin, head tilted down at it
A = k.aim; k.reset_pose()
A("LowerTorso", (0, -0.1, 1)); A("UpperTorso", (0.02, -0.08, 1))
A("Head", (0.18, 0.2, 0.96), (0.1, 1, 0))
A("UpperLeg.P", (0.14, 1, 0.06)); A("LowerLeg.P", (0.04, 0.1, -1))
A("UpperLeg.N", (-0.08, 1, 0.02)); A("LowerLeg.N", (-0.1, 0.18, -1))
A("UpperArm.P", (0.45, 0.25, -0.85)); A("LowerArm.P", (-0.55, 0.8, 0.12)); A("Hand.P", (-0.7, 0.55, 0.0), (0, 0, 1))
A("UpperArm.N", (-0.45, 0.25, -0.85)); A("LowerArm.N", (0.55, 0.8, 0.12)); A("Hand.N", (0.7, 0.55, 0.0), (0, 0, 1))
k.upd()
STEP = 0.36
hip = k.arm().matrix_world @ k.arm().pose.bones["LowerTorso"].head
k.arm().location.z += (STEP + 0.07) - hip.z; k.upd()
hipz = (k.arm().matrix_world @ k.arm().pose.bones["LowerTorso"].head).z

# ---- materials
stone = k.pbr("gravel_embedded_concrete", 1.1, tint=(0.45, 0.45, 0.58))
ground = k.pbr("brown_mud_leaves_01", 0.5, tint=(0.4, 0.34, 0.45))
darkstone = k.material("Dark", (0.05, 0.05, 0.07), 0.9)
iron = k.material("Iron", (0.02, 0.02, 0.03), 0.6)
bark = k.material("Bark", (0.02, 0.02, 0.03), 0.95)

# ---- set
bpy.ops.mesh.primitive_plane_add(size=80); g = bpy.context.active_object; g.name = "Ground"; g.data.materials.append(ground)
h.solid("StepTop", "cube", (0.2, -0.1, STEP / 2), (1.8, 0.5, STEP / 2), stone, bevel=0.015)
h.solid("StepLow", "cube", (0.2, 0.75, 0.09), (1.8, 0.35, 0.09), stone, bevel=0.015)
h.solid("GraveBig", "cube", (-0.1, -0.75, 1.25), (0.75, 0.16, 1.25), stone, bevel=0.04)
h.solid("GraveL", "cube", (-1.7, 0.2, 0.45), (0.3, 0.09, 0.45), stone, rot=(0.05, 0.1, 0.35), bevel=0.03)
h.solid("GraveR", "cube", (1.9, -1.3, 0.8), (0.4, 0.1, 0.8), stone, rot=(0, 0.08, -0.3), bevel=0.03)
for i in range(14):
    x = rnd.uniform(-9, 9); y = rnd.uniform(-10, -3.2); hh = rnd.uniform(0.5, 1.3)
    h.solid("Grave", "cube", (x, y, hh / 2), (rnd.uniform(0.25, 0.45), 0.1, hh / 2), darkstone, rot=(0, rnd.uniform(-.1, .1), rnd.uniform(-.4, .4)), bevel=0.03)
for i in range(26):  # iron fence
    x = -8 + i * 0.7
    h.solid("Fence", "cylinder", (x, -3.0, 0.7), (0.025, 0.025, 0.7), iron)
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.04, radius2=0.0, depth=0.15, location=(x, -3.0, 1.45)); c = bpy.context.active_object; c.name = "Fence"; c.data.materials.append(iron)
h.solid("FenceBar", "cube", (0, -3.0, 1.0), (9.5, 0.02, 0.025), iron); h.solid("FenceBar", "cube", (0, -3.0, 0.4), (9.5, 0.02, 0.025), iron)
for i in range(9):
    h.bare_tree(rnd.uniform(-9, 9), rnd.uniform(-8, -4.5), rnd.uniform(5, 8), rnd.uniform(0.12, 0.22), bark, rnd)
h.stars()

# ---- pumpkins (face +Y toward the camera side)
big = h.pumpkin("PumpkinBig", (0.0, 0.33, hipz + 0.27), 0.24, rot_z=0, light=45)
h.pumpkin("PumpkinR", (-1.0, 0.45, STEP + 0.16), 0.17, rot_z=25, light=80)
h.pumpkin("PumpkinR4", (-1.5, 0.15, STEP + 0.12), 0.12, rot_z=35, light=70)
h.pumpkin("PumpkinR5", (-0.75, 0.0, STEP + 0.1), 0.1, rot_z=-10, light=60)
h.pumpkin("PumpkinR6", (-1.15, 0.8, 0.18 + 0.2), 0.2, rot_z=20, light=90)
h.pumpkin("PumpkinR2", (-1.7, 0.75, 0.18 + 0.14), 0.14, rot_z=-15, light=60)
h.pumpkin("PumpkinR3", (-0.5, 0.85, 0.18 + 0.11), 0.11, rot_z=20, light=50)
h.pumpkin("PumpkinL", (0.95, 0.55, STEP + 0.13), 0.13, rot_z=25, light=50, glow=(0.8, 0.3, 0.9), skin=(0.75, 0.2, 0.05))
h.pumpkin("PumpkinFar", (-1.5, 1.6, 0.14), 0.15, rot_z=30, light=60)

# ---- camera, atmosphere
k.world((0.008, 0.016, 0.045), strength=0.22)
H = k.head_center()
res = k.frame_head(head_frac=0.19, head_xy=(0.21, 0.52), view_dir=(0.1, 1, 0.14), lens=36); print("frame", res)
scene.camera.data.clip_end = 300
cam = scene.camera; q = cam.matrix_world.to_quaternion(); mp = cam.location + (q @ Vector((0, 0, -1))) * 25
mo = h.moon(mp, 2.5)
for _ in range(6):
    fx, fy, _d = k.project(mo.location)
    q = cam.matrix_world.to_quaternion()
    mo.location += (q @ Vector((1, 0, 0))) * (0.8 - fx) * 20 + (q @ Vector((0, 1, 0))) * (0.2 - fy) * -20
print("moon at", k.project(mo.location))
h.fog("Fog_air", (0, -6, 4), (40, 40, 8), 0.004, color=(0.5, 0.6, 0.9), aniso=0.3)
h.fog("Mist_low", (0, 0, 0.25), (40, 30, 0.9), 0.5, color=(0.55, 0.6, 0.8), noise=2.4, fade_height=True)
h.embers(18, (0.6, 0.8, 0.8), (1.5, 0.8, 0.8), size=(0.004, 0.009), strength=25)

for o in [o for o in scene.objects if o.type == "LIGHT" and not o.name.startswith("Pumpkin")]:
    bpy.data.objects.remove(o, do_unlink=True)
k.area("MoonRim", H + Vector((-3.5, -6.0, 3.8)), H, 1200, 5, (0.55, 0.72, 1.0), 120)
k.area("MoonRim2", H + Vector((4.0, -4.0, 2.0)), H, 180, 4, (0.6, 0.65, 1.0), 120)
k.area("VioletFill", H + Vector((-2.2, 3.2, 1.2)), H, 30, 3.5, (0.55, 0.45, 1.0), 150)

k.setup_cycles(SAMPLES, look="None", exposure=0.0, dof_fstop=2.4)
scene.cycles.volume_bounces = 1
bpy.ops.wm.save_as_mainfile(filepath=OUT + "_scene.blend", copy=True)
k.render(OUT + ".png", PCT, SAMPLES); print("RENDERED", OUT + ".png")
