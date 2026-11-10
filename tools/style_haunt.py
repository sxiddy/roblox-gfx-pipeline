"""Haunting spirit in a misty forest: backlit by cold moon, bare trees fading into fog, veils and ghost figures.
Run after build_exact_gfx.py (see run_haunt.py)."""
import math, random, sys
import bpy
from mathutils import Vector

sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import importlib, gfx_kit as k
importlib.reload(k)

scene = bpy.context.scene
OUT = globals().get("OUT", r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\gfx_output\sttvr_l1ght\haunt")
PCT = globals().get("PCT", 50)
SAMPLES = globals().get("SAMPLES", 64)

k.clear(["Tree", "Grave", "Ghost", "Veil", "Ground", "Fog", "Mist", "Backdrop", "Halo", "Sunburst", "Moon"])
k.clean_stray()

# ---------------------------------------------------------------- pose (written plan)
k.reset_pose()
A = k.aim
A("LowerTorso", (0, -0.05, 1))
A("UpperTorso", (0.03, -0.1, 1))
A("Head", (-0.34, 0.12, 0.93), (0.15, 1, 0))
A("UpperArm.P", (0.22, 0.0, -0.97)); A("LowerArm.P", (0.16, 0.38, -0.91)); A("Hand.P", (0.1, 0.3, -0.95), (0, 0, 1))
A("UpperArm.N", (-0.2, 0.02, -0.97)); A("LowerArm.N", (-0.14, 0.4, -0.9)); A("Hand.N", (-0.08, 0.32, -0.94), (0, 0, 1))
A("UpperLeg.P", (0.04, 0, -1)); A("UpperLeg.N", (-0.04, 0.03, -1))
k.upd()

# ---------------------------------------------------------------- render settings
scene.render.resolution_x, scene.render.resolution_y = 1080, 1350
if not scene.camera:
    cd = bpy.data.cameras.new("Cam"); co = bpy.data.objects.new("Cam", cd); scene.collection.objects.link(co); scene.camera = co
random.seed(7)


def mat(name, color, rough=0.9, emit=None, strength=1.0, alpha=None):
    return k.material(name, color, rough, 0.0, emit, strength, alpha)


def add(obj, m=None):
    if m: obj.data.materials.append(m)
    return obj


# ---------------------------------------------------------------- ground
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0)); g = bpy.context.active_object; g.name = "Ground"
try:
    gm = k.pbr("brown_mud_leaves_01", 0.5, tint=(0.16, 0.18, 0.22))
except Exception as e:
    print("pbr failed", e); gm = mat("GroundM", (0.03, 0.03, 0.035))
g.data.materials.append(gm)

# ---------------------------------------------------------------- bare trees
bark = mat("Bark", (0.02, 0.02, 0.025), 0.95)


def branch(base, d, L, r0):
    bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=r0, radius2=r0 * 0.25, depth=L)
    b = bpy.context.active_object; b.name = "Tree_b"
    d = Vector(d).normalized(); b.location = base + d * L / 2
    b.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); b.data.materials.append(bark)
    return b


def tree(x, y, h, r):
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=r, radius2=r * 0.3, depth=h, location=(x, y, h / 2))
    t = bpy.context.active_object; t.name = "Tree"; t.data.materials.append(bark)
    for _ in range(random.randint(5, 8)):
        z = random.uniform(h * 0.3, h * 0.95); a = random.uniform(0, math.tau)
        tilt = random.uniform(0.9, 1.3)
        d = (math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), math.cos(tilt))
        L = random.uniform(1.0, 2.6) * (1.3 - z / h * 0.6)
        b = branch(Vector((x, y, z)), d, L, r * 0.28)
        if random.random() < 0.7:  # twig
            b2 = branch(b.location + Vector(d) * L / 2, (d[0] + random.uniform(-.6, .6), d[1] + random.uniform(-.6, .6), d[2] + .4), L * 0.5, r * 0.1)


for i in range(34):
    d = random.uniform(2.5, 22)
    x = random.uniform(-1, 1) * (d * 0.55 + 1.2); y = -d
    if abs(x) < 0.9 and d < 5: x += math.copysign(1.6, x or 1)
    tree(x, y, random.uniform(5, 9), random.uniform(0.1, 0.26))
for i in range(22):
    d = random.uniform(3.5, 20); x = random.uniform(-0.42, 0.42) * (d + 2.5)
    if abs(x) < 0.7: x += math.copysign(0.9, x or 1)
    tree(x, -d, random.uniform(6, 10), random.uniform(0.1, 0.24))
for i in range(4):  # near trees framing the shot, in front/side
    tree(random.choice([-1, 1]) * random.uniform(1.8, 3.2), random.uniform(-3, 1.5), random.uniform(6, 9), random.uniform(0.14, 0.24))

# ---------------------------------------------------------------- gravestones
stone = k.pbr("rock_moss_set_01", 1.0) if False else mat("Stone", (0.05, 0.055, 0.06), 0.85)
for i in range(7):
    x = random.uniform(-4.5, 4.5); y = random.uniform(-9, -2.5)
    if abs(x) < 1.0 and y > -3.5: x += 1.6
    w, h = random.uniform(0.35, 0.55), random.uniform(0.6, 1.1)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, h / 2 - 0.1)); s = bpy.context.active_object; s.name = "Grave"
    s.scale = (w, 0.12, h); s.rotation_euler = (random.uniform(-.08, .08), random.uniform(-.1, .1), random.uniform(-.5, .5))
    bv = s.modifiers.new("b", "BEVEL"); bv.width = 0.04; bv.segments = 2
    s.data.materials.append(stone)

