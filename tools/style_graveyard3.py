"""Graveyard v3, rebuilt to match gfx_references/halloween/ref2_moon_graveyard.png:
chibi big in the left third leaning on a huge mossy tombstone, hand to cheek, huge jack-o'-lantern right of centre,
second pumpkin behind, blurred foreground pumpkins at the bottom, crypts/stones/branches, teal moon top-centre, cobbles.
Camera looks along -Y-ish; image-right = world -X. Run via run_halloween.py -- graveyard3 pct spp."""
import math, random, sys
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import importlib, gfx_kit as k, halloween_kit as h, halloween_v2 as v2
importlib.reload(k); importlib.reload(h); importlib.reload(v2)

scene = bpy.context.scene
OUT = globals().get("OUT"); PCT = globals().get("PCT", 50); SAMPLES = globals().get("SAMPLES", 64)
rnd = random.Random(7)
h.keep_only_avatar(); v2.avatar_materials()
scene.render.resolution_x, scene.render.resolution_y = 1080, 756   # ref 736x515 = 1.43

# ---- pose: seated on the tomb plinth, back leaning on the stone, head tilted toward the raised hand,
# N arm (her left = image-right) forearm up so the hand block rests at the cheek; P arm on the lap.
A = k.aim; k.reset_pose()
A("LowerTorso", (0.05, -0.1, 1)); A("UpperTorso", (0.07, -0.08, 1))
A("Head", (-0.1, 0.02, 1), (-0.15, 1, 0))
A("UpperLeg.P", (0.06, 0.12, -1)); A("LowerLeg.P", (0.03, -0.05, -1))
A("UpperLeg.N", (-0.08, 0.1, -1)); A("LowerLeg.N", (-0.04, -0.05, -1))
A("UpperArm.P", (0.25, 0.25, -0.93)); A("LowerArm.P", (-0.35, 0.85, -0.35)); A("Hand.P", (-0.4, 0.8, -0.35), (0, 0, 1))
k.upd()
Hc = k.head_center(); cheek = Hc + Vector((-0.16, 0.05, -0.16)); best = None
for ux in (-0.5, -0.35, -0.2, -0.05):
    for uy in (0.2, 0.45, 0.7):
        for lx in (-0.1, 0.05, 0.2, 0.35):
            for ly in (0.0, 0.2, 0.4):
                A("UpperArm.N", (ux, uy, -0.75)); A("LowerArm.N", (lx, ly, 1)); A("Hand.N", (lx, ly, 1), (0, 1, 0))
                t = k.arm().matrix_world @ k.arm().pose.bones["Hand.N"].tail
                e = (t - cheek).length
                if best is None or e < best[0]:
                    best = (e, (ux, uy, lx, ly))
ux, uy, lx, ly = best[1]; print("ARM solve", best)
A("UpperArm.N", (ux, uy, -0.75)); A("LowerArm.N", (lx, ly, 1)); A("Hand.N", (lx, ly, 1), (0, 1, 0))
k.upd()
foot = min((k.arm().matrix_world @ k.arm().pose.bones[b].tail).z for b in ("LowerLeg.P", "LowerLeg.N", "LowerLeg.P"))
low = min((o.matrix_world @ Vector(c)).z for o in k.arm().children_recursive if o.type == "MESH" for c in o.bound_box)
k.arm().location.z -= low; k.upd()
SEAT = 0.0
H = k.head_center()
hand = k.arm().matrix_world @ k.arm().pose.bones["Hand.N"].tail
print("HEAD", tuple(round(c, 3) for c in H), "HAND.N tip", tuple(round(c, 3) for c in hand))

# ---- camera: head ~25% of width at (0.27, 0.22), slight 3/4 from her right, 50 mm
res = k.frame_head(head_frac=0.25, head_xy=(0.27, 0.23), view_dir=(0.3, 1, -0.14), lens=50); print("frame", res)
cam = scene.camera; cam.data.clip_end = 300
q = cam.matrix_world.to_quaternion(); FWD = q @ Vector((0, 0, -1))
assert (q @ Vector((1, 0, 0))).x < 0, "image-right must be world -X"


