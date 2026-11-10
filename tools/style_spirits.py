"""Plan A, Spirit Procession (sttvr_l1ght new avatar, 2026-11-02): night pine-forest path, she walks toward the camera
and glances back over her right shoulder at faint cyan spirits drifting in the mist screen-left; moon shafts through
the canopy, low warm candle in her right hand. Teal-black grade. Run via run_halloween.py -- spirits."""
import math, random, sys
import bpy
from mathutils import Vector

sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import importlib, gfx_kit as k, halloween_kit as h, halloween_v2 as v2
importlib.reload(k); importlib.reload(h); importlib.reload(v2)

scene = bpy.context.scene
OUT = globals().get("OUT"); PCT = globals().get("PCT", 50); SAMPLES = globals().get("SAMPLES", 64)
rnd = random.Random(7)
h.keep_only_avatar(); v2.avatar_materials()
import forest_kit as fk; fk.avatar_polish()
scene.render.resolution_x = scene.render.resolution_y = 1080

# ---- pose: mid-stride walking toward +Y, torso counter-twist, head turned ~50 deg to her right (+X) and slightly down
A = k.aim; k.reset_pose()

def part_hair(width=0.62, top=0.78, depth=0.02):
    """Open the face: delete hair-mesh faces that hang in front of the face plate (rest pose, avatar faces +Y).
    Box = middle `width` of the head, from the chin up to `top` of the head height, in front of the face."""
    import bmesh
    k.upd(); hd = k.head_obj(); pts = [hd.matrix_world @ Vector(c) for c in hd.bound_box]
    x0, x1 = min(p.x for p in pts), max(p.x for p in pts); z0, z1 = min(p.z for p in pts), max(p.z for p in pts)
    front = max(p.y for p in pts); cx = (x0 + x1) / 2; hw = (x1 - x0) * width / 2; ztop = z0 + (z1 - z0) * top
    gone = 0
    for o in k.arm().children_recursive:
        if o.type != "MESH" or o == hd or o.parent_bone != "Head":
            continue
        bm = bmesh.new(); bm.from_mesh(o.data); mw = o.matrix_world
        kill = [f for f in bm.faces if (lambda c: abs(c.x - cx) < hw and z0 - 0.02 < c.z < ztop and c.y > front - depth)(mw @ f.calc_center_median())]
        gone += len(kill); bmesh.ops.delete(bm, geom=kill, context="FACES"); bm.to_mesh(o.data); bm.free()
    print("part_hair removed faces:", gone)
part_hair()
A("LowerTorso", (0, 0.1, 1), (-0.5, 0.87, 0)); A("UpperTorso", (0.06, 0.12, 1), (-0.05, 1, 0))
A("Head", (0.06, -0.02, 1), (0.42, 1, 0.12))
A("UpperLeg.N", (0, 0.32, -0.95)); A("LowerLeg.N", (0, 0.05, -1))
A("UpperLeg.P", (0, -0.22, -0.97)); A("LowerLeg.P", (0, -0.4, -0.92))
A("UpperArm.P", (0.15, 0.3, -0.94)); A("LowerArm.P", (-0.05, 0.95, -0.25)); A("Hand.P", (-0.05, 0.95, -0.25), (1, 0, 0))
A("UpperArm.N", (-0.25, -0.5, -0.83)); A("LowerArm.N", (-0.15, -0.45, -0.88)); A("Hand.N", (-0.15, -0.45, -0.88))
k.upd()
a = k.arm()
def zrange():
    dg = bpy.context.evaluated_depsgraph_get(); zs = []
    for o in a.children_recursive:
        if o.type == "MESH" and not o.hide_render:
            e = o.evaluated_get(dg); zs += [(e.matrix_world @ v.co).z for v in e.data.vertices]
    return min(zs), max(zs)
lo_z, hi_z = zrange(); a.location.z -= lo_z; k.upd(); print("avatar z", [round(v, 2) for v in zrange()])

# ---- chin point for the under-chin uplight (candle stays at the chest)
hd = k.head_obj(); hp = [hd.matrix_world @ Vector(c) for c in hd.bound_box]
fwd = Vector((0.42, 1, 0)).normalized(); Hc = k.head_center()
chin = Vector((Hc.x, Hc.y, min(p.z for p in hp))) + fwd * 0.16