# ---------------------------------------------------------------- veil + ghosts (translucent cloth)
veil = mat("VeilM", (0.8, 0.85, 0.92), 0.7, emit=(0.5, 0.6, 0.75), strength=0.45, alpha=0.28)
for i, (vx, vy, vz, vw, vh, ang) in enumerate([][:0] and [(-0.75, -0.8, 1.5, 0.22, 2.3, 8), (-0.45, -1.2, 1.7, 0.18, 2.6, -6), (0.6, -0.9, 1.45, 0.24, 2.2, 5),
                                               (0.95, -1.3, 1.65, 0.16, 2.5, -9), (0.05, -1.6, 1.8, 0.3, 2.8, 3)]):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=6, y_subdivisions=40, size=1, location=(vx, vy, vz))
    v = bpy.context.active_object; v.name = "Veil_%d" % i; v.rotation_euler = (math.radians(90), 0, math.radians(ang)); v.scale = (vw, vh, 1)
    w = v.modifiers.new("w", "WAVE"); w.height = 0.35; w.width = 0.55; w.narrowness = 2.5; w.time_offset = 1.3 + i
    w.use_normal_x = True; w.use_x = True; w.use_y = False
    w2 = v.modifiers.new("w2", "WAVE"); w2.use_normal = True; w2.height = 0.12; w2.width = 0.3; w2.start_position_y = i
    v.data.materials.append(veil); v.data.shade_smooth()

ghost = mat("GhostM", (0.75, 0.8, 0.9), 0.8, emit=(0.45, 0.55, 0.7), strength=0.5, alpha=0.3)
for i, (x, y) in enumerate([(-2.6, -9.5), (-0.9, -12), (1.6, -10), (3.2, -13), (-4.4, -14), (0.4, -16)]):
    s = 1.0 + (i % 3) * 0.12
    bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=0.5 * s, radius2=0.12 * s, depth=1.5 * s, location=(x, y, 0.75 * s)); c = bpy.context.active_object
    c.name = "Ghost"; c.data.materials.append(ghost); c.data.shade_smooth()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15 * s, location=(x, y, 1.62 * s)); h = bpy.context.active_object
    h.name = "Ghost_h"; h.data.materials.append(ghost)

# ---------------------------------------------------------------- fog volumes
def fog(name, loc, size, density, aniso=0.2, noise=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); f = bpy.context.active_object; f.name = name; f.scale = size
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type not in {"OUTPUT_MATERIAL"}: nt.nodes.remove(n)
    out = nt.nodes["Material Output"]; pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = (0.75, 0.82, 0.95, 1); pv.inputs["Density"].default_value = density; pv.inputs["Anisotropy"].default_value = aniso
    if noise:
        tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = noise
        nz.inputs["Detail"].default_value = 4
        cr = nt.nodes.new("ShaderNodeMapRange"); cr.inputs[1].default_value = 0.35; cr.inputs[2].default_value = 0.75
        cr.inputs[4].default_value = 0.0; cr.inputs[3].default_value = 0.0
        mu = nt.nodes.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; mu.inputs[1].default_value = density
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], cr.inputs["Value"])
        cr.inputs[4].default_value = 0.0; cr.inputs[3].default_value = 1.0
        sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sp.inputs[0])
        inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
        nt.links.new(sp.outputs["Z"], inv.inputs[1])
        sq = nt.nodes.new("ShaderNodeMath"); sq.operation = "POWER"; sq.inputs[1].default_value = 3.0; nt.links.new(inv.outputs[0], sq.inputs[0])
        m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; nt.links.new(cr.outputs[0], m2.inputs[0]); nt.links.new(sq.outputs[0], m2.inputs[1])
        nt.links.new(m2.outputs[0], mu.inputs[0]); nt.links.new(mu.outputs[0], pv.inputs["Density"])
    nt.links.new(pv.outputs[0], out.inputs["Volume"]); f.data.materials.append(m)
    f.visible_shadow = False
    return f


fog("Fog_air", (0, -8, 4), (40, 40, 8), 0.007, 0.3)
fog("Mist_ground", (0, -4, 0.45), (40, 30, 1.8), 0.9, 0.1, noise=2.2)

# ---------------------------------------------------------------- camera
k.world((0.07, 0.085, 0.11), strength=0.12, haze=0.0)
res = k.frame_head(head_frac=0.3, head_xy=(0.5, 0.3), view_dir=(0.08, 1, -0.04), lens=50)
print("frame", res)
scene.camera.data.clip_end = 200

# ---------------------------------------------------------------- lights (moon back, dim front fill)
for o in [o for o in scene.objects if o.type == "LIGHT"]:
    bpy.data.objects.remove(o, do_unlink=True)
H = k.head_center()
k.area("MoonBack", H + Vector((-3.0, -5.5, 3.2)), H, 650, 5, (0.72, 0.84, 1.0), 120)
k.area("MoonRim", H + Vector((3.2, -3.5, 1.0)), H, 450, 3, (0.8, 0.88, 1.0), 120)
k.area("FrontFill", H + Vector((0.8, 3.0, 0.5)), H, 160, 3.5, (0.7, 0.8, 1.0), 150)

k.setup_cycles(SAMPLES, look="None", exposure=-0.3, dof_fstop=2.8)
scene.cycles.volume_bounces = 1
scene.render.film_transparent = False
bpy.ops.wm.save_as_mainfile(filepath=OUT + "_scene.blend", copy=True)
k.render(OUT + ".png", PCT, SAMPLES)
print("RENDERED", OUT + ".png")
