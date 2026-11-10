"""Rig a Roblox avatar-3d export (from fetch_avatar3d.py) and stage a GFX shot.

Splits the OBJ into its body parts, finds head/torso/limbs from their positions, builds an R15
armature with joints derived from part overlaps, binds every part (and accessory) to its bone,
then poses it. Works for any R15 avatar export. Set AVATAR_DIR and POSE below.
"""
import math, os, glob, json
import bpy, bmesh
from mathutils import Matrix, Vector

AVATAR_DIR = globals().get("AVATAR_DIR", r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\exact")
POSE = globals().get("POSE", "gfx")
STUD = 0.28

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.images, bpy.data.armatures, bpy.data.curves):
    for b in list(coll):
        if b.users == 0:
            coll.remove(b)
scene = bpy.context.scene
col = scene.collection

# ---------------------------------------------------------------- import + recentre
meta = json.load(open(os.path.join(AVATAR_DIR, "meta.json")))
before = set(bpy.data.objects)
bpy.ops.wm.obj_import(filepath=os.path.join(AVATAR_DIR, meta["obj"]), use_split_groups=True)
objs = [o for o in bpy.data.objects if o not in before]
for o in objs:  # bake the importer's axis-conversion rotation into the mesh
    o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)

def bounds(o):
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    mn = Vector([min(v[i] for v in vs) for i in range(3)])
    mx = Vector([max(v[i] for v in vs) for i in range(3)])
    return mn, mx

players = [o for o in objs if o.name.startswith("Player")]
allmin = Vector([min(bounds(o)[0][i] for o in players) for i in range(3)])
allmax = Vector([max(bounds(o)[1][i] for o in players) for i in range(3)])
shift = Vector(((allmin.x + allmax.x) / -2, (allmin.y + allmax.y) / -2, -allmin.z))
for o in objs:
    o.data.transform(Matrix.Translation(shift))
    o.data.update()

# optional: some exports lack one leg (stocking-cut avatars). MIRROR_LEG="P" drops stray pieces on the P side and
# copies the N-side leg parts across (swap "N" to mirror the other way).
if globals().get("MIRROR_LEG"):
    _sg = 1 if MIRROR_LEG == "P" else -1
    def _ctr(o):
        mn, mx = bounds(o); return (mn + mx) / 2, mx - mn
    legz = min(bounds(o)[0].z for o in players) + (allmax.z - allmin.z) * 0.45
    for o in list(players):   # stray partial pieces below hip height on the missing side
        c_, sz = _ctr(o)
        if _sg * c_.x > 0.1 and c_.z < legz and sz.x < 0.4:
            bpy.data.objects.remove(o, do_unlink=True); players.remove(o); objs.remove(o)
    for o in list(players):
        c_, sz = _ctr(o)
        if -_sg * c_.x > 0.1 and c_.z < legz and sz.x > 0.25:
            n = o.copy(); n.data = o.data.copy(); n.name = "Player_m" + o.name[6:]
            col_ = bpy.context.scene.collection; col_.objects.link(n)
            n.data.transform(Matrix.Scale(-1, 4, (1, 0, 0))); n.data.flip_normals(); players.append(n); objs.append(n)

# textures: the MTL names them by CDN hash without an extension, so wire them up here
tex_of, cur = {}, None
for line in open(os.path.join(AVATAR_DIR, meta["mtl"])):
    if line.startswith("newmtl"): cur = line.split()[1]
    elif line.startswith("map_Kd"): tex_of[cur] = line.split()[1]
for o in objs:
    for m in o.data.materials:
        key = next((k for k in tex_of if m.name.startswith(k)), None)
        nt = m.node_tree; b = nt.nodes["Principled BSDF"]
        b.inputs["Roughness"].default_value = 0.55
        b.inputs["Specular IOR Level"].default_value = 0.3
        if key:
            t = nt.nodes.new("ShaderNodeTexImage"); t.interpolation = "Cubic"
            t.image = bpy.data.images.load(os.path.join(AVATAR_DIR, tex_of[key]), check_existing=True)
            nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
            nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])

