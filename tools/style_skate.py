"""Graffiti skate spot at night for Qsi2408. Stage functions run in Blender via bl.py (exec'd into one namespace).

POSE PLAN: sits on a concrete skate ledge with the graffiti wall behind (-Y). Legs dangle over the front edge, knees
slightly apart, sneakers in frame. Right hand (.P, screen-left) rests on the right knee; left hand (.N, screen-right)
flat on the ledge top beside the hip. Torso upright with a small forward slouch, head tilted ~8 deg and turned a little
toward the lens.
CAMERA: tripod, 3/4 from front-left of the avatar (+X side), low (lens below the chin, looking up ~10 deg), 45mm, roll -4,
4:5 portrait 1080x1350, head ~0.30 of frame width centred at (0.5, 0.3), cut at the shins/sneakers.
SET: graffiti wall (QSI piece behind the head), concrete ledge with a steel grind edge, skateboard leaning on the ledge
at screen-right, spray cans on the ledge at screen-left, wet-ish asphalt.
LIGHT: hard purple neon rim from behind, soft cool key from the front, orange sodium streetlight wash on the wall.
GRADE: deep blacks, grain, slight chromatic aberration, purple tint.
"""
import sys, importlib, math, random
sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import bpy, bmesh
from mathutils import Vector
import gfx_kit as k; importlib.reload(k)

ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
OUT = ROOT + r"\gfx_output\Qsi2408"
LEDGE_H = 0.42


def stage_avatar():
    G = {"__name__": "bx", "AVATAR_DIR": ROOT + r"\avatars\Qsi2408", "POSE": "idle"}
    exec(open(ROOT + r"\tools\build_exact_gfx.py", encoding="utf-8").read(), G)
    for n in ("Backdrop", "Halo"):
        if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    print("skinned", k.skin_clothes())
    for o in sorted(bpy.data.objects, key=lambda o: o.name):
        if o.type == "MESH":
            m = o.data.materials[0].name if o.data.materials else "-"
            print(o.name, o.parent.name if o.parent else "-", o.parent_bone, tuple(round(d, 2) for d in o.dimensions), m)


def low(parts):
    return min((o.matrix_world @ Vector(c)).z for o in k.arm().children if o.name.split(".")[0] in parts for c in o.bound_box)


def stage_pose():
    k.apply_pose("sit")
    k.aim("LowerTorso", (0, 0.02, 1)); k.aim("UpperTorso", (0, 0.1, 1), (0.1, 1, 0))
    k.aim("Head", (-0.06, 0.06, 1), (0.3, 1, -0.05))
    # thighs forward, shins dangle down over the edge, feet a little apart
    k.aim("UpperLeg.P", (0.08, 1, -0.05)); k.aim("UpperLeg.N", (-0.1, 1, -0.05))
    k.aim("LowerLeg.P", (0.06, 0.15, -1)); k.aim("LowerLeg.N", (-0.1, 0.1, -1))
    k.aim("Foot.P", (0.06, 0.15, -1), (0, 1, 0)); k.aim("Foot.N", (-0.1, 0.1, -1), (0, 1, 0))
    # P hand on the P knee, N hand flat on the ledge beside the hip
    k.aim("UpperArm.P", (0.25, 0.45, -0.85)); k.aim("LowerArm.P", (0.05, 1, -0.3)); k.aim("Hand.P", (0.05, 1, -0.4), (0, 0, 1))
    k.aim("UpperArm.N", (-0.35, -0.1, -1)); k.aim("LowerArm.N", (-0.2, 0, -1)); k.aim("Hand.N", (-0.2, 0.1, -1), (0, 1, 0))
    k.upd(); a = k.arm()
    for b in ("Head", "Hand.P", "Hand.N", "Foot.P", "UpperLeg.P"):
        print(b, tuple(round(x, 2) for x in a.matrix_world @ a.pose.bones[b].head))


def img_mat(name, path, rough=0.85):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
    return m


