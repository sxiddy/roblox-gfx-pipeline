"""Heartbreak Bedroom GFX for P00TSE (concept 1). Stage functions run in Blender via bl.py.
POSE PLAN: tripod camera, 3/4 from avatar's front-left, eye level of seated head, 50mm, head_frac ~0.26, head in upper third.
Seated on bed hugging knees: thighs forward+up, shins back+down, both forearms wrapped across shins, torso leans forward,
head tilted onto the near shoulder, face to lens. Cut at feet/shins by frame bottom."""
import sys, importlib, math
sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import bpy
from mathutils import Vector
import gfx_kit as k; importlib.reload(k)
ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"

def stage_avatar():
    bpy.ops.wm.save_as_mainfile(filepath=ROOT + r"\gfx_output\_session_backup_garage.blend", copy=True)
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.armatures, bpy.data.lights, bpy.data.cameras):
        for d in list(coll):
            if d.users == 0: coll.remove(d)
    G = {"__name__": "bx", "AVATAR_DIR": ROOT + r"\avatars\P00TSE", "POSE": "idle", "MIRROR_LEG": "P"}
    exec(open(ROOT + r"\tools\build_exact_gfx.py", encoding="utf-8").read(), G)
    print("skinned", k.skin_clothes())

def stage_pose():
    k.apply_pose("sit")
    k.aim("LowerTorso", (0, 0.15, 1)); k.aim("UpperTorso", (0.04, 0.3, 0.95), (0.2, 1, 0))
    k.aim("Head", (0.2, 0.12, 0.97), (0.3, 1, 0.2))
    k.aim("UpperLeg.P", (0.12, 0.8, 0.55)); k.aim("LowerLeg.P", (0.0, -0.3, -0.95)); k.aim("Foot.P", (0, 0.9, -0.2), (0, 0, 1))
    k.aim("UpperLeg.N", (-0.12, 0.8, 0.55)); k.aim("LowerLeg.N", (0.0, -0.3, -0.95)); k.aim("Foot.N", (0, 0.9, -0.2), (0, 0, 1))
    k.aim("UpperArm.P", (0.2, 0.35, -0.9)); k.aim("LowerArm.P", (-0.8, 0.5, 0.3)); k.aim("Hand.P", (-0.9, 0.3, 0.1), (0, 0, 1))
    k.aim("UpperArm.N", (-0.2, 0.35, -0.9)); k.aim("LowerArm.N", (0.8, 0.5, 0.3)); k.aim("Hand.N", (0.9, 0.3, 0.1), (0, 0, 1))
    k.upd()
    a = k.arm()
    for b in ("LowerTorso", "UpperLeg.P", "LowerLeg.P", "Foot.P", "Head", "LowerArm.P", "Hand.P"):
        print(b, tuple(round(x, 2) for x in a.matrix_world @ a.pose.bones[b].head))

def stage_camera(head_frac=0.26, head_xy=(0.5, 0.33), view_dir=(0.4, 1, 0.0), lens=50, roll=0):
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 1536, 1920
    if not sc.camera:
        cd = bpy.data.cameras.new("Cam"); co = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(co); sc.camera = co
    r = k.frame_head(head_frac, head_xy=head_xy, view_dir=view_dir, lens=lens, roll=roll)
    print(r); k.show_camera()

def quick(path):
    sc = bpy.context.scene; old = sc.render.engine; sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"
    sc.render.resolution_percentage = 40; sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    sc.render.engine = old

def stage_set():
    for n in [o.name for o in bpy.data.objects if o.name.startswith(("Floor", "Wall", "Candle", "Fairy", "TV", "Pillow", "Poster"))]:
        bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    a = k.arm(); a.rotation_euler[2] = math.radians(-90); a.location = (0.0, -0.15, 0.0); k.upd()
    bed = bpy.data.objects["GothicBed_01"]
    low = min((o.matrix_world @ Vector(c)).z for o in a.children for c in o.bound_box)
    a.location.z += 0.44 - low + 0.01; k.upd()
    # sheets dark
    for m in bed.data.materials:
        print("bedmat", m.name)
    k.plane("Floor", (9, 9), (0, 0, 0), k.pbr("weathered_brown_planks", 1.6, tint=(0.14, 0.12, 0.13)))
    wall = k.pbr("painted_plaster_wall", 1.2, tint=(0.14, 0.12, 0.17))
    k.plane("WallBack", (9, 4), (-1.7, 0, 2.0), wall, rot=(0, math.radians(90), 0))
    k.plane("WallSide", (9, 4), (0, -2.6, 2.0), wall, rot=(math.radians(90), 0, 0))
    k.cube("PillowA", (0.5, 0.32, 0.12), (-0.55, -0.55, 0.52), k.material("PillowMat", (0.04, 0.04, 0.05), 0.9), rot_z=0.4)
    k.cube("PillowB", (0.45, 0.3, 0.12), (-0.58, 0.45, 0.52), k.material("PillowMat2", (0.2, 0.05, 0.14), 0.9), rot_z=-0.3)
    # CRT TV on a crate beside the bed (camera-left), glowing screen
    r = k.import_model("electronics", "Television_01", loc=(0.9, 1.7, 0.0), rot_z=-135, scale=1.0)
    for o in r: o.name = "TV_" + o.name
    k.show_camera()