# ---- candle in the right hand (held low, in front of the hip)
hand = a.matrix_world @ a.pose.bones["Hand.P"].tail
wax = k.material("Wax", (0.85, 0.8, 0.7), 0.5)
bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.11, location=hand + Vector((0, 0.01, 0.05)))
c = bpy.context.active_object; c.name = "Candle"; c.data.materials.append(wax)
flame = hand + Vector((0, 0.01, 0.13))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=flame); fl = bpy.context.active_object; fl.name = "CandleFlame"
fl.scale = (1, 1, 1.8); fl.data.materials.append(h.emissive("FlameM", (1, 0.5, 0.12), 25)); fl.visible_shadow = False

# ---- set: dark forest floor path, pine-ish gnarled trees (tall, dense), roots
bark = v2.bark_mat(tint=(0.08, 0.07, 0.07))
v2.ground(tex="forest_ground_04", tint=(0.22, 0.27, 0.27), disp=0.06)
needle = k.material("Needles", (0.012, 0.022, 0.018), 0.85)
def pine(name, x, y, hgt):
    """Conifer silhouette: bark trunk + 8 stacked drooping cone tiers with cloud displacement for ragged needle edges."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.06 * hgt / 9, depth=hgt, location=(x, y, hgt / 2))
    t = bpy.context.active_object; t.name = name + "Trunk"; t.data.materials.append(bark)
    tx = bpy.data.textures.new(name + "n", "CLOUDS"); tx.noise_scale = 0.12
    for j in range(8):
        f = j / 8; r = (1 - f) * 0.24 * hgt + 0.1; z = hgt * (0.42 + 0.55 * f)
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=r, radius2=0.02, depth=r * 1.1, location=(x, y, z))
        c = bpy.context.active_object; c.name = name; c.data.materials.append(needle)
        c.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
        s = c.modifiers.new("s", "SUBSURF"); s.levels = 2
        d = c.modifiers.new("d", "DISPLACE"); d.texture = tx; d.strength = r * 0.35
import forest_kit as fk; importlib.reload(fk)
# real Poly Haven conifers (linked instances), roots, stumps, moss and ferns; the camera is on +X/+Y so screen-left = +X
TREES = [(-2.6, 4.5), (2.4, 3.6), (-0.9, 6.5), (3.6, 7.5), (-3.8, 9), (1.2, 11), (-2.0, 13), (5.0, 12),
         (-5.5, 15), (0.0, 17), (3.0, 19), (-1.5, 22), (6.5, 18), (-7, 20), (8, 9), (-6, 6)]
for i, (x, d) in enumerate(TREES):
    fk.place("plants", "pine_tree_01" if i % 3 else "fir_tree_01", (x, -d, 0), height=rnd.uniform(11, 16), rot_z=rnd.uniform(0, 360))
    if i < 7:
        fk.place("plants", "pine_roots", (x, -d, 0), scale=rnd.uniform(0.9, 1.2), rot_z=rnd.uniform(0, 360))
for x, d, s in [(-1.6, 2.2, 1.0), (3.0, 5.5, 0.8)]:
    fk.place("plants", "tree_stump_01", (x, -d, 0), scale=s, rot_z=rnd.uniform(0, 360))
fk.place("plants", "dead_tree_trunk", (1.8, -4.8, 0), scale=1.0, rot_z=70)
for i in range(26):
    x = rnd.uniform(-4, 6); d = rnd.uniform(-1.5, 9)
    if abs(x) < 0.8 and d < 2: continue
    fk.place("plants", "fern_02", (x, -d, 0), height=rnd.uniform(0.4, 0.8), rot_z=rnd.uniform(0, 360))
for i in range(10):
    x, d = rnd.uniform(-4, 1.0), rnd.uniform(0, 8)  # keep moss out of the spirits' glow (screen-left = +X)
    fk.place("plants", "moss_01", (x, -d, 0), scale=rnd.uniform(0.8, 1.5), rot_z=rnd.uniform(0, 360))
fk.tint_model(fk._cache["moss_01"][0], (0.35, 0.4, 0.38)); fk.tint_model(fk._cache["fern_02"][0], (0.45, 0.55, 0.5))
# needle silhouettes inside the frame: saplings and low-branched firs in the mid ground, between the spirits
for x, d, hh in [(0.6, 5.2, 3.2), (3.4, 9.5, 4.5), (-0.6, 9.0, 3.8), (5.5, 7.0, 4.0), (2.0, 13.5, 5.0), (7.0, 14, 5.5)]:
    fk.place("plants", "pine_sapling_medium", (x, -d, 0), height=hh, rot_z=rnd.uniform(0, 360))

# ---- spirits: hooded wraith forms, emission + transparency fading toward the hem, screen-left (world +X) behind her
def spirit_mat():
    """Glowing smoke: volume emission only (surface fully transparent), density = noise x upward gradient, so the
    form has no hard outline and dissolves toward the hem."""
    m = bpy.data.materials.new("SpiritM"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tr = N.new("ShaderNodeBsdfTransparent"); vol = N.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.25, 0.85, 1.0, 1); vol.inputs["Emission Color"].default_value = (0.2, 0.85, 1.0, 1)
    vol.inputs["Emission Strength"].default_value = 3.5
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.05; ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 0.8; ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 8.0
    nr = N.new("ShaderNodeValToRGB"); nr.color_ramp.elements[0].position = 0.3; nr.color_ramp.elements[1].position = 0.6
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; sc = N.new("ShaderNodeMath"); sc.operation = "MULTIPLY"; sc.inputs[1].default_value = 1.8
    L.new(tc.outputs["Generated"], sep.inputs[0]); L.new(sep.outputs["Z"], ramp.inputs[0])
    L.new(tc.outputs["Object"], nz.inputs["Vector"]); L.new(nz.outputs["Fac"], nr.inputs[0])
    L.new(ramp.outputs["Color"], mul.inputs[0]); L.new(nr.outputs["Color"], mul.inputs[1]); L.new(mul.outputs[0], sc.inputs[0])
    L.new(sc.outputs[0], vol.inputs["Density"]); L.new(sc.outputs[0], vol.inputs["Emission Strength"])
    L.new(tr.outputs[0], out.inputs["Surface"]); L.new(vol.outputs[0], out.inputs["Volume"]); return m

sm = spirit_mat()
def spirit(name, loc, hgt, lean, rot_z):
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.3 * hgt / 1.9, radius2=0.16 * hgt / 1.9, depth=hgt * 0.8,
                                    location=Vector(loc) + Vector((0, 0, hgt * 0.4 + 0.15)))
    body = bpy.context.active_object; body.name = name
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15 * hgt / 1.9, location=Vector(loc) + Vector((0, 0.02, hgt * 0.86 + 0.15)))
    hd = bpy.context.active_object; hd.scale = (1, 1, 1.25)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2 * hgt / 1.9, location=Vector(loc) + Vector((0, 0, hgt * 0.72 + 0.15)))
    sh = bpy.context.active_object; sh.scale = (1.5, 0.75, 0.55)
    for o in (body, hd, sh):
        o.select_set(True)
    bpy.context.view_layer.objects.active = body; bpy.ops.object.join()
    sub = body.modifiers.new("s", "SUBSURF"); sub.levels = 2
    tx = bpy.data.textures.new(name + "t", "CLOUDS"); tx.noise_scale = 0.35
    dp = body.modifiers.new("d", "DISPLACE"); dp.texture = tx; dp.strength = 0.22
    body.rotation_euler = (math.radians(lean), 0, math.radians(rot_z))
    body.data.materials.append(sm); body.visible_shadow = False
    for attr in ("visible_diffuse", "visible_glossy"):
        setattr(body, attr, False)
    return body

# ---- camera: front three-quarter from her right, slightly below the eye, 85 mm, mid-thigh up (fixed distance, then shift)
H0 = k.head_center(); cam = scene.camera; cam.data.clip_end = 300; cam.data.shift_x = cam.data.shift_y = 0
k.place_camera(H0 + Vector((0.42, 1, -0.1)).normalized() * 3.5, H0 - Vector((0, 0, 0.4)), 85)
for _ in range(6):
    x, y, _d = k.project(H0); cam.data.shift_x += x - 0.64; cam.data.shift_y -= y - 0.25; k.upd()
cam.data.dof.focus_distance = (H0 - cam.location).length; print("frame", k.measure(), "dist", round(cam.data.dof.focus_distance, 2))

# spirits placed by frame position: ray from the lens to a target depth behind her, standing on the ground
def at_frame(fx, depth):
    q = cam.matrix_world.to_quaternion(); f = cam.data.lens / cam.data.sensor_width
    d = q @ Vector(((fx - 0.5 + cam.data.shift_x) / f, 0, -1)); d.z = 0; d.normalize()
    p = cam.location + d * depth; return Vector((p.x, p.y, 0))
SPIRITS = [("Spirit1", 0.14, 7.5, 1.9, -14, 25), ("Spirit2", 0.33, 10.5, 1.8, 12, 15),
           ("Spirit3", 0.05, 13.5, 2.0, -10, 30), ("Spirit4", 0.45, 16, 1.7, 15, 10)]
for nm, fx, dep, hg, ln, rz in SPIRITS:
    p = at_frame(fx, dep); spirit(nm, p, hg, ln, rz); print("proj", nm, [round(v, 2) for v in k.project(p + Vector((0, 0, hg * 0.6)))])

# ---- atmosphere: near-black teal world, height-faded blue mist, faint motes
k.world((0.004, 0.012, 0.016), strength=1.0)
h.fog("Mist", (0, -8, 3.0), (40, 34, 7.0), 0.028, color=(0.55, 0.75, 0.85), aniso=0.7, noise=1.8, fade_height=True)
h.fog("ShaftAir", (0, -10, 8.0), (40, 34, 16.0), 0.004, color=(0.75, 0.85, 0.95), aniso=0.75)

# ---- lights: moon shafts (narrow spots through the canopy), cold rim on hair, spirit cyan back glow, candle key
for o in [o for o in scene.objects if o.type == "LIGHT"]:
    bpy.data.objects.remove(o, do_unlink=True)
H = k.head_center()
def spot(name, loc, target, energy, angle, color, beam=True):
    d = bpy.data.lights.new(name, "SPOT"); d.energy = energy; d.color = color; d.spot_size = math.radians(angle); d.spot_blend = 0.6
    d.shadow_soft_size = 0.05; o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    if not beam:
        return
    # visible god ray: a long volume-only cylinder along the beam (scatter lit by the spot + faint self glow)
    v = Vector(target) - Vector(loc); L = v.length * 0.95; r = math.tan(math.radians(angle / 2)) * L * 0.55
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=r, radius2=r * 0.15, depth=L, location=Vector(loc) + v * 0.5)
    b = bpy.context.active_object; b.name = name + "Beam"; b.rotation_euler = v.to_track_quat("-Z", "Y").to_euler()
    bm = bpy.data.materials.new(name + "BeamM"); bm.use_nodes = True; N = bm.node_tree.nodes; N.clear()
    pv = N.new("ShaderNodeVolumePrincipled"); pv.inputs["Density"].default_value = 0.05; pv.inputs["Anisotropy"].default_value = 0.6
    pv.inputs["Emission Color"].default_value = (0.7, 0.85, 1.0, 1); pv.inputs["Emission Strength"].default_value = 0.6
    ou = N.new("ShaderNodeOutputMaterial"); bm.node_tree.links.new(pv.outputs[0], ou.inputs["Volume"])
    b.data.materials.append(bm); b.visible_shadow = False
spot("MoonShaft1", (-4, -16, 16), (2.0, -9, 0), 90000, 6, (0.7, 0.85, 1.0))
spot("MoonShaft2", (-3, -8, 15), (-0.4, -1.0, 0), 14000, 5, (0.7, 0.85, 1.0), beam=False)
spot("MoonShaft3", (-6, -20, 16), (5.0, -14, 0), 75000, 5, (0.7, 0.85, 1.0))
spot("MoonShaft4", (-2, -12, 17), (3.2, -6.5, 0), 60000, 4, (0.7, 0.85, 1.0))
r = H + Vector((-0.8, -1.6, 1.3)); k.area("MoonRim", r, H, 22 * (r - H).length_squared, 0.6, (0.6, 0.82, 1.0), 90)
k.area("DeepGlow", Vector((1.5, -26, 3.5)), Vector((1.5, 0, 2.5)), 2500, 14, (0.45, 0.75, 0.9), 160)
s = H + Vector((1.2, -1.8, 0.2)); k.area("SpiritGlow", s, H, 18 * (s - H).length_squared, 1.2, (0.45, 0.9, 1.0), 120)
ld = bpy.data.lights.new("CandleL", "POINT"); ld.energy = 40; ld.color = (1.0, 0.55, 0.2); ld.shadow_soft_size = 0.01
lo = bpy.data.objects.new("CandleL", ld); scene.collection.objects.link(lo); lo.location = flame + Vector((0, 0.03, 0))
f = H + Vector((0.6, 1.6, -0.3)); k.area("CoolFill", f, H, 2.5 * (f - H).length_squared, 1.5, (0.55, 0.7, 0.9), 150)
# torch-under-the-chin look with the candle kept at the chest: a hidden warm light just under the chin aims up the face
up = chin + fwd * 0.04 - Vector((0, 0, 0.05))
k.area("CandleUp", up, H, 1.1, 0.06, (1.0, 0.5, 0.16), 120)
bpy.data.objects["CandleUp"].visible_camera = False

v2.lint(("Spirit", "Tree", "Candle"))
k.setup_cycles(SAMPLES, look="AgX - Punchy", exposure=0.0, dof_fstop=3.5)
scene.cycles.volume_bounces = 1
bpy.ops.wm.save_as_mainfile(filepath=OUT + "_scene.blend", copy=True)
k.render(OUT + ".png", PCT, SAMPLES); print("RENDERED", OUT + ".png")