def spray_wall():
    """Real concrete texture with the RGBA spray overlay mixed on top by its alpha (UV-mapped)."""
    m = k.pbr("concrete_layers_02", 0.8, tint=(0.2, 0.2, 0.22)); m.name = "SprayWall"; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; base = b.inputs["Base Color"].links[0].from_socket
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(OUT + r"\graffiti.png", check_existing=True); t.image.reload()
    uv = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(uv.outputs["UV"], t.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    nt.links.new(t.outputs["Alpha"], mix.inputs["Factor"]); nt.links.new(base, mix.inputs[6]); nt.links.new(t.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    return m


def build_board(loc, rot, L=0.62, W=0.155, T=0.013, kick_at=0.21, kick=0.42):
    """Popsicle deck: rounded nose/tail kicked toward +Y (grip side), maple edge, red underside graphic,
    trucks (baseplate, hanger, axle) and wheels on the -Y underside. Length along local Z, width along X."""
    bm = bmesh.new(); r = W / 2; zc = L / 2 - r; pts = []
    for i in range(13):  # nose arc
        t = math.pi * i / 12; pts.append((r * math.cos(t), zc + r * math.sin(t)))
    pts += [(-r, kick_at), (-r, 0), (-r, -kick_at)]
    for i in range(13):  # tail arc
        t = math.pi + math.pi * i / 12; pts.append((r * math.cos(t), -zc + r * math.sin(t)))
    pts += [(r, -kick_at), (r, 0), (r, kick_at)]
    lift = lambda z: max(0.0, abs(z) - kick_at) * kick
    bot = [bm.verts.new((x, lift(z), z)) for x, z in pts]
    top = [bm.verts.new((x, lift(z) + T, z)) for x, z in pts]
    fb = bm.faces.new(bot[::-1]); ft = bm.faces.new(top)
    n = len(pts); sides = [bm.faces.new((bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i])) for i in range(n)]
    bmesh.ops.triangulate(bm, faces=[fb, ft])
    me = bpy.data.meshes.new("Board"); bm.to_mesh(me); bm.free()
    sb = bpy.data.objects.new("Board", me); bpy.context.scene.collection.objects.link(sb)
    grip = k.material("Grip", (0.015, 0.015, 0.017), 0.95)
    graphic = k.material("DeckRed", (0.36, 0.04, 0.05), 0.45)
    maple = k.material("Maple", (0.55, 0.38, 0.22), 0.6)
    for m in (graphic, grip, maple): me.materials.append(m)
    for p in me.polygons:  # 0 underside, 1 grip, 2 edge
        p.material_index = 2 if abs(p.normal.y) < 0.5 else (1 if p.normal.y > 0 else 0)
        p.use_smooth = False
    sb.location = loc; sb.rotation_euler = tuple(math.radians(a) for a in rot)
    metal = k.material("Truck", (0.62, 0.63, 0.66), 0.28, 1.0)
    wheel = k.material("Wheel", (0.93, 0.92, 0.86), 0.45)
    def part(o, name, mat):
        o.name = name; o.data.materials.append(mat); o.parent = sb
    for zz in (-0.17, 0.17):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.006, zz)); bp = bpy.context.active_object
        bp.scale = (0.055, 0.012, 0.07); part(bp, "Baseplate", metal)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.014, depth=0.13, location=(0, -0.028, zz), rotation=(0, math.radians(90), 0))
        part(bpy.context.active_object, "Hanger", metal)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.004, depth=0.2, location=(0, -0.03, zz), rotation=(0, math.radians(90), 0))
        part(bpy.context.active_object, "Axle", metal)
        for dx in (-0.083, 0.083):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.027, depth=0.03, vertices=24, location=(dx, -0.03, zz), rotation=(0, math.radians(90), 0))
            w = bpy.context.active_object; part(w, "Wheel", wheel)
            bv = w.modifiers.new("bev", "BEVEL"); bv.width = 0.006; bv.segments = 3
    return sb