def _sphere(name, loc, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=16, ring_count=8)
    o = bpy.context.object; o.name = name; o.data.materials.append(mat); return o

def stage_light():
    for o in [o for o in bpy.data.objects if o.type == "LIGHT" or o.name.startswith(("Candle", "Fairy", "Screen"))]:
        bpy.data.objects.remove(o, do_unlink=True)
    # darken the bed sheets/wood: multiply the texture
    m = bpy.data.materials["GothicBed_01"]; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    if not nt.nodes.get("Dark"):
        src = b.inputs["Base Color"].links[0].from_socket
        mx = nt.nodes.new("ShaderNodeMix"); mx.name = "Dark"; mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
        mx.inputs[0].default_value = 1; mx.inputs[7].default_value = (0.16, 0.14, 0.2, 1)
        nt.links.new(src, mx.inputs[6]); nt.links.new(mx.outputs[2], b.inputs["Base Color"])
    H = k.head_center()
    tv = [o for o in bpy.data.objects if o.name.startswith("TV_")][0]; tv.location = (0.5, 1.3, 0); tv.rotation_euler[2] = math.radians(-120)
    print("tv proj", k.project(tv.location + Vector((0, 0, 0.3))))
    # CRT glow (blue) from the TV side, plus emissive screen plane
    k.area("CRTKey", Vector((0.3, 1.0, 0.75)), H, 90, 0.7, (0.3, 0.55, 1.0), 120)
    scr = k.plane("Screen", (0.3, 0.24), (0.38, 1.2, 0.3), k.material("ScreenMat", (0, 0, 0), 0.3, emit=(0.3, 0.55, 1.0), strength=6), rot=(math.radians(90), 0, math.radians(-30)))
    # candles right of the bed on the floor
    wax = k.material("Wax", (0.8, 0.75, 0.7), 0.5); fl = k.material("Flame", (1, 0.5, 0.15), 0.5, emit=(1, 0.5, 0.15), strength=30)
    for i, (x, y, h) in enumerate(((0.55, -1.15, 0.2), (0.8, -1.35, 0.13), (0.35, -1.45, 0.27))):
        k.cube("Candle%d" % i, (0.05, 0.05, h), (x, y, h / 2), wax); _sphere("CandleFlame%d" % i, (x, y, h + 0.03), 0.012, fl)
        ld = bpy.data.lights.new("CandleL%d" % i, "POINT"); ld.energy = 12; ld.color = (1, 0.55, 0.22); ld.shadow_soft_size = 0.02
        o = bpy.data.objects.new("CandleL%d" % i, ld); bpy.context.scene.collection.objects.link(o); o.location = (x, y, h + 0.05)
    # pink fairy lights strung on the back wall
    pk = k.material("FairyMat", (0, 0, 0), 0.3, emit=(1.0, 0.25, 0.6), strength=40)
    for i in range(22):
        t = i / 21; y = -2.2 + 4.4 * t; z = 2.15 - 0.45 * math.sin(math.pi * (t * 3 % 1)) * 0.6 - 0.2 * t
        _sphere("Fairy%d" % i, (-1.66, y, z), 0.016, pk)
    k.area("FairyGlow", Vector((-1.4, 0.2, 1.9)), H, 60, 1.8, (1.0, 0.3, 0.6), 150)
    k.area("RimWarm", H + Vector((-0.3, -1.4, 0.6)), H, 40, 0.5, (1.0, 0.55, 0.3), 120)
    k.area("Fill", H + Vector((2.0, 0.4, 0.4)), H, 8, 3.0, (0.5, 0.55, 0.9), 150)
    k.world((0.01, 0.01, 0.02), 1.0, haze=0.012)
    sc = bpy.context.scene
    k.setup_cycles(64, look="AgX - Punchy", exposure=0.0, dof_fstop=2.0)
    sc.camera.data.dof.focus_distance = (k.head_center() - sc.camera.location).length
    k.show_camera()

def _bbox(roots):
    ms = [o for r in roots for o in [r] + list(r.children_recursive) if o.type == "MESH"]
    vs = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    return Vector([min(v[i] for v in vs) for i in range(3)]), Vector([max(v[i] for v in vs) for i in range(3)])