def ray(fx, fy):
    """World direction through frame point (fx right, fy down)."""
    cd = cam.data; fr = cd.view_frame(scene=scene)  # tr, br, bl, tl in camera space
    tl, tr, bl = fr[3], fr[0], fr[2]
    p = tl + (tr - tl) * fx + (bl - tl) * fy
    return (cam.matrix_world.to_3x3() @ p).normalized()


def on_ground(fx, fy, z=0.0):
    d = ray(fx, fy); t = (z - cam.location.z) / d.z if d.z < -1e-3 else 99
    if t > 18:  # near/above the horizon: clamp far back
        p = cam.location + d * 18; p.z = z; return p
    return cam.location + d * t


def at_depth(fx, fy, dist):
    return cam.location + ray(fx, fy) * dist


def width_at(dist, frac):
    return frac * dist * cam.data.sensor_width / cam.data.lens


# ---- set: cobbles, plinth + huge weathered tombstone behind her
gnd = v2.ground(size=40, disp=0.03); gnd.data.materials.clear(); gnd.data.materials.append(v2.cobble_mat(5.5, (0.1, 0.105, 0.12)))
stone = v2.weathered_stone((0.4, 0.42, 0.47)); dark = v2.weathered_stone((0.22, 0.24, 0.3), moss_amt=0.35)
bark = v2.bark_mat((0.06, 0.05, 0.05))
def face_cam(p, turn=0.0):
    d = cam.location - Vector(p); return math.degrees(math.atan2(-d.x, d.y)) + turn


v2.tombstone("TombHero", (H.x + 0.2, H.y - 0.3, 0), w=0.95, h=1.75, d=0.2, style="round", tilt=(-5, 3), rot_z=face_cam((H.x, H.y, 0), -8), mat=stone)

# huge jack-o'-lantern right of centre, bottom at frame y~0.86, centre x 0.71, width ~0.32
p0 = on_ground(0.70, 0.86); d0 = (p0 - cam.location).length
R = width_at(d0, 0.31) / 2.1
big = v2.carved_pumpkin("PumpkinHero", (p0.x, p0.y - R * 0.3, R * 0.8), R, rot_z=face_cam(p0, 12), light=60 * (R / 0.25) ** 2, face="jack", rib=0.1, res=256)
print("hero pumpkin R", round(R, 3), k.project(big.location))
p1 = on_ground(0.95, 0.74); d1 = (p1 - cam.location).length; R1 = width_at(d1, 0.14) / 2; print('back pumpkin', round(R1, 3), round(d1, 2))
v2.carved_pumpkin("PumpkinBack", (p1.x, p1.y - R1, R1 * 0.8), R1, rot_z=face_cam(p1, 20), light=25 * (R1 / 0.25) ** 2, face="jack", rib=0.06)
# blurred foreground pumpkins cut off at the bottom edge
for nm, fx, fy, dist, wf in (("PumpkinFG1", 0.13, 1.0, 0.75, 0.2), ("PumpkinFG2", 0.46, 1.04, 0.7, 0.15)):
    p = at_depth(fx, fy, dist); r = width_at(dist, wf) / 2
    v2.carved_pumpkin(nm, (p.x, p.y, p.z), r, rot_z=face_cam(p, rnd.uniform(-20, 20)), light=6 * (r / 0.1) ** 2, face="classic")

# background stones / crypt / branches, placed through the frame on the ground far behind
for i, (fx, fy, hh) in enumerate([(0.6, 0.5, 1.35), (0.71, 0.47, 1.6), (0.84, 0.46, 1.5), (0.49, 0.47, 1.1), (0.98, 0.52, 2.8)]):
    dd = ray(fx, fy); dd.z = 0; p = cam.location + dd.normalized() * (7.0 + i * 0.5); p.z = 0
    v2.tombstone("TombBG%d" % i, tuple(p), w=hh * 0.5, h=hh, d=0.2, style=rnd.choice(["round", "point"]),
                 tilt=(rnd.uniform(-6, 6), rnd.uniform(-7, 7)), rot_z=face_cam(p, rnd.uniform(-25, 15)), mat=dark)
