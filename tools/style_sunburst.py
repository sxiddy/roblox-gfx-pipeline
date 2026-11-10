"""Restage the rigged avatar scene (from build_exact_gfx.py) as a comic sunburst GFX, rendered in Cycles."""
import math
import bpy
from mathutils import Vector

scene = bpy.context.scene
for n in ("Backdrop", "Halo", "Key", "Fill", "RimPurple", "RimGold", "Sunburst"):
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o, do_unlink=True)

CAM = Vector((0.75, 2.5, 1.32))
TARGET = Vector((0, 0, 1.18))

# sunburst: flat emissive rays around the camera axis
bpy.ops.mesh.primitive_plane_add(size=9, location=Vector((0, 0, 1.5)) + (Vector((0, 0, 1.5)) - CAM).normalized() * 2.2)
sb = bpy.context.active_object; sb.name = "Sunburst"
sb.rotation_euler = (CAM - sb.location).to_track_quat("Z", "Y").to_euler()
m = bpy.data.materials.new("SunburstMat"); m.use_nodes = True
nt = m.node_tree; nt.nodes.clear()
N = lambda t: nt.nodes.new(t)
tc, sep = N("ShaderNodeTexCoord"), N("ShaderNodeSeparateXYZ")
ang = N("ShaderNodeMath"); ang.operation = "ARCTAN2"
rays = N("ShaderNodeMath"); rays.operation = "MULTIPLY"; rays.inputs[1].default_value = 18 / math.pi
frac = N("ShaderNodeMath"); frac.operation = "PINGPONG"; frac.inputs[1].default_value = 1.0
step = N("ShaderNodeMath"); step.operation = "GREATER_THAN"; step.inputs[1].default_value = 0.5
mix = N("ShaderNodeMix"); mix.data_type = "RGBA"
mix.inputs[6].default_value = (0.0, 0.09, 0.75, 1); mix.inputs[7].default_value = (0.0, 0.35, 1.0, 1)
dist = N("ShaderNodeVectorMath"); dist.operation = "LENGTH"
vig = N("ShaderNodeMapRange"); vig.inputs["From Min"].default_value = 0.3; vig.inputs["From Max"].default_value = 3.6
vig.inputs["To Min"].default_value = 1.3; vig.inputs["To Max"].default_value = 0.15
em, out = N("ShaderNodeEmission"), N("ShaderNodeOutputMaterial")
L = nt.links.new
L(tc.outputs["Object"], sep.inputs[0]); L(sep.outputs["Y"], ang.inputs[0]); L(sep.outputs["X"], ang.inputs[1])
L(ang.outputs[0], rays.inputs[0]); L(rays.outputs[0], frac.inputs[0]); L(frac.outputs[0], step.inputs[0])
L(step.outputs[0], mix.inputs["Factor"]); L(mix.outputs[2], em.inputs["Color"])
L(tc.outputs["Object"], dist.inputs[0]); L(dist.outputs["Value"], vig.inputs["Value"]); L(vig.outputs[0], em.inputs["Strength"])
L(em.outputs[0], out.inputs["Surface"])
sb.data.materials.append(m)
sb.visible_shadow = False

def light(name, loc, energy, size, color):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size; ld.color = color
    o = bpy.data.objects.new(name, ld); scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (TARGET - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

light("Key", (1.6, 2.2, 2.2), 210, 1.6, (1.0, 0.96, 0.92))
light("Fill", (-1.8, 2.0, 1.2), 55, 2.0, (0.85, 0.92, 1.0))
light("Rim", (-0.6, -1.3, 2.2), 260, 0.8, (0.75, 0.9, 1.0))
light("RimR", (1.2, -1.0, 1.4), 140, 0.6, (1.0, 1.0, 1.0))

cam = scene.camera
cam.location = CAM
cam.rotation_euler = (TARGET - CAM).to_track_quat("-Z", "Y").to_euler()
cam.data.lens = 45
cam.data.dof.use_dof = False
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.25, 0.35, 0.5, 1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.4

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
scene.cycles.device = "GPU"
scene.cycles.samples = 160
scene.cycles.use_denoising = True
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.resolution_x = scene.render.resolution_y = 1080
print("sunburst staged on", prefs.compute_device_type, [d.name for d in prefs.devices if d.use])
