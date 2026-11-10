"""Build Roblox user Bio_IsHere (id 360459264) in Blender from the downloaded assets.

Body: the 14 real "ROBLOX Boy" R15 meshes (meshes/body_*.obj, in studs), skinned to an
armature by bone parenting, so every part pivots on a real joint. Pose it in Pose Mode.
Run inside Blender (Scripting tab -> Open -> Run Script), or send over the Blender MCP socket.
Set POSE below to "gfx" (hand on hip, hand in hair) or "idle".
"""
import math, os
import bpy
from mathutils import Matrix, Vector

POSE = "gfx"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) if "__file__" in globals() else \
    r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
MESH = lambda i: os.path.join(ROOT, "meshes", f"{i}.obj")
TEX = lambda i: os.path.join(ROOT, "textures", f"{i}.png")
STUD = 0.28  # metres per stud

# ---------------------------------------------------------------- scene reset
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.lights, bpy.data.cameras,
             bpy.data.images, bpy.data.armatures):
    for b in list(coll):
        if b.users == 0:
            coll.remove(b)
scene = bpy.context.scene
col = scene.collection

# ---------------------------------------------------------------- materials
def srgb(h):
    c = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)

def mat(name, color, rough=0.55, metal=0.0, emit=None, strength=3.0, sss=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.9, 0.35, 0.2)
        b.inputs["Subsurface Scale"].default_value = 0.05
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