def place(cat, name, x, y, z, rot=0, scale=1.0, tag="Dec"):
    """Import, scale, rotate about z around the group centre (roots use quaternion mode), then drop onto (x, y, z=bottom)."""
    from mathutils import Quaternion
    r = k.import_model(cat, name, loc=(0, 0, 0), rot_z=0, scale=scale)
    for o in r: o.name = tag + "_" + o.name
    bpy.context.view_layer.update()
    mn, mx = _bbox(r); c = (mn + mx) / 2; q = Quaternion((0, 0, 1), math.radians(rot))
    for o in r:
        o.rotation_mode = "QUATERNION"; o.rotation_quaternion = q @ o.rotation_quaternion
        o.location = c + q @ (o.location - c)
    bpy.context.view_layer.update()
    mn, mx = _bbox(r); c = (mn + mx) / 2
    for o in r: o.location += Vector((x - c.x, y - c.y, z - mn.z))
    bpy.context.view_layer.update(); return r

def stage_dress():
    for o in [o for o in bpy.data.objects if o.name.startswith(("Dec_", "Duvet", "Teddy"))]: bpy.data.objects.remove(o, do_unlink=True)
    for n in ("Floor", "WallBack", "WallSide"):
        o = bpy.data.objects[n]; o.data.materials[0] = k.pbr("wood_floor", 1.4, tint=(0.16, 0.13, 0.14)) if n == "Floor" else k.pbr("floral_jacquard", 1.0, tint=(0.2, 0.15, 0.22))
    # velvet duvet (foreground, camera-left) with soft rounded edges, and a teddy blanket roll behind her
    d = k.cube("Duvet", (1.3, 0.75, 0.16), (0.0, 0.62, 0.52), k.pbr("velour_velvet", 1.0, tint=(0.18, 0.1, 0.2)), rot_z=0.0)
    bv = d.modifiers.new("b", "BEVEL"); bv.width = 0.06; bv.segments = 4
    sd = d.modifiers.new("s", "SUBSURF"); sd.levels = 2
    t = k.cube("Teddy", (0.9, 0.3, 0.2), (-0.5, -0.35, 0.55), k.pbr("curly_teddy_natural", 1.0, tint=(0.12, 0.1, 0.12)), rot_z=0.2)
    bv = t.modifiers.new("b", "BEVEL"); bv.width = 0.08; bv.segments = 4; t.modifiers.new("s", "SUBSURF").levels = 2
    place("decorative", "throw_pillows_01", -0.5, 0.55, 0.5, rot=20)
    place("furniture", "side_table_01", -1.4, -1.0, 0.0, rot=0)
    st = _bbox([o for o in bpy.data.objects if o.name.startswith("Dec_side")]); top = st[1].z
    place("lighting", "desk_lamp_arm_01", -1.45, -0.85, top, rot=-60)
    place("decorative", "alarm_clock_01", -1.3, -1.2, top, rot=-80)
    place("decorative", "brass_candleholders", -1.28, -0.7, top, rot=0, scale=0.8)
    place("decorative", "ornate_mirror_01", -1.62, 0.7, 1.35, rot=90)
    place("decorative", "fancy_picture_frame_02", -1.62, -0.4, 1.7, rot=90)
    # hearts: tone down, slight pink
    for n in ("Handle1Mtl", "Handle2Mtl"):
        m = bpy.data.materials[n]; b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.75, 0.55, 0.65, 1)
        for nd in m.node_tree.nodes:
            if nd.type == "TEX_IMAGE" and b.inputs["Base Color"].links == () : pass
    # face: calmer
    L = bpy.data.lights
    if "FaceKey" in L: L["FaceKey"].energy = 12
    k.show_camera()

def darken(mat, rgb):
    nt = mat.node_tree; b = nt.nodes["Principled BSDF"]
    if nt.nodes.get("Tint"): nt.nodes["Tint"].inputs[7].default_value = (*rgb, 1); return
    ls = b.inputs["Base Color"].links
    mx = nt.nodes.new("ShaderNodeMix"); mx.name = "Tint"; mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1
    mx.inputs[7].default_value = (*rgb, 1)
    if ls: src = ls[0].from_socket; nt.links.new(src, mx.inputs[6])
    else: mx.inputs[6].default_value = b.inputs["Base Color"].default_value
    nt.links.new(mx.outputs[2], b.inputs["Base Color"])

def stage_dress2():
    for n in ("Duvet", "Teddy"):
        if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    for o in [o for o in bpy.data.objects if o.name.startswith(("Dec_ornate", "Dec_fancy"))]: bpy.data.objects.remove(o, do_unlink=True)
    place("decorative", "ornate_mirror_01", -1.62, 0.9, 0.95, rot=90)
    place("decorative", "fancy_picture_frame_02", -1.62, -0.3, 1.45, rot=90)
    for o in bpy.data.objects:
        if o.type != "MESH": continue
        for m in o.data.materials:
            if o.name.startswith("Dec_throw"): darken(m, (0.22, 0.18, 0.28))
            elif o.name.startswith("Dec_desk"): darken(m, (0.3, 0.25, 0.3))
            elif o.name.startswith("Dec_side"): darken(m, (0.5, 0.45, 0.45))
    for n in ("Handle1Mtl", "Handle2Mtl", "Handle3Mtl", "Handle4Mtl", "Handle5Mtl"):
        darken(bpy.data.materials[n], (0.62, 0.48, 0.58))
    k.show_camera()