def wall_details(wy):
    """Precast panel seams, a drain pipe with brackets, a utility box and a grime band along the base."""
    groove = k.material("Seam", (0.012, 0.012, 0.014), 0.9)
    for x in (-3.0, -1.5, 0.0, 1.5, 3.0):
        k.cube("SeamV", (0.018, 0.012, 5.0), (x + 0.37, wy + 0.004, 2.5), groove)
    for z in (1.25, 2.6):
        k.cube("SeamH", (10, 0.012, 0.016), (0, wy + 0.004, z), groove)
    pipe = k.material("PipeMetal", (0.12, 0.13, 0.14), 0.45, 0.8)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=5.0, location=(1.25, wy + 0.08, 2.5))
    bpy.context.active_object.name = "Pipe"; bpy.context.active_object.data.materials.append(pipe)
    for z in (0.6, 1.6, 2.6):
        k.cube("Bracket", (0.11, 0.07, 0.025), (1.25, wy + 0.05, z), pipe)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.06, minor_radius=0.045, location=(1.25, wy + 0.14, 0.12), rotation=(0, math.radians(90), 0))
    bpy.context.active_object.name = "PipeElbow"; bpy.context.active_object.data.materials.append(pipe)
    box = k.material("UtilBox", (0.16, 0.17, 0.16), 0.55, 0.6)
    k.cube("UtilBox", (0.42, 0.14, 0.56), (-1.9, wy + 0.07, 1.4), box)  # clear of the head silhouette
    k.cube("UtilConduit", (0.04, 0.04, 1.3), (-1.9, wy + 0.03, 0.5), box)


def jeans(mul=0.38):
    """Own material for the legs: darker grey denim with a fine crease bump so the cargos stop reading as pale tubes."""
    src = bpy.data.materials["Player1Mtl"]
    m = bpy.data.materials.get("JeansMtl") or src.copy(); m.name = "JeansMtl"; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    if "JeansDark" not in nt.nodes:
        s = b.inputs["Base Color"].links[0].from_socket
        mix = nt.nodes.new("ShaderNodeMix"); mix.name = "JeansDark"; mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1; nt.links.new(s, mix.inputs[6]); nt.links.new(mix.outputs[2], b.inputs["Base Color"])
        tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.name = "Crease"
        wv.wave_type = "BANDS"; wv.bands_direction = "Z"; wv.inputs["Scale"].default_value = 9
        wv.inputs["Distortion"].default_value = 9; wv.inputs["Detail"].default_value = 3
        nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
        bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35
        nt.links.new(wv.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    nt.nodes["JeansDark"].inputs[7].default_value = (mul, mul, mul * 1.03, 1)
    b.inputs["Roughness"].default_value = 0.9; b.inputs["Specular IOR Level"].default_value = 0.15
    nt.nodes["Bump"].inputs["Strength"].default_value = 0.6
    for n in ("UpperLeg_P", "UpperLeg_N", "LowerLeg_P", "LowerLeg_N"):
        o = bpy.data.objects[n]; o.data.materials[0] = m


def stage_set():
    a = k.arm(); keep = set(a.children_recursive) | {a, bpy.context.scene.camera}
    for o in [o for o in bpy.context.scene.objects if o not in keep]:
        bpy.data.objects.remove(o, do_unlink=True)
    a.location = (0, 0, 0); k.upd()
    seat = low(("LowerTorso", "UpperLeg", "UpperLeg_P", "UpperLeg_N"))
    a.location.z += LEDGE_H - seat + 0.003; k.upd()
    back = min((o.matrix_world @ Vector(c)).y for o in a.children if o.name.split(".")[0] in ("LowerTorso", "UpperTorso") for c in o.bound_box)
    knee = min((a.matrix_world @ a.pose.bones[b].head).y for b in ("LowerLeg.P", "LowerLeg.N"))
    # asphalt ground, slightly glossy
    g = k.plane("Ground", (14, 14), (0, 2, 0), k.pbr("concrete_floor_02", 1.0, tint=(0.08, 0.08, 0.095)))
    bs = g.data.materials[0].node_tree.nodes["Principled BSDF"]
    for l in list(bs.inputs["Roughness"].links): g.data.materials[0].node_tree.links.remove(l)
    bs.inputs["Roughness"].default_value = 0.35
    # ledge: concrete block with steel grind edge on the front top
    conc = k.pbr("concrete_layers_02", 1.2, tint=(0.5, 0.5, 0.53))
    fy = knee - 0.05; depth = max(0.55, fy - back + 0.05); ly = fy - depth  # front edge just behind the knees
    k.cube("Ledge", (4.0, depth, LEDGE_H), (0, ly + depth / 2, LEDGE_H / 2), conc)
    steel = k.material("Steel", (0.5, 0.52, 0.55), 0.3, 1.0)
    k.cube("Coping", (4.0, 0.04, 0.03), (0, fy - 0.01, LEDGE_H + 0.004), steel)
    # graffiti wall 0.8 m behind the ledge, image faces +Y
    wy = ly - 0.8
    w = k.plane("Graffiti", (10, 5), (0, wy, 2.5), spray_wall(), rot=(90, 0, 180))
    k.cube("WallBlock", (10.2, 0.2, 5.2), (0, wy - 0.11, 2.6), k.material("WallDark", (0.05, 0.05, 0.055), 0.9))
    # skateboard leaning against the ledge front at screen-right (world -X), underside + wheels toward the lens
    build_board((-0.42, fy + 0.11, 0.31), (16, 0, 140))
    wall_details(wy)
    jeans()
    # spray cans on the ledge top at screen-left (world +X)
    for i, (x, c) in enumerate(((0.55, (0.55, 0.1, 0.9)), (0.66, (0.9, 0.08, 0.12)), (0.6, (0.1, 0.75, 0.85)))):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.15, location=(x, ly + 0.2 + 0.08 * i, LEDGE_H + 0.075))
        cn = bpy.context.active_object; cn.name = "Can"; cn.data.materials.append(k.material("Can%d" % i, c, 0.3, 0.6))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.02, location=(x, ly + 0.2 + 0.08 * i, LEDGE_H + 0.16))
        bpy.context.active_object.name = "Cap"; bpy.context.active_object.data.materials.append(k.material("CapW", (0.9, 0.9, 0.9), 0.4))
    # purple LED strip under the coping lip
    k.led_strip([(-2.0, fy + 0.01, LEDGE_H - 0.03), (2.0, fy + 0.01, LEDGE_H - 0.03)], color=(0.55, 0.1, 1.0), strength=6)
    print("ledge_back", round(ly, 3), "front", round(fy, 3), "wall", round(wy, 3), "seat", round(low(("LowerTorso", "UpperLeg_P", "UpperLeg_N")), 3))


