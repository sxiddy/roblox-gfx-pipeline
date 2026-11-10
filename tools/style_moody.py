"""Restage a rigged avatar (build_exact_gfx.py) as a moody night portrait:
leaning on a padded armrest, head tilted, moonlit starry sky, cold desaturated grade. Cycles."""
import math
import bpy
from mathutils import Matrix, Vector

scene = bpy.context.scene
arm = bpy.data.objects["Avatar"]
for n in ("Backdrop", "Halo", "Key", "Fill", "RimPurple", "RimGold", "Sunburst", "Rim", "RimR",
          "Sky", "Moon", "MoonGlow", "Armrest", "Moonlight", "FrontFill", "BackRim"):
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o, do_unlink=True)

def aim(bone, d, hint=(0, 1, 0)):
    bpy.context.view_layer.update()
    pb = arm.pose.bones[bone]
    y = Vector(d).normalized()
    h = Vector(hint); z = (h - h.dot(y) * y).normalized(); x = y.cross(z)
    m = Matrix((x, y, z)).transposed().to_4x4(); m.translation = pb.head
    pb.matrix = m

for pb in arm.pose.bones:
    pb.matrix_basis = Matrix.Identity(4)
# lean forward onto folded forearms, head resting tilted
aim("LowerTorso", (0, 0.12, 1))
aim("UpperTorso", (0.04, 0.42, 0.9), (0, 1, -0.3))
aim("Head", (-0.3, 0.22, 0.93), (0.1, 1, 0))
aim("UpperArm.P", (0.22, 0.6, -0.77))
aim("LowerArm.P", (-0.88, 0.42, 0.02), (0, 0, 1))
aim("Hand.P", (-0.9, 0.35, 0.0), (0, 0, 1))
aim("UpperArm.N", (-0.2, 0.62, -0.76))
aim("LowerArm.N", (0.9, 0.38, 0.12), (0, 0, 1))
aim("Hand.N", (0.92, 0.3, 0.1), (0, 0, 1))
bpy.context.view_layer.update()

W = lambda b: arm.matrix_world @ arm.pose.bones[b].head
head_c = arm.matrix_world @ ((arm.pose.bones["Head"].head + arm.pose.bones["Head"].tail) / 2)
elbow_z = min(W("LowerArm.P").z, W("LowerArm.N").z)
fy = (W("LowerArm.P").y + W("LowerArm.N").y) / 2

