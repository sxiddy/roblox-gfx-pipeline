"""Scene 1, Spectral Violet Graveyard (docs/GFX_MASTER_PIPELINE.md): seated on a double-stepped tomb, carved pumpkin in
her lap below the chin, step pumpkins image-left, violet mist + rim, cold moon, gnarled trees. Run via run_halloween.py."""
import math, random, sys
import bpy
from mathutils import Vector

sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import importlib, gfx_kit as k, halloween_kit as h, halloween_v2 as v2
importlib.reload(k); importlib.reload(h); importlib.reload(v2)

scene = bpy.context.scene
OUT = globals().get("OUT"); PCT = globals().get("PCT", 50); SAMPLES = globals().get("SAMPLES", 64)
rnd = random.Random(31)
h.keep_only_avatar(); v2.avatar_materials()
scene.render.resolution_x = scene.render.resolution_y = 1080

# ---- pose: S-curve spine, head tilt ~8 deg, seated, hands on the pumpkin sides
A = k.aim; k.reset_pose()
A("LowerTorso", (0, -0.08, 1)); A("UpperTorso", (0.05, 0.06, 1))
A("Head", (0.14, 0.07, 0.99), (0.05, 1, 0))
A("UpperLeg.P", (0.14, 1, 0.04)); A("LowerLeg.P", (0.05, 0.12, -1))
A("UpperLeg.N", (-0.1, 1, 0.0)); A("LowerLeg.N", (-0.08, 0.2, -1))
A("UpperArm.P", (0.35, 0.3, -0.89)); A("LowerArm.P", (-0.3, 0.95, -0.02)); A("Hand.P", (-0.45, 0.85, -0.2), (0, 0, 1))
A("UpperArm.N", (-0.35, 0.3, -0.89)); A("LowerArm.N", (0.3, 0.95, -0.02)); A("Hand.N", (0.45, 0.85, -0.2), (0, 0, 1))
k.upd()
STEP, LOW = 0.32, 0.16
hip = k.arm().matrix_world @ k.arm().pose.bones["LowerTorso"].head
k.arm().location.z += (STEP + 0.07) - hip.z; k.upd()
hipz = (k.arm().matrix_world @ k.arm().pose.bones["LowerTorso"].head).z

# ---- set
stone = v2.stone_mat(); dark = v2.stone_mat(tint=(0.25, 0.25, 0.32)); bark = v2.bark_mat()
iron = k.material("Iron", (0.02, 0.02, 0.03), 0.55, metal=0.8)
v2.ground(tint=(0.32, 0.27, 0.38))
h.solid("StepTop", "cube", (0.15, -0.15, STEP / 2), (1.6, 0.55, STEP / 2), stone, bevel=0.02)
h.solid("StepLow", "cube", (0.15, 0.62, LOW / 2), (1.6, 0.3, LOW / 2), stone, bevel=0.02)
v2.tombstone("TombBack", (-0.05, -0.5, STEP + 0.03), w=0.5, h=0.62, d=0.12, style="round", tilt=(-4, 2), mat=stone)
for i, (x, y) in enumerate([(1.6, -1.6), (-1.7, -2.2), (2.6, -3.4), (-2.9, -3.8), (0.6, -4.6), (-1.0, -6.0), (3.4, -6.5)]):
    v2.tombstone("Tomb%d" % i, (x, y, 0), w=rnd.uniform(0.38, 0.6), h=rnd.uniform(0.6, 1.1), style=rnd.choice(["round", "point"]),
                 tilt=(rnd.uniform(-7, 7), rnd.uniform(-6, 6)), rot_z=rnd.uniform(-20, 20), mat=dark)
for i in range(22):
    x = -7 + i * 0.65
    h.solid("Fence", "cylinder", (x, -3.0, 0.65), (0.02, 0.02, 0.65), iron)