def stage_camera(head_frac=0.30, view=(0.45, 1, -0.22), lens=45, roll=-4, head_xy=(0.5, 0.3)):
    sc = bpy.context.scene
    if not sc.camera:
        cd = bpy.data.cameras.new("Cam"); c = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(c); sc.camera = c
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1350
    print(k.frame_head(head_frac, head_xy=head_xy, view_dir=view, lens=lens, roll=roll))
    a = k.arm()
    for n, p in (("footP", a.matrix_world @ a.pose.bones["Foot.P"].tail), ("handP", a.matrix_world @ a.pose.bones["Hand.P"].tail),
                 ("board", bpy.data.objects["Board"].location), ("cans", bpy.data.objects["Can"].location)):
        print(n, [round(v, 2) for v in k.project(p)])
    try:
        k.show_camera("SOLID")
    except Exception as e:
        print("show_camera", e)


def stage_light(key=38, rim=70, lamp=90):
    sc = bpy.context.scene; H = k.head_center()
    for o in [o for o in sc.objects if o.type == "LIGHT"]: bpy.data.objects.remove(o, do_unlink=True)
    # soft cool key from front, camera side
    k.area("Key", H + Vector((0.9, 1.5, 0.4)), H, key, 1.2, (0.7, 0.8, 1.0))
    # hard purple neon rims from behind on both sides
    k.area("RimL", H + Vector((0.8, -0.6, 0.5)), H, rim, 0.3, (0.55, 0.12, 1.0))
    k.area("RimR", H + Vector((-0.8, -0.6, 0.4)), H, rim * 0.7, 0.3, (0.6, 0.15, 1.0))
    # orange sodium streetlight washing the wall from high screen-right
    wy = bpy.data.objects["Graffiti"].location.y
    k.area("Lamp", Vector((-2.4, wy + 2.0, 3.6)), Vector((-0.3, wy, 1.2)), lamp, 0.5, (1.0, 0.55, 0.22), 70)
    k.world((0.004, 0.005, 0.01), 1.0, haze=0.012)


def stage_render(name="cy1", pct=50, samples=48, exposure=0.0):
    k.setup_cycles(samples, "AgX - Punchy", exposure, dof_fstop=2.8)
    k.render(OUT + "\\" + name + ".png", pct, samples)


def stage_workbench(name="wb1", pct=40):
    sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"
    sc.render.resolution_percentage = pct; sc.render.filepath = OUT + "\\" + name + ".png"
    bpy.ops.render.render(write_still=True)