def mat(name, color, rough=0.5, emit=None, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = strength
    return m

# padded armrest under the forearms
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, fy + 0.05, elbow_z - 0.16))
ar = bpy.context.active_object; ar.name = "Armrest"; ar.scale = (1.25, 0.34, 0.24)
bpy.ops.object.transform_apply(scale=True)
bv = ar.modifiers.new("Bevel", "BEVEL"); bv.width = 0.08; bv.segments = 6
sub = ar.modifiers.new("Sub", "SUBSURF"); sub.levels = sub.render_levels = 2
ar.data.shade_smooth()
fab = mat("Fabric", (0.012, 0.016, 0.03), 0.8)
nt = fab.node_tree; b = nt.nodes["Principled BSDF"]
b.inputs["Sheen Weight"].default_value = 0.15
wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 120
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.15
nt.links.new(wv.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
ar.data.materials.append(fab)

# night sky: gradient + star field + moon, on a big plane behind
CAM = head_c + Vector((0.42, 1.55, 0.12))
back = head_c + (head_c - CAM).normalized() * 6
bpy.ops.mesh.primitive_plane_add(size=16, location=back)
sky = bpy.context.active_object; sky.name = "Sky"
sky.rotation_euler = (CAM - back).to_track_quat("Z", "Y").to_euler()
m = bpy.data.materials.new("SkyMat"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
N = nt.nodes.new; L = nt.links.new
tc = N("ShaderNodeTexCoord"); sep = N("ShaderNodeSeparateXYZ")
grad = N("ShaderNodeMapRange"); grad.inputs["From Min"].default_value = -6; grad.inputs["From Max"].default_value = 6
ramp = N("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.004, 0.006, 0.012, 1); ramp.color_ramp.elements[1].color = (0.035, 0.05, 0.085, 1)
cloud = N("ShaderNodeTexNoise"); cloud.inputs["Scale"].default_value = 0.35; cloud.inputs["Detail"].default_value = 6
cmix = N("ShaderNodeMix"); cmix.data_type = "RGBA"; cmix.blend_type = "SCREEN"; cmix.inputs["Factor"].default_value = 0.08
vor = N("ShaderNodeTexVoronoi"); vor.feature = "DISTANCE_TO_EDGE" if False else "F1"; vor.inputs["Scale"].default_value = 40
star = N("ShaderNodeMapRange"); star.inputs["From Min"].default_value = 0.07; star.inputs["From Max"].default_value = 0.0
star.inputs["To Min"].default_value = 0; star.inputs["To Max"].default_value = 14
add = N("ShaderNodeMix"); add.data_type = "RGBA"; add.blend_type = "ADD"; add.inputs["Factor"].default_value = 1
em = N("ShaderNodeEmission"); out = N("ShaderNodeOutputMaterial")
L(tc.outputs["Object"], sep.inputs[0]); L(sep.outputs["Y"], grad.inputs["Value"]); L(grad.outputs[0], ramp.inputs["Fac"])
L(ramp.outputs["Color"], cmix.inputs[6]); L(tc.outputs["Object"], cloud.inputs["Vector"]); L(cloud.outputs["Color"], cmix.inputs[7])
L(tc.outputs["Object"], vor.inputs["Vector"]); L(vor.outputs["Distance"], star.inputs["Value"])
L(cmix.outputs[2], add.inputs[6]); L(star.outputs[0], add.inputs[7])
L(add.outputs[2], em.inputs["Color"]); L(em.outputs[0], out.inputs["Surface"])
sky.data.materials.append(m); sky.visible_shadow = False

# moon top-right of frame with a soft halo
right = (CAM - head_c).cross(Vector((0, 0, 1))).normalized() * -1
moon_pos = back + right * 1.9 + Vector((0, 0, 1.6)) + (CAM - back).normalized() * 0.05
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, location=moon_pos)
moon = bpy.context.active_object; moon.name = "Moon"; moon.data.shade_smooth()
moon.data.materials.append(mat("MoonMat", (1, 1, 1), emit=(0.85, 0.92, 1.0), strength=40))
moon.visible_shadow = False
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.3, location=moon_pos + (CAM - moon_pos).normalized() * -0.3)
glow = bpy.context.active_object; glow.name = "MoonGlow"; glow.visible_shadow = False
gm = bpy.data.materials.new("GlowMat"); gm.use_nodes = True; gn = gm.node_tree; gn.nodes.clear()
gv = gn.nodes.new("ShaderNodeVolumePrincipled"); gv.inputs["Density"].default_value = 0.0; gv.inputs["Emission Strength"].default_value = 0.35; gv.inputs["Emission Color"].default_value = (0.7, 0.82, 1.0, 1)
gn.links.new(gv.outputs[0], gn.nodes.new("ShaderNodeOutputMaterial").inputs["Volume"]); glow.data.materials.append(gm)

def light(name, loc, energy, size, color, target):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size; ld.color = color
    o = bpy.data.objects.new(name, ld); scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

light("Moonlight", head_c + right * 1.2 + Vector((0, -0.9, 1.4)), 320, 0.5, (0.75, 0.86, 1.0), head_c)
light("FrontFill", CAM + Vector((-0.4, 0.2, 0.3)), 18, 1.5, (0.55, 0.65, 0.9), head_c)
light("BackRim", head_c - right * 1.2 + Vector((0, -1.0, 0.6)), 140, 0.5, (0.7, 0.8, 1.0), head_c)

cam = scene.camera
cam.location = CAM
cam.rotation_euler = (head_c + Vector((0, 0, -0.06)) - CAM).to_track_quat("-Z", "Y").to_euler()
cam.data.lens = 50
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.2
cam.data.dof.focus_distance = (CAM - head_c).length
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.05, 0.11, 1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25

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
scene.cycles.device = "GPU"; scene.cycles.samples = 160; scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Base Contrast" if False else "AgX - Punchy"
scene.view_settings.exposure = 0.1
scene.render.resolution_x = scene.render.resolution_y = 1080
print("moody staged; head", tuple(round(v, 2) for v in head_c))