# ---------------------------------------------------------------- classify parts
info = {o: (bounds(o), (bounds(o)[0] + bounds(o)[1]) / 2) for o in players}
c = lambda o: info[o][1]
head = max(players, key=lambda o: c(o).z)
rest = [o for o in players if o is not head]
width = lambda o: info[o][0][1].x - info[o][0][0].x
torso = sorted(sorted([o for o in rest if abs(c(o).x) < 0.25], key=width)[-2:], key=lambda o: c(o).z)
limbs = [o for o in rest if o not in torso]
lt, ut = torso
is_leg = lambda o: abs(c(o).x) < width(ut) * 0.4 and c(o).z < c(lt).z
chains = {}
for sign, s in ((1, "P"), (-1, "N")):
    side = [o for o in limbs if c(o).x * sign > 0]
    legs = sorted(side, key=lambda o: info[o][0][0].z)[:3]  # the three parts reaching lowest: foot, shin, thigh
    chains["Arm" + s] = sorted([o for o in side if o not in legs], key=lambda o: -c(o).z)
    chains["Leg" + s] = sorted(legs, key=lambda o: -c(o).z)
assert len(torso) == 2 and all(len(chains[k]) == 3 for k in ('LegP', 'LegN')) and all(len(chains[k]) in (2, 3) for k in ('ArmP', 'ArmN')), (len(torso), {k: len(v) for k, v in chains.items()})

def joint(upper, lower):
    """Pivot near the top of the lower part, so it stays tucked inside the upper part when bent."""
    (umin, _), (_, lmax) = info[upper][0], info[lower][0]
    z = max(lmax.z - 0.12, (umin.z + lmax.z) / 2)
    return Vector(((c(upper).x + c(lower).x) / 2, (c(upper).y + c(lower).y) / 2, z))

lt, ut = torso
waist = joint(ut, lt)
neck = Vector((0, c(head).y, info[head][0][0].z + 0.05))
BONES = [("LowerTorso", Vector((0, c(lt).y, info[lt][0][0].z)), waist, None, lt),
         ("UpperTorso", waist, neck, "LowerTorso", ut),
         ("Head", neck, Vector((0, neck.y, info[head][0][1].z)), "UpperTorso", head)]
for s in ("P", "N"):
    arm_parts = chains["Arm" + s]
    if len(arm_parts) == 2:  # some bodies (chibi) have no visible forearm: keep the bone, no mesh
        up, end = arm_parts; low = None
    else:
        up, low, end = arm_parts
    sh = Vector((c(up).x, c(up).y, info[up][0][1].z - 0.2))
    if low is None:
        e = Vector((c(up).x, c(up).y, info[up][0][0].z + 0.08))
        w = Vector((c(end).x, c(end).y, info[end][0][1].z - 0.08))
    else:
        e, w = joint(up, low), joint(low, end)
    BONES += [(f"UpperArm.{s}", sh, e, "UpperTorso", up), (f"LowerArm.{s}", e, w, f"UpperArm.{s}", low),
              (f"Hand.{s}", w, Vector((c(end).x, c(end).y, info[end][0][0].z)), f"LowerArm.{s}", end)]
    up, low, end = chains["Leg" + s]
    hp = Vector((c(up).x, c(up).y, info[up][0][1].z - 0.2))
    k, a = joint(up, low), joint(low, end)
    BONES += [(f"UpperLeg.{s}", hp, k, "LowerTorso", up), (f"LowerLeg.{s}", k, a, f"UpperLeg.{s}", low),
              (f"Foot.{s}", a, Vector((a.x, a.y, 0)), f"LowerLeg.{s}", end)]

ad = bpy.data.armatures.new("Rig")
arm = bpy.data.objects.new("Avatar", ad); col.objects.link(arm)
ad.display_type = "STICK"
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
for name, h, t, p, _ in BONES:
    eb = ad.edit_bones.new(name); eb.head = h; eb.tail = t
    eb.align_roll(Vector((0, 1, 0)))
    if p: eb.parent = ad.edit_bones[p]
bpy.ops.object.mode_set(mode="OBJECT")

def bind(o, bone):
    b = ad.bones[bone]
    o.parent = arm; o.parent_type = "BONE"; o.parent_bone = bone
    o.matrix_parent_inverse = (b.matrix_local @ Matrix.Translation((0, b.length, 0))).inverted()

for name, _, _, _, part in BONES:
    if part is None: continue
    part.name = name.replace(".", "_"); bind(part, name)
for o in objs:
    if o.name.startswith("Handle"):
        mn, mx = bounds(o)
        bind(o, "Head" if (mn.z + mx.z) / 2 > neck.z - 0.2 else "UpperTorso")
import sys as _sys  # sleeves and skirts must bend with the limbs, or hands float when posed
_sys.path.insert(0, "C:/Users/Siddharth D/Projects/gfx and animation roblox blender/tools")
import gfx_kit as _k
_k.skin_clothes()

