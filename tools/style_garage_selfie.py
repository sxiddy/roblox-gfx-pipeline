"""Restage a rigged avatar as a high-angle wide-lens selfie in a rooftop parking garage:
concrete floor with yellow bay lines, low wall + chain-link fence, cardboard boxes, overcast top light. Cycles, 9:16."""
import math
import bpy
from mathutils import Matrix, Vector

scene = bpy.context.scene
arm = bpy.data.objects["Avatar"]
for o in list(bpy.data.objects):
    if o.type in {"LIGHT"} or o.name.split(".")[0] in {"Backdrop", "Halo", "Floor", "Wall", "Fence", "Post", "Rail", "Box", "Tape", "Plane", "Key", "Bounce", "Overcast", "FaceFill"}:
        bpy.data.objects.remove(o, do_unlink=True)

def aim(bone, d, hint=(0, 1, 0)):
    bpy.context.view_layer.update()
    pb = arm.pose.bones[bone]
    y = Vector(d).normalized()
    h = Vector(hint); z = (h - h.dot(y) * y).normalized(); x = y.cross(z)
    m = Matrix((x, y, z)).transposed().to_4x4(); m.translation = pb.head
    pb.matrix = m

for pb in arm.pose.bones:
    pb.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
H = arm.matrix_world @ ((arm.pose.bones["Head"].head + arm.pose.bones["Head"].tail) / 2)
# selfie: avatar's right arm (+X, screen-left) reaches up to the phone; body leans in, head dips toward the arm
aim("LowerTorso", (0.03, 0.1, 1))
aim("UpperTorso", (0.1, 0.32, 1), (0.25, 1, 0))
aim("UpperArm.P", (0.5, 0.55, 0.68))
aim("LowerArm.P", (0.42, 0.6, 0.68))
aim("Hand.P", (0.42, 0.6, 0.68), (0, 0, 1))
bpy.context.view_layer.update()
# the phone is in the hand: put the lens just past the fingertips so the hand stays out of frame
# search lens positions near the phone hand: the wrist must be out of frame, the elbow inside it near the
# bottom-left corner (sleeve fills the corner), head about 0.6 away
from bpy_extras.object_utils import world_to_camera_view
cam = scene.camera; cam.data.lens = 16
scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
TARGET = H + Vector((0, 0, -0.32))
def place(c):
    cam.location = c
    q = (TARGET - c).to_track_quat("-Z", "Y")
    cam.rotation_euler = (q @ Matrix.Rotation(math.radians(-13), 4, "Z").to_quaternion()).to_euler()
tip = arm.matrix_world @ arm.pose.bones["Hand.P"].tail
wrist = arm.matrix_world @ arm.pose.bones["Hand.P"].head
elbow = arm.matrix_world @ arm.pose.bones["LowerArm.P"].head
def inside(v):
    return v.z > 0 and 0 <= v.x <= 1 and 0 <= v.y <= 1
best = None
for dx in (-0.2, -0.14, -0.08, -0.02, 0.04):
    for dy in (-0.05, 0.02, 0.09, 0.16, 0.24, 0.32, 0.4, 0.48):
        for dz in (-0.1, -0.03, 0.04, 0.11, 0.18, 0.25):
            c = tip + Vector((dx, dy, dz)); d = (c - H).length
            if not 0.62 < d < 0.95:
                continue
            place(c); bpy.context.view_layer.update()
            w, e = world_to_camera_view(scene, cam, wrist), world_to_camera_view(scene, cam, elbow)
            if inside(w) or inside(world_to_camera_view(scene, cam, tip)) or not inside(e):
                continue
            score = e.x + e.y + abs(d - 0.75)
            if best is None or score < best[0]:
                best = (score, c.copy(), (round(e.x, 2), round(e.y, 2)), round(d, 2))
CAM = best[1] if best else tip + Vector((-0.12, 0.34, -0.06))
print("cam search", best and best[2:])
aim("Head", (0.12, 0.08, 0.99), (Vector(CAM) - H).normalized())
aim("UpperArm.N", (-0.25, 0.1, -1))
aim("LowerArm.N", (-0.1, 0.25, -1))
aim("Hand.N", (-0.1, 0.25, -1))
aim("UpperLeg.P", (0.08, 0.05, -1)); aim("UpperLeg.N", (-0.1, -0.05, -1))
bpy.context.view_layer.update()
H = arm.matrix_world @ ((arm.pose.bones["Head"].head + arm.pose.bones["Head"].tail) / 2)

def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree, m.node_tree.nodes["Principled BSDF"]