def striped_mat(name, scale):
    """Yellow shirt with thick black bands running around the part (object-space Z)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.75
    coord = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"; wave.bands_direction = "Z"; wave.wave_profile = "SAW"
    wave.inputs["Scale"].default_value = scale
    wave.inputs["Distortion"].default_value = 0.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].color = (*srgb("#FFB300"), 1)
    ramp.color_ramp.elements[1].position = 0.6
    ramp.color_ramp.elements[1].color = (0.012, 0.012, 0.012, 1)
    noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 90
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.06
    nt.links.new(coord.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m

def denim_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.85
    coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 1.6; noise.inputs["Detail"].default_value = 8
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*srgb("#405E82"), 1)
    ramp.color_ramp.elements[1].color = (*srgb("#93AECB"), 1)
    wave = nt.nodes.new("ShaderNodeTexWave"); wave.inputs["Scale"].default_value = 70; wave.inputs["Distortion"].default_value = 1.2
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.12
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(coord.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m

def tex_mat(name, tex_id, emissive=False, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(TEX(tex_id))
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emissive:
        nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = 6.0
    return m

SKIN = mat("Skin", srgb("#EAB892"), 0.45, sss=0.12)
BLACK = mat("Black", (0.01, 0.01, 0.012), 0.5)
SHOE = mat("Shoe", srgb("#2b2b30"), 0.35)
STRAP = mat("Strap", srgb("#151517"), 0.3, metal=0.5)
ORANGE = mat("Orange", srgb("#E8661A"), 0.45)
SHIRT = striped_mat("Shirt", 1.1)
SLEEVE = striped_mat("Sleeve", 1.6)
JEANS = denim_mat("Jeans")

# ---------------------------------------------------------------- armature (studs, +Y forward, +X = avatar's left)
BONES = [  # name, head, tail, parent
    ("LowerTorso", (0, 0, 2.70), (0, 0, 3.15), None),
    ("UpperTorso", (0, 0, 3.15), (0, 0, 4.85), "LowerTorso"),
    ("Head", (0, 0, 4.85), (0, 0, 6.00), "UpperTorso"),
]
for s, x in (("L", 1.0), ("R", -1.0)):
    BONES += [
        (f"UpperArm.{s}", (1.21 * x, 0, 4.55), (1.21 * x, 0, 3.87), "UpperTorso"),
        (f"LowerArm.{s}", (1.21 * x, 0, 3.87), (1.21 * x, 0, 3.05), f"UpperArm.{s}"),
        (f"Hand.{s}", (1.21 * x, 0, 3.05), (1.21 * x, 0, 2.05), f"LowerArm.{s}"),
        (f"UpperLeg.{s}", (0.5 * x, 0, 2.72), (0.5 * x, 0, 1.50), "LowerTorso"),
        (f"LowerLeg.{s}", (0.5 * x, 0, 1.50), (0.5 * x, 0, 0.55), f"UpperLeg.{s}"),
        (f"Foot.{s}", (0.5 * x, 0, 0.55), (0.5 * x, 0, 0.0), f"LowerLeg.{s}"),
    ]

ad = bpy.data.armatures.new("Bio_Rig")
arm = bpy.data.objects.new("Bio_IsHere", ad); col.objects.link(arm)
ad.display_type = "STICK"
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
for name, h, t, p in BONES:
    eb = ad.edit_bones.new(name); eb.head = h; eb.tail = t
    eb.align_roll(Vector((0, 1, 0)))
    if p: eb.parent = ad.edit_bones[p]; eb.use_connect = False
bpy.ops.object.mode_set(mode="OBJECT")

def bind(o, bone):
    """Parent to a bone without moving the object (armature is at identity while building)."""
    b = ad.bones[bone]
    o.parent = arm; o.parent_type = "BONE"; o.parent_bone = bone
    o.matrix_parent_inverse = (b.matrix_local @ Matrix.Translation((0, b.length, 0))).inverted()
    return o

def load_obj(path, name, material):
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=path, forward_axis="Y", up_axis="Z")
    o = next(x for x in bpy.data.objects if x not in before)
    o.name = name
    o.data.materials.clear(); o.data.materials.append(material)
    o.data.shade_smooth()
    return o

def body(part, loc, material, bone):
    o = load_obj(os.path.join(ROOT, "meshes", f"body_{part}.obj"), part, material)
    o.location = loc
    return bind(o, bone)

# ---------------------------------------------------------------- body parts (centres in studs)
body("LowerTorso", (0, 0, 2.90), JEANS, "LowerTorso")
body("UpperTorso", (0, 0, 3.99), SHIRT, "UpperTorso")
for s, side, x in (("L", "Left", 1.0), ("R", "Right", -1.0)):
    body(f"{side}UpperArm", (1.21 * x, 0, 4.28), SLEEVE, f"UpperArm.{s}")
    body(f"{side}LowerArm", (1.21 * x, 0, 3.47), BLACK, f"LowerArm.{s}")
    body(f"{side}Hand", (1.21 * x, 0, 2.56), SKIN, f"Hand.{s}")
    body(f"{side}UpperLeg", (0.5 * x, 0, 2.09), JEANS, f"UpperLeg.{s}")
    body(f"{side}LowerLeg", (0.5 * x, 0, 1.02), JEANS, f"LowerLeg.{s}")
    body(f"{side}Foot", (0.5 * x, 0, 0.314), SHOE, f"Foot.{s}")

def box(name, size, loc, material, bone, bevel=0.03, subsurf=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True)
    m = o.modifiers.new("Bevel", "BEVEL"); m.width = bevel; m.segments = 3; m.harden_normals = True
    if subsurf:
        s = o.modifiers.new("Sub", "SUBSURF"); s.levels = s.render_levels = subsurf
    o.data.shade_smooth(); o.data.materials.append(material)
    return bind(o, bone)

# belt, suspenders, chest emblem (sit on the clothing surface)
for x in (0.42, -0.42):
    box("Suspender", (0.09, 0.05, 1.45), (x, 0.545, 3.92), STRAP, "UpperTorso", 0.02)
    box("SuspenderBack", (0.09, 0.05, 1.45), (x, -0.545, 3.92), STRAP, "UpperTorso", 0.02)
box("Emblem", (0.34, 0.05, 0.34), (0, 0.56, 4.1), ORANGE, "UpperTorso", 0.06, subsurf=2)

# ---------------------------------------------------------------- head (classic rounded cylinder) + face
HC = Vector((0, 0, 5.42))
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.6, depth=1.2, location=HC)
head = bpy.context.active_object; head.name = "Head"
bm = head.modifiers.new("Bevel", "BEVEL"); bm.width = 0.3; bm.segments = 8; bm.limit_method = "ANGLE"
sub = head.modifiers.new("Sub", "SUBSURF"); sub.levels = sub.render_levels = 1
head.data.shade_smooth(); head.data.materials.append(SKIN)
bind(head, "Head")

def on_face(x, z, lift=0.012):
    return (x, math.sqrt(max(0.36 - x * x, 0)) + lift, z)

def curve(name, pts, depth):
    cd = bpy.data.curves.new(name, "CURVE"); cd.dimensions = "3D"
    cd.bevel_depth = depth; cd.bevel_resolution = 3; cd.use_fill_caps = True
    sp = cd.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, v in zip(sp.points, pts):
        p.co = (*v, 1)
    o = bpy.data.objects.new(name, cd); col.objects.link(o)
    o.data.materials.append(BLACK)
    return bind(o, "Head")

zig = [on_face(-0.3 + i * 0.075, 5.18 + (0.07 if i % 2 else 0)) for i in range(9)]
curve("Mouth", zig, 0.011)
for i in range(1, 8, 2):
    curve(f"Tooth{i}", [zig[i], on_face(zig[i][0], 5.12)], 0.008)
for x in (0.2, -0.2):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=on_face(x, 5.5, 0.0))
    e = bpy.context.active_object; e.name = "Eye"; e.scale = (0.75, 0.4, 1.35)
    e.data.shade_smooth(); e.data.materials.append(BLACK); bind(e, "Head")

# ---------------------------------------------------------------- accessories (Roblox meshes in 0.3 m/stud OBJs)
def accessory(mesh_id, name, material, offset, scale, bone="Head", rot=(0, 0, 0), centre=HC):
    o = load_obj(MESH(mesh_id), name, material)
    o.scale = (scale,) * 3
    o.rotation_euler = [math.radians(a) for a in rot]
    o.location = centre + Vector(offset)
    return bind(o, bone)

accessory(16627529, "Hair_BeautifulHair", tex_mat("HairMat", 16627494, rough=0.35), (-0.09, -0.06, 0.63), 1.58)
accessory(83284634, "Cap_Band", tex_mat("CapMat", 3210183293, rough=0.6), (0, 0, 0.38), 1.26)
accessory(4131800469, "VintageGlasses", tex_mat("GlassesMat", 4131810844, rough=0.15, metal=0.9), (0, 0.62, 0.1), 3.0)
accessory(4641670867, "SparklingShine", tex_mat("ShineMat", 4641683252, emissive=True), (0, 0, 0.3), 3.4)
accessory(5355486008, "GalaxySword", tex_mat("SwordMat", 5355543242, rough=0.2, metal=0.3),
          (0.1, -0.66, -0.15), 4.2, "UpperTorso", rot=(0, -38, 0), centre=Vector((0, 0, 3.99)))

# ---------------------------------------------------------------- pose
def aim(bone, d, hint=(0, 1, 0)):
    """Point a bone along d (armature space) with its local Z towards hint."""
    bpy.context.view_layer.update()
    pb = arm.pose.bones[bone]
    y = Vector(d).normalized()
    h = Vector(hint); z = (h - h.dot(y) * y).normalized(); x = y.cross(z)
    m = Matrix((x, y, z)).transposed().to_4x4(); m.translation = pb.head
    pb.matrix = m

if POSE == "gfx":
    # contrapposto: weight on the right leg, hand on hip, other hand running through the hair
    aim("LowerTorso", (0.07, 0, 1), (-0.18, 1, 0))
    aim("UpperTorso", (-0.08, 0.04, 1), (0.22, 1, 0))
    aim("Head", (-0.12, 0.06, 1), (0.3, 1, 0))
    aim("UpperArm.L", (0.62, -0.3, -0.72))
    aim("LowerArm.L", (-0.55, 0.3, -0.78))
    aim("Hand.L", (-0.45, 0.35, -0.82), (0, 0, 1))
    aim("UpperArm.R", (-0.6, 0.25, 0.76))
    aim("LowerArm.R", (0.8, -0.05, 0.6))
    aim("Hand.R", (0.75, -0.3, 0.3), (0, 0, 1))
    aim("UpperLeg.R", (-0.1, 0, -1))
    aim("LowerLeg.R", (-0.02, 0, -1))
    aim("Foot.R", (0, 0, -1), (-0.25, 1, 0))
    aim("UpperLeg.L", (-0.18, 0.32, -0.93))
    aim("LowerLeg.L", (0.06, -0.12, -1))
    aim("Foot.L", (0, 0, -1), (0.35, 1, 0))
else:
    aim("UpperArm.L", (0.25, 0, -1)); aim("UpperArm.R", (-0.25, 0, -1))
    aim("LowerArm.L", (0.15, 0.25, -1)); aim("LowerArm.R", (-0.15, 0.25, -1))
    aim("Hand.L", (0.15, 0.25, -1)); aim("Hand.R", (-0.15, 0.25, -1))
bpy.context.view_layer.update()
arm.scale = (STUD,) * 3

# ---------------------------------------------------------------- stage: curved backdrop, GFX lighting
import bmesh
me = bpy.data.meshes.new("Backdrop"); bk = bpy.data.objects.new("Backdrop", me); col.objects.link(bk)
bmm = bmesh.new()
v = [bmm.verts.new(p) for p in ((-12, 10, 0), (12, 10, 0), (12, -3, 0), (-12, -3, 0), (-12, -3, 9), (12, -3, 9))]
bmm.faces.new((v[0], v[1], v[2], v[3])); bmm.faces.new((v[3], v[2], v[5], v[4]))
bmm.to_mesh(me); bmm.free()
bv = bk.modifiers.new("Curve", "BEVEL"); bv.width = 2.5; bv.segments = 24; bv.limit_method = "ANGLE"
me.shade_smooth()
me.materials.append(mat("Backdrop", srgb("#1d1230"), 0.32))

bpy.ops.mesh.primitive_torus_add(major_radius=0.62, minor_radius=0.012, major_segments=128, location=(-0.41, -1.11, 1.62))
halo = bpy.context.active_object; halo.name = "Halo"
halo.rotation_euler = (Vector((1.45, 3.9, 0.85)) - halo.location).to_track_quat("Z", "Y").to_euler()
halo.data.materials.append(mat("HaloGlow", (0, 0, 0), emit=srgb("#9B5CFF"), strength=25))

def light(name, loc, energy, size, color, target=(0, 0, 0.95)):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.color = color; ld.size = size; ld.spread = math.radians(70)
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
co.location = (1.45, 3.9, 0.85)
co.rotation_euler = (Vector((0, 0, 0.95)) - co.location).to_track_quat("-Z", "Y").to_euler()
cam.dof.focus_distance = (co.location - Vector((0, 0.1, 1.3))).length
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
print("Bio_IsHere built:", len(arm.children), "parts, pose", POSE)