# ---------------------------------------------------------------- pose (P = avatar's right side, +X)
def aim(bone, d, hint=(0, 1, 0)):
    bpy.context.view_layer.update()
    pb = arm.pose.bones[bone]
    y = Vector(d).normalized()
    h = Vector(hint); z = (h - h.dot(y) * y).normalized(); x = y.cross(z)
    m = Matrix((x, y, z)).transposed().to_4x4(); m.translation = pb.head
    pb.matrix = m

if POSE == "gfx":
    aim("LowerTorso", (0.07, 0, 1), (-0.18, 1, 0))
    aim("UpperTorso", (-0.08, 0.04, 1), (0.22, 1, 0))
    aim("Head", (-0.12, 0.06, 1), (0.3, 1, 0))
    aim("UpperArm.P", (0.62, -0.3, -0.72))
    aim("LowerArm.P", (-0.55, 0.3, -0.78))
    aim("Hand.P", (-0.45, 0.35, -0.82), (0, 0, 1))
    aim("UpperArm.N", (-0.6, 0.25, 0.76))
    aim("LowerArm.N", (0.8, -0.05, 0.6))
    aim("Hand.N", (0.75, -0.3, 0.3), (0, 0, 1))
    aim("UpperLeg.N", (-0.1, 0, -1))
    aim("LowerLeg.N", (-0.02, 0, -1))
    aim("Foot.N", (0, 0, -1), (-0.25, 1, 0))
    aim("UpperLeg.P", (-0.18, 0.32, -0.93))
    aim("LowerLeg.P", (0.06, -0.12, -1))
    aim("Foot.P", (0, 0, -1), (0.35, 1, 0))
bpy.context.view_layer.update()
arm.scale = (STUD,) * 3

# ---------------------------------------------------------------- stage
def mat(name, color, rough=0.5, emit=None, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = strength
    return m

me = bpy.data.meshes.new("Backdrop"); bk = bpy.data.objects.new("Backdrop", me); col.objects.link(bk)
bm = bmesh.new()
v = [bm.verts.new(p) for p in ((-12, 10, 0), (12, 10, 0), (12, -3, 0), (-12, -3, 0), (-12, -3, 9), (12, -3, 9))]
bm.faces.new((v[0], v[1], v[2], v[3])); bm.faces.new((v[3], v[2], v[5], v[4])); bm.to_mesh(me); bm.free()
bv = bk.modifiers.new("Curve", "BEVEL"); bv.width = 2.5; bv.segments = 24
me.shade_smooth(); me.materials.append(mat("Backdrop", (0.012, 0.006, 0.03), 0.3))

CAM = Vector((1.45, 3.9, 0.85))
bpy.ops.mesh.primitive_torus_add(major_radius=0.62, minor_radius=0.012, major_segments=128, location=(-0.41, -1.11, 1.62))
halo = bpy.context.active_object; halo.name = "Halo"
halo.rotation_euler = (CAM - halo.location).to_track_quat("Z", "Y").to_euler()
halo.data.materials.append(mat("HaloGlow", (0, 0, 0), emit=(0.33, 0.1, 1.0), strength=25))

def light(name, loc, energy, size, color, target=(0, 0, 0.95)):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.color = color; ld.size = size
    ld.spread = math.radians(70)
    o = bpy.data.objects.new(name, ld); col.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

light("Key", (2.2, 2.7, 2.5), 380, 1.8, (1.0, 0.9, 0.78))
light("Fill", (-2.6, 2.4, 1.0), 90, 3.0, (0.75, 0.82, 1.0))
light("RimPurple", (-2.0, -1.8, 2.3), 650, 1.2, (0.62, 0.35, 1.0))
light("RimGold", (2.2, -1.6, 1.6), 260, 1.0, (1.0, 0.72, 0.3))

world = scene.world or bpy.data.worlds.new("World"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.012, 0.04, 1)

cam = bpy.data.cameras.new("Cam"); cam.lens = 55
cam.dof.use_dof = True; cam.dof.aperture_fstop = 4.0
co = bpy.data.objects.new("Camera", cam); col.objects.link(co)
co.location = CAM
co.rotation_euler = (Vector((0, 0, 0.95)) - CAM).to_track_quat("-Z", "Y").to_euler()
cam.dof.focus_distance = (CAM - Vector((0, 0.1, 1.3))).length
scene.camera = co

scene.render.engine = "BLENDER_EEVEE"
scene.eevee.use_raytracing = True
scene.eevee.taa_render_samples = 96
scene.view_settings.view_transform = "AgX"
try:
    scene.view_settings.look = "AgX - Punchy"
except TypeError:
    pass
scene.render.resolution_x, scene.render.resolution_y = 1080, 1350
print("rigged parts:", len(arm.children), "| bones:", [b[0] for b in BONES][:3], "...")