# ---------------------------------------------------------------- floor: worn concrete + yellow bay lines
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object; floor.name = "Floor"
m, nt, b = node_mat("Concrete"); N = nt.nodes.new; L = nt.links.new
tc = N("ShaderNodeTexCoord")
noise = N("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 3; noise.inputs["Detail"].default_value = 12
grit = N("ShaderNodeTexNoise"); grit.inputs["Scale"].default_value = 180
crete = N("ShaderNodeValToRGB")
crete.color_ramp.elements[0].color = (0.035, 0.035, 0.034, 1); crete.color_ramp.elements[1].color = (0.2, 0.195, 0.185, 1)
mp = N("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, 0, math.radians(32))
lines = []
for axis, period, width in (("X", 2.6, 0.16), ("Y", 5.5, 0.16)):
    sx = N("ShaderNodeSeparateXYZ")
    mod = N("ShaderNodeMath"); mod.operation = "PINGPONG"; mod.inputs[1].default_value = period / 2
    th = N("ShaderNodeMath"); th.operation = "LESS_THAN"; th.inputs[1].default_value = width / 2
    L(mp.outputs[0], sx.inputs[0]); L(sx.outputs[axis], mod.inputs[0]); L(mod.outputs[0], th.inputs[0])
    lines.append(th)
L(tc.outputs["Object"], mp.inputs["Vector"])
both = N("ShaderNodeMath"); both.operation = "MAXIMUM"; L(lines[0].outputs[0], both.inputs[0]); L(lines[1].outputs[0], both.inputs[1])
wear = N("ShaderNodeMath"); wear.operation = "MULTIPLY"; L(both.outputs[0], wear.inputs[0])
wearn = N("ShaderNodeMapRange"); wearn.inputs["From Min"].default_value = 0.35; wearn.inputs["From Max"].default_value = 0.55
L(tc.outputs["Object"], noise.inputs["Vector"]); L(noise.outputs["Fac"], wearn.inputs["Value"]); L(wearn.outputs[0], wear.inputs[1])
mixc = N("ShaderNodeMix"); mixc.data_type = "RGBA"; mixc.inputs[7].default_value = (0.55, 0.38, 0.02, 1)
gm = N("ShaderNodeMath"); gm.operation = "MULTIPLY"; L(noise.outputs["Fac"], gm.inputs[0]); L(grit.outputs["Fac"], gm.inputs[1])
stain = N("ShaderNodeTexNoise"); stain.inputs["Scale"].default_value = 0.9; stain.inputs["Detail"].default_value = 6
L(tc.outputs["Object"], stain.inputs["Vector"])
gs = N("ShaderNodeMath"); gs.operation = "MULTIPLY"; L(gm.outputs[0], gs.inputs[0]); L(stain.outputs["Fac"], gs.inputs[1])
L(gs.outputs[0], crete.inputs["Fac"]); L(crete.outputs["Color"], mixc.inputs[6]); L(wear.outputs[0], mixc.inputs["Factor"])
L(mixc.outputs[2], b.inputs["Base Color"])
bump = N("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25
L(grit.outputs["Fac"], bump.inputs["Height"]); L(bump.outputs["Normal"], b.inputs["Normal"])
b.inputs["Roughness"].default_value = 0.85
floor.data.materials.append(m)

# ---------------------------------------------------------------- low wall, fence, posts behind the avatar
def box(name, size, loc, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    o.data.materials.append(mat); return o

m_wall, nt, b = node_mat("WallConcrete")
wn = nt.nodes.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = 6; wn.inputs["Detail"].default_value = 10
wr = nt.nodes.new("ShaderNodeValToRGB")
wr.color_ramp.elements[0].color = (0.07, 0.07, 0.07, 1); wr.color_ramp.elements[1].color = (0.22, 0.215, 0.205, 1)
nt.links.new(wn.outputs["Fac"], wr.inputs["Fac"]); nt.links.new(wr.outputs["Color"], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.9
back = Vector((0, -1.6, 0)); rot = (0, 0, math.radians(-18))
box("Wall", (12, 0.3, 1.1), back + Vector((0, 0, 0.55)), m_wall, rot)

m_metal, nt, b = node_mat("GalvanisedSteel")
b.inputs["Base Color"].default_value = (0.5, 0.5, 0.52, 1); b.inputs["Metallic"].default_value = 1; b.inputs["Roughness"].default_value = 0.45
R = Matrix.Rotation(rot[2], 4, "Z")
for i in range(-3, 4):
    p = back + (R @ Vector((i * 2.4, 0, 0)))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=3.2, location=p + Vector((0, 0, 2.6)))
    po = bpy.context.active_object; po.name = "Post"; po.data.materials.append(m_metal)
for z in (1.15, 2.6, 4.1):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=16, location=back + Vector((0, 0, z)), rotation=(0, math.radians(90), rot[2]))
    ra = bpy.context.active_object; ra.name = "Rail"; ra.data.materials.append(m_metal)

# chain-link: two diagonal line sets used as alpha on a plane
bpy.ops.mesh.primitive_plane_add(size=1, location=back + Vector((0, 0.02, 2.65)), rotation=(math.radians(90), 0, rot[2]))
fence = bpy.context.active_object; fence.name = "Fence"; fence.scale = (16, 3.0, 1)
m_f, nt, b = node_mat("ChainLink"); N = nt.nodes.new; L = nt.links.new
b.inputs["Base Color"].default_value = (0.55, 0.56, 0.58, 1); b.inputs["Metallic"].default_value = 1; b.inputs["Roughness"].default_value = 0.4
tc = N("ShaderNodeTexCoord"); sxyz = N("ShaderNodeSeparateXYZ"); L(tc.outputs["Object"], sxyz.inputs[0])
ws = []
for sgn in (1, -1):
    s1 = N("ShaderNodeMath"); s1.operation = "MULTIPLY"; s1.inputs[1].default_value = 16 * sgn
    s2 = N("ShaderNodeMath"); s2.operation = "MULTIPLY"; s2.inputs[1].default_value = 3.0
    ad = N("ShaderNodeMath"); ad.operation = "ADD"
    pp = N("ShaderNodeMath"); pp.operation = "PINGPONG"; pp.inputs[1].default_value = 0.03
    th = N("ShaderNodeMath"); th.operation = "LESS_THAN"; th.inputs[1].default_value = 0.004
    L(sxyz.outputs["X"], s1.inputs[0]); L(sxyz.outputs["Y"], s2.inputs[0]); L(s1.outputs[0], ad.inputs[0]); L(s2.outputs[0], ad.inputs[1])
    L(ad.outputs[0], pp.inputs[0]); L(pp.outputs[0], th.inputs[0]); ws.append(th)
mx = N("ShaderNodeMath"); mx.operation = "MAXIMUM"; L(ws[0].outputs[0], mx.inputs[0]); L(ws[1].outputs[0], mx.inputs[1])
L(mx.outputs[0], b.inputs["Alpha"])
fence.data.materials.append(m_f)

# cardboard boxes, back right
m_cb, nt, b = node_mat("Cardboard")
b.inputs["Base Color"].default_value = (0.42, 0.28, 0.14, 1); b.inputs["Roughness"].default_value = 0.8
m_tape, _, bt = node_mat("Tape"); bt.inputs["Base Color"].default_value = (0.05, 0.12, 0.45, 1)
for loc, size, rz in (((-0.7, -0.55, 0.13), (0.42, 0.3, 0.26), 12), ((-0.42, -0.85, 0.1), (0.36, 0.27, 0.2), -20), ((-0.72, -0.58, 0.36), (0.32, 0.24, 0.2), 30)):
    bx = box("Box", size, loc, m_cb, (0, 0, math.radians(rz)))
    tp = box("Tape", (size[0] + 0.005, 0.06, size[2] + 0.005), loc, m_tape, (0, 0, math.radians(rz)))

# ---------------------------------------------------------------- overcast top light, cool fill, haze-like world
def light(name, loc, energy, size, color, target):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size; ld.color = color
    o = bpy.data.objects.new(name, ld); scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o

# one soft key from the open side above the camera, a faint cool rim; everything else falls off dark
light("Key", H + Vector((0.5, 1.0, 1.6)), 70, 1.6, (0.92, 0.96, 1.0), H).data.spread = math.radians(55)
light("Rim", H + Vector((-1.0, -1.2, 0.9)), 110, 0.8, (0.72, 0.82, 1.0), H)
light("Bounce", Vector((0, 0.6, 0.05)), 6, 1.5, (1.0, 0.85, 0.55), H)
world = scene.world; wnt = world.node_tree
wnt.nodes["Background"].inputs["Color"].default_value = (0.5, 0.53, 0.58, 1)
wnt.nodes["Background"].inputs["Strength"].default_value = 0.06
haze = wnt.nodes.get("Haze") or wnt.nodes.new("ShaderNodeVolumeScatter"); haze.name = "Haze"
haze.inputs["Density"].default_value = 0.004
wnt.links.new(haze.outputs[0], wnt.nodes["World Output"].inputs["Volume"])

# ---------------------------------------------------------------- wide high selfie camera with a dutch tilt
place(CAM)
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.0; cam.data.dof.focus_distance = (CAM - H).length

scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
for dev in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = dev; break
    except TypeError:
        continue
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type != "CPU"
scene.cycles.device = "GPU"; scene.cycles.samples = 128; scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Punchy"
scene.view_settings.exposure = -0.2
scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
print("garage staged; head", tuple(round(v, 2) for v in H), "cam dist", round((CAM - H).length, 2))