h.solid("FenceBar", "cube", (0, -3.0, 1.05), (7.5, 0.015, 0.02), iron); h.solid("FenceBar", "cube", (0, -3.0, 0.35), (7.5, 0.015, 0.02), iron)
for i, (x, y) in enumerate([(-2.2, -4.5), (-4.5, -6.5), (-1.0, -8.5), (-6.5, -9), (-3.5, -11), (1.0, -10.5)]):
    v2.gnarled_tree((x, y, 0), rnd.uniform(3.5, 5.5), 100 + i, bark)

# ---- carved pumpkins (face +Y; camera sits at -X so turn them +rot_z)
v2.carved_pumpkin("PumpkinLap", (0.0, 0.24, hipz + 0.1), 0.14, rot_z=8, light=35)
v2.carved_pumpkin("PumpkinStep1", (0.62, 0.05, STEP + 0.12 * 0.82), 0.12, rot_z=25, light=5)
v2.carved_pumpkin("PumpkinStep2", (0.95, 0.62, LOW + 0.13 * 0.82), 0.13, rot_z=30, light=6)
v2.carved_pumpkin("PumpkinStep3", (0.42, 0.7, LOW + 0.085 * 0.82), 0.085, rot_z=15, light=3)
v2.carved_pumpkin("PumpkinGround", (1.4, 1.15, 0.14 * 0.82), 0.14, rot_z=35, light=6)

# ---- camera: subject right third, 75 mm
res = k.frame_head(head_frac=0.3, head_xy=(0.6, 0.38), view_dir=(-0.35, 1, 0.04), lens=75); print("frame", res)
cam = scene.camera; cam.data.clip_end = 300
mo = h.moon(cam.location + (cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))) * 40, 2.6)
for _ in range(6):
    fx, fy, _d = k.project(mo.location); q = cam.matrix_world.to_quaternion()
    mo.location += (q @ Vector((1, 0, 0))) * (0.22 - fx) * 30 + (q @ Vector((0, 1, 0))) * (fy - 0.11) * 30
print("moon", k.project(mo.location))

# ---- atmosphere (indigo world, violet height-faded mist) and wisps
k.world((0.004, 0.009, 0.022), strength=1.0)
h.fog("Mist", (0, -4, 4.0), (30, 24, 8.5), 0.04, color=(0.45, 0.56, 0.78), aniso=0.6, noise=1.6, fade_height=True)
v2.wisps(7, (0, -3.5, 1.2), (3.5, 2, 0.8))

# ---- lights: pumpkin interiors (in carved_pumpkin), violet rim rear-left, cold moon sun
for o in [o for o in scene.objects if o.type == "LIGHT" and not o.name.startswith("Pumpkin")]:
    bpy.data.objects.remove(o, do_unlink=True)
H = k.head_center()
rim = H + Vector((0.9, -1.5, 1.2)); k.area("MoonRim", rim, H, 45 * (rim - H).length_squared, 0.8, (0.5, 0.7, 1.0), 90)
sd = bpy.data.lights.new("Moon", "SUN"); sd.energy = 1.4; sd.color = (0.23, 0.42, 0.62); sd.angle = math.radians(0.5)
so = bpy.data.objects.new("MoonSun", sd); scene.collection.objects.link(so)
so.rotation_euler = (mo.location - H).normalized().to_track_quat("Z", "Y").to_euler()

pk = bpy.data.objects["PumpkinLap_root"].location
g = pk + (cam.location - pk).normalized() * 0.25 + Vector((0, 0, -0.05))
k.area("PumpkinGlow", g, H, 6 * (g - H).length_squared / 0.09, 0.25, (1.0, 0.5, 0.1), 120)
v2.lint()
k.setup_cycles(SAMPLES, look="AgX - Punchy", exposure=0.0, dof_fstop=3.2)
scene.cycles.volume_bounces = 1
bpy.ops.wm.save_as_mainfile(filepath=OUT + "_scene.blend", copy=True)
k.render(OUT + ".png", PCT, SAMPLES); print("RENDERED", OUT + ".png")