cp = on_ground(0.9, 0.42)
h.solid("TombCrypt", "cube", (cp.x, cp.y - 1, 1.6), (1.3, 1.0, 1.6), dark, rot=(0, 0, math.radians(face_cam(cp, -25))), bevel=0.04)
h.solid("TombCryptRoof", "cube", (cp.x, cp.y - 1, 3.3), (1.45, 1.15, 0.12), dark, rot=(0, 0, math.radians(face_cam(cp, -25))), bevel=0.03)
for i, (fx, fy, hh) in enumerate([(0.38, 0.42, 6.5), (0.02, 0.45, 6.0), (0.75, 0.41, 6.5), (1.02, 0.44, 5.5)]):
    p = on_ground(fx, fy)
    v2.gnarled_tree(tuple(p), hh, 300 + i, bark, depth=3)
# a few small mossy rocks at the bottom-right edge
for i in range(3):
    p = on_ground(rnd.uniform(0.84, 0.98), rnd.uniform(0.93, 0.99))
    try:
        k.import_model("rocks", "rock_moss_set_01", tuple(p), rnd.uniform(0, 360), rnd.uniform(0.08, 0.12))
    except Exception as e:
        print("rock skip", e); break

# ---- moon, stars, cloud
mo = h.moon(at_depth(0.55, 0.15, 45), width_at(45, 0.16) / 2, tint=(0.05, 0.45, 0.6))
print("moon", k.project(mo.location))
em = mo.data.materials[0].node_tree.nodes.get("Emission"); em.inputs["Strength"].default_value = 2.4
rp = [n for n in mo.data.materials[0].node_tree.nodes if n.type == 'VALTORGB'][0].color_ramp
rp.elements[0].color = (0.04, 0.4, 0.62, 1); rp.elements[1].color = (0.6, 0.92, 1.0, 1); rp.elements[0].position = 0.42; rp.elements[1].position = 0.58
h.stars(220, radius=70)
cl = h.fog("Cloud", tuple(at_depth(0.7, 0.3, 40)), (8, 3, 1.5), 0.25, color=(0.5, 0.7, 0.95), noise=0.6)

# ---- world, mist
k.world((0.015, 0.045, 0.14), strength=1.0)
h.fog("Mist", (0, -6, 2.0), (30, 20, 4.5), 0.03, color=(0.35, 0.55, 0.9), aniso=0.6, noise=1.2, fade_height=True)

# ---- lights: blue moon rim from behind-top, warm pumpkin bounce from image-right, faint cool front fill
for o in [o for o in scene.objects if o.type == "LIGHT" and not o.name.startswith("Pumpkin")]:
    bpy.data.objects.remove(o, do_unlink=True)
rim = H + Vector((-0.6, -1.4, 1.3)); k.area("MoonRim", rim, H, 110 * (rim - H).length_squared, 0.8, (0.45, 0.7, 1.0), 90)
sd = bpy.data.lights.new("Moon", "SUN"); sd.energy = 1.2; sd.color = (0.3, 0.55, 0.9); sd.angle = math.radians(1)
so = bpy.data.objects.new("MoonSun", sd); scene.collection.objects.link(so)
so.rotation_euler = (mo.location - H).normalized().to_track_quat("Z", "Y").to_euler()
wp = H + Vector((-0.7, 0.5, -0.35)); k.area("PumpkinBounce", wp, H, 18 * (wp - H).length_squared, 0.5, (1.0, 0.45, 0.1), 120)
fp = cam.location + Vector((0.3, 0, 0.3)); k.area("CoolFill", fp, H, 5 * (fp - H).length_squared, 1.2, (0.45, 0.6, 1.0), 120)
sp = big.location + Vector((0, 0, 0.1)) + (cam.location - big.location).normalized() * (R * 1.6)
k.area("PumpkinSpec", sp, big.location, 20, 0.3, (1.0, 0.6, 0.25), 90)
v2.lint()
for nm in ("TombHero", "PumpkinHero_root", "PumpkinBack_root", "PumpkinFG1_root", "PumpkinFG2_root", "TombCrypt"):
    print("proj", nm, [round(c, 3) for c in k.project(bpy.data.objects[nm].location)])
print("measure", k.measure())
k.setup_cycles(SAMPLES, look="AgX - Punchy", exposure=0.0, dof_fstop=2.8)
scene.cycles.volume_bounces = 1
bpy.ops.wm.save_as_mainfile(filepath=OUT + "_scene.blend", copy=True)
k.render(OUT + ".png", PCT, SAMPLES); print("RENDERED", OUT + ".png")
