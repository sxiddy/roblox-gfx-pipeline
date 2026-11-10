"""Blender side of the GFX pipeline. Use inside a style script after build_exact_gfx.py has rigged the avatar:

    import sys, importlib; sys.path.insert(0, r"...\\gfx and animation roblox blender\\tools")
    import gfx_kit as k; importlib.reload(k)
    k.clean_stray()                         # drop leftover untextured meshes (the white-floor bug)
    k.apply_pose("selfie")                  # or k.apply_pose("hip", mirror=True)
    k.ref_camera(r"...\\gfx_references\\name.png")   # aspect + 50% overlay + thirds guides
    k.frame_head(head_frac=0.5, head_xy=(0.45, 0.35), view_dir=(0.3, 1, 0.6), lens=18, roll=-13)
    k.light_preset("selfie_soft"); k.setup_cycles(128)
    k.render_mask(r"...\\mask.png")         # avatar alpha for gfx2d.py --mask / --outline

Conventions: armature object "Avatar", avatar faces +Y, ".P" = avatar's right (+X). Directions are world vectors.
"""
import glob
import math
import os

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library")


def arm():
    return bpy.data.objects["Avatar"]


def upd():
    bpy.context.view_layer.update()


# ---------------------------------------------------------------- posing
def aim(bone, d, hint=(0, 1, 0)):
    """Point a bone's Y axis along d; its Z axis goes toward hint (falls back to up if hint is parallel)."""
    upd(); a = arm(); pb = a.pose.bones[bone]
    y = Vector(d).normalized(); h = Vector(hint)
    z = h - h.dot(y) * y
    if z.length < 0.2:
        h = Vector((0, 0, 1)) if abs(y.z) < 0.9 else Vector((0, 1, 0)); z = h - h.dot(y) * y
    z.normalize(); x = y.cross(z)
    m = Matrix((x, y, z)).transposed().to_4x4(); m.translation = pb.head
    pb.matrix = m


def reset_pose():
    for pb in arm().pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    upd()


# (bone, direction, hint). Hands left out follow their forearm so they never look detached.
RELAX = [("UpperArm.N", (-0.2, 0.05, -1)), ("LowerArm.N", (-0.08, 0.15, -1))]
POSES = {
    "idle": [],
    "selfie": [("LowerTorso", (0.03, 0.1, 1)), ("UpperTorso", (0.1, 0.32, 1), (0.25, 1, 0)),
               ("UpperArm.P", (0.5, 0.55, 0.68)), ("LowerArm.P", (0.42, 0.6, 0.68)), ("Hand.P", (0.42, 0.6, 0.68), (0, 0, 1)),
               ("Head", (0.12, 0.08, 0.99), (0.3, 1, 0.4)), ("UpperArm.N", (-0.25, 0.1, -1)), ("LowerArm.N", (-0.1, 0.25, -1)),
               ("UpperLeg.P", (0.08, 0.05, -1)), ("UpperLeg.N", (-0.1, -0.05, -1))],
    "hip": [("LowerTorso", (0.07, 0, 1), (-0.18, 1, 0)), ("UpperTorso", (-0.08, 0.04, 1), (0.22, 1, 0)),
            ("Head", (-0.12, 0.06, 1), (0.3, 1, 0)),
            ("UpperArm.P", (0.62, -0.3, -0.72)), ("LowerArm.P", (-0.55, 0.3, -0.78)), ("Hand.P", (-0.45, 0.35, -0.82), (0, 0, 1)),
            ("UpperArm.N", (-0.2, 0.05, -1)), ("LowerArm.N", (-0.05, 0.2, -1)),
            ("UpperLeg.N", (-0.1, 0, -1)), ("LowerLeg.N", (-0.02, 0, -1)),
            ("UpperLeg.P", (-0.18, 0.32, -0.93)), ("LowerLeg.P", (0.06, -0.12, -1))],
    "mirror": [("LowerTorso", (0.07, 0, 1), (-0.15, 1, 0)), ("UpperTorso", (-0.06, 0.04, 1)), ("Head", (-0.05, 0.05, 1)),
               ("UpperArm.P", (0.3, 0.6, -0.75)), ("LowerArm.P", (-0.4, 0.62, 0.68)), ("Hand.P", (-0.3, 0.5, 0.8), (0, 1, 0)),
               ("UpperArm.N", (-0.62, -0.3, -0.72)), ("LowerArm.N", (0.55, 0.3, -0.78)), ("Hand.N", (0.45, 0.35, -0.82), (0, 0, 1)),
               ("UpperLeg.P", (-0.18, 0.32, -0.93)), ("LowerLeg.P", (0.06, -0.12, -1)), ("UpperLeg.N", (-0.08, 0, -1))],
    "peace": [("UpperTorso", (0.04, 0.05, 1)), ("Head", (-0.15, 0.05, 0.99), (0.2, 1, 0)),
              ("UpperArm.P", (0.35, 0.3, -0.88)), ("LowerArm.P", (-0.3, 0.35, 0.88)), ("Hand.P", (-0.2, 0.3, 0.93), (0, 1, 0))] + RELAX,
    "cross_arms": [("UpperTorso", (0, -0.04, 1)), ("Head", (0.08, -0.05, 1)),
                   ("UpperArm.P", (0.18, 0.35, -0.92)), ("LowerArm.P", (-0.95, 0.3, 0.1)),
                   ("UpperArm.N", (-0.18, 0.38, -0.91)), ("LowerArm.N", (0.95, 0.36, 0.18))],
    "lean": [("LowerTorso", (0.1, 0, 1), (-0.1, 1, 0)), ("UpperTorso", (-0.15, 0.05, 1)), ("Head", (0.12, 0.08, 1), (-0.2, 1, 0)),
             ("UpperArm.P", (0.5, -0.1, -0.86)), ("LowerArm.P", (0.3, 0.1, -0.95)),
             ("UpperArm.N", (-0.25, 0.1, -0.96)), ("LowerArm.N", (-0.1, 0.2, -0.97)),
             ("UpperLeg.P", (0.15, 0.05, -1)), ("UpperLeg.N", (0.12, 0.2, -1)), ("LowerLeg.N", (-0.05, -0.1, -1))],
    "sit": [("UpperLeg.P", (0.08, 1, -0.05)), ("LowerLeg.P", (0.02, 0.1, -1)), ("Foot.P", (0, 0.1, -1), (0, 1, 0)),
            ("UpperLeg.N", (-0.08, 1, -0.05)), ("LowerLeg.N", (-0.02, 0.1, -1)), ("Foot.N", (0, 0.1, -1), (0, 1, 0)),
            ("UpperTorso", (0, 0.12, 1)), ("Head", (0.05, 0.05, 1)),
            ("UpperArm.P", (0.12, 0.4, -0.9)), ("LowerArm.P", (0.02, 0.97, -0.2)),
            ("UpperArm.N", (-0.12, 0.4, -0.9)), ("LowerArm.N", (-0.02, 0.97, -0.2))],
    "point": [("UpperTorso", (0.05, 0.1, 1), (0.25, 1, 0)), ("Head", (0, 0.06, 1)),
              ("UpperArm.P", (0.3, 0.95, 0.1)), ("LowerArm.P", (0.12, 1, 0.08))] + RELAX,
    "shy": [("UpperTorso", (0, 0.12, 1)), ("Head", (0.12, 0.22, 0.97)),
            ("UpperArm.P", (0.1, 0.3, -0.95)), ("LowerArm.P", (-0.5, 0.6, -0.6)),
            ("UpperArm.N", (-0.1, 0.3, -0.95)), ("LowerArm.N", (0.5, 0.62, -0.58))],
    "look_up": [("UpperTorso", (0, -0.08, 1)), ("Head", (0.05, -0.45, 0.89), (0, 0.85, 0.5))] + RELAX,
    "action": [("LowerTorso", (0, 0.15, 1), (0.3, 1, 0)), ("UpperTorso", (0, 0.35, 1), (0.45, 1, 0)), ("Head", (0, 0.1, 1), (0.2, 1, 0)),
               ("UpperArm.P", (0.2, 1, 0.1)), ("LowerArm.P", (0.1, 1, 0.05)),
               ("UpperArm.N", (-0.5, -0.7, -0.3)), ("LowerArm.N", (-0.3, -0.8, -0.4)),
               ("UpperLeg.P", (0.1, 0.6, -0.8)), ("LowerLeg.P", (0, -0.1, -1)),
               ("UpperLeg.N", (-0.1, -0.55, -0.83)), ("LowerLeg.N", (0, -0.6, -0.8))],
}


def _flip(name):
    return name[:-2] + (".N" if name.endswith(".P") else ".P") if name[-2:] in (".P", ".N") else name


def apply_pose(name, mirror=False, reset=True):
    """Pose from POSES. mirror=True swaps sides (left/right). Bones of the avatar that don't exist are skipped."""
    if reset:
        reset_pose()
    bones = arm().pose.bones; done = set()
    for item in POSES[name]:
        bone, d, hint = (item + ((0, 1, 0),))[:3] if len(item) == 2 else item
        if mirror:
            bone = _flip(bone); d = (-d[0], d[1], d[2]); hint = (-hint[0], hint[1], hint[2])
        if bone in bones:
            aim(bone, d, hint); done.add(bone)
            hand = bone.replace("LowerArm", "Hand")
            if bone.startswith("LowerArm") and hand in bones and not any(_b(i, mirror) == hand for i in POSES[name]):
                aim(hand, d, (0, 0, 1))
    upd()


def _b(item, mirror):
    return _flip(item[0]) if mirror else item[0]


# ---------------------------------------------------------------- measuring and camera
def head_obj():
    """The body-part head mesh (not hair or hats)."""
    kids = [o for o in arm().children if o.parent_bone == "Head" and o.type == "MESH"]
    named = [o for o in kids if o.name.split(".")[0] == "Head"]
    body = named or [o for o in kids if not o.name.startswith("Handle")] or kids
    return min(body, key=lambda o: o.dimensions.length) if body else None


def head_center():
    upd(); pb = arm().pose.bones["Head"]
    return arm().matrix_world @ ((pb.head + pb.tail) / 2)


def project(p, cam=None):
    """World point -> frame fraction (x right, y DOWN, like the grid images) and depth."""
    scene = bpy.context.scene; cam = cam or scene.camera
    v = world_to_camera_view(scene, cam, Vector(p))
    return v.x, 1 - v.y, v.z


def measure():
    """Head centre in the frame and head width as a fraction of frame width."""
    upd(); o = head_obj(); scene = bpy.context.scene
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box] if o else [head_center()]
    pr = [project(p) for p in pts]
    xs = [p[0] for p in pr]
    cx, cy, _ = project(sum(pts, Vector()) / len(pts))
    return {"head_xy": (round(cx, 3), round(cy, 3)), "head_frac": round(max(xs) - min(xs), 3),
            "aspect": f"{scene.render.resolution_x}x{scene.render.resolution_y}"}


def ref_camera(ref_path, long_side=1920, alpha=0.5):
    """Match the render aspect to the reference and show it over the camera view for posing by eye."""
    scene = bpy.context.scene; cam = scene.camera
    img = bpy.data.images.load(ref_path, check_existing=True); w, h = img.size
    s = long_side / max(w, h)
    scene.render.resolution_x, scene.render.resolution_y = round(w * s / 2) * 2, round(h * s / 2) * 2
    cam.data.show_background_images = True
    bg = cam.data.background_images[0] if cam.data.background_images else cam.data.background_images.new()
    bg.image = img; bg.alpha = alpha; bg.display_depth = "FRONT"; bg.frame_method = "CROP"
    cam.data.show_composition_thirds = True; cam.data.show_composition_center = True
    return scene.render.resolution_x, scene.render.resolution_y


def place_camera(loc, target, lens=None, roll=0.0):
    cam = bpy.context.scene.camera; cam.location = Vector(loc)
    q = (Vector(target) - cam.location).to_track_quat("-Z", "Y")
    cam.rotation_euler = (q @ Matrix.Rotation(math.radians(roll), 4, "Z").to_quaternion()).to_euler()
    if lens:
        cam.data.lens = lens
    upd()


def frame_head(head_frac, head_xy=(0.5, 0.4), view_dir=(0, 1, 0.3), lens=35, roll=0.0, iters=6):
    """Put the camera on view_dir from the head, then solve distance and lens shift so the head is head_frac of
    the frame width with its centre at head_xy (measured from the reference with `gfx2d.py grid`)."""
    cam = bpy.context.scene.camera; H = head_center(); dist = 1.0
    cam.data.shift_x = cam.data.shift_y = 0
    for _ in range(iters):
        place_camera(H + Vector(view_dir).normalized() * dist, H, lens, roll)
        m = measure()
        if m["head_frac"] <= 0:
            raise RuntimeError("head not found in frame; check head_obj()")
        dist *= m["head_frac"] / head_frac
    place_camera(H + Vector(view_dir).normalized() * dist, H, lens, roll)
    sx, sy = bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y; k = min(sx, sy) / max(sx, sy)
    for _ in range(iters):
        x, y = measure()["head_xy"]
        cam.data.shift_x += (x - head_xy[0]) * (1 if sx >= sy else k)
        cam.data.shift_y -= (y - head_xy[1]) * (k if sx >= sy else 1)
        upd()
    cam.data.dof.focus_distance = dist
    return {"dist": round(dist, 3), **measure()}


def selfie_camera(target_frac=0.75, corner="bl", hand="P"):
    """Lens near the phone hand: wrist out of frame, elbow in frame near `corner`, head ~target_frac away."""
    a = arm(); pb = a.pose.bones; H = head_center(); target = H + Vector((0, 0, -0.32))
    tip, wrist, elbow = (a.matrix_world @ v for v in (pb[f"Hand.{hand}"].tail, pb[f"Hand.{hand}"].head, pb[f"LowerArm.{hand}"].head))
    want = {"bl": (0, 1), "br": (1, 1), "tl": (0, 0), "tr": (1, 0)}[corner]
    inside = lambda p: p[2] > 0 and 0 <= p[0] <= 1 and 0 <= p[1] <= 1
    best = None
    for dx in (-0.2, -0.14, -0.08, -0.02, 0.04, 0.1):
        for dy in (-0.05, 0.02, 0.09, 0.16, 0.24, 0.32, 0.4, 0.48):
            for dz in (-0.1, -0.03, 0.04, 0.11, 0.18, 0.25):
                c = tip + Vector((dx if hand == "P" else -dx, dy, dz)); d = (c - H).length
                if not 0.62 < d < 0.95:
                    continue
                place_camera(c, target)
                if inside(project(wrist)) or inside(project(tip)) or not inside(project(elbow)):
                    continue
                e = project(elbow); score = abs(e[0] - want[0]) + abs(e[1] - want[1]) + abs(d - target_frac)
                if best is None or score < best[0]:
                    best = (score, c.copy())
    if best:
        place_camera(best[1], target)
    return best is not None


# ---------------------------------------------------------------- materials and props
def material(name, color=(0.5, 0.5, 0.5), rough=0.6, metal=0.0, emit=None, strength=1.0, alpha=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color[:3], 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit[:3], 1); b.inputs["Emission Strength"].default_value = strength
    if alpha is not None:
        b.inputs["Alpha"].default_value = alpha
    return m


def pbr(name, scale=1.0, tint=None):
    """Material from library/textures/*/<name> (diffuse, roughness, GL normal). scale = repeats per metre."""
    d = glob.glob(os.path.join(LIB, "textures", "*", name))
    if not d:
        raise ValueError(f"texture {name} not in library/textures")
    files = glob.glob(os.path.join(d[0], "*.jpg")) + glob.glob(os.path.join(d[0], "*.png"))
    pick = lambda *keys: next((f for f in files if any(k in os.path.basename(f).lower() for k in keys)), None)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale); nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

    def tex(path, colour):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
        t.projection = "BOX"; t.projection_blend = 0.2  # object-coord UVs smeared into stripes on side faces
        if not colour:
            t.image.colorspace_settings.name = "Non-Color"
        nt.links.new(mp.outputs[0], t.inputs["Vector"]); return t
    if pick("diff", "albedo", "col"):
        t = tex(pick("diff", "albedo", "col"), True)
        if tint:
            mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1; mix.inputs[7].default_value = (*tint, 1)
            nt.links.new(t.outputs["Color"], mix.inputs[6]); nt.links.new(mix.outputs[2], b.inputs["Base Color"])
        else:
            nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    if pick("rough"):
        nt.links.new(tex(pick("rough"), False).outputs["Color"], b.inputs["Roughness"])
    if pick("nor_gl", "normal"):
        nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(tex(pick("nor_gl", "normal"), False).outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


def cube(name, size, loc, mat, rot_z=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=(0, 0, math.radians(rot_z)))
    o = bpy.context.active_object; o.name = name; o.scale = size; o.data.materials.append(mat); return o


def plane(name, size, loc, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=tuple(math.radians(r) for r in rot))
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1); o.data.materials.append(mat); return o


def cardboard_box(loc, size=(0.42, 0.3, 0.26), rot_z=0.0, tape=(0.05, 0.12, 0.45)):
    b = cube("Box", size, loc, material("Cardboard", (0.42, 0.28, 0.14), 0.8), rot_z)
    cube("Tape", (size[0] + 0.005, 0.06, size[2] + 0.005), loc, material("Tape", tape, 0.4), rot_z)
    return b


def chain_fence(loc, width=16, height=3, rot_z=0.0, cells=16):
    """Chain-link as an alpha mask on a vertical plane."""
    o = plane("Fence", (width, height), loc, bpy.data.materials.new("ChainLink"), (90, 0, rot_z))
    m = o.data.materials[0]; m.use_nodes = True; nt = m.node_tree; N = nt.nodes.new; L = nt.links.new
    b = nt.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.55, 0.56, 0.58, 1)
    b.inputs["Metallic"].default_value = 1; b.inputs["Roughness"].default_value = 0.4
    tc = N("ShaderNodeTexCoord"); sx = N("ShaderNodeSeparateXYZ"); L(tc.outputs["Object"], sx.inputs[0]); ws = []
    for sgn in (1, -1):
        s1 = N("ShaderNodeMath"); s1.operation = "MULTIPLY"; s1.inputs[1].default_value = cells * sgn
        s2 = N("ShaderNodeMath"); s2.operation = "MULTIPLY"; s2.inputs[1].default_value = cells * height / width
        ad = N("ShaderNodeMath"); ad.operation = "ADD"
        pp = N("ShaderNodeMath"); pp.operation = "PINGPONG"; pp.inputs[1].default_value = 0.03
        th = N("ShaderNodeMath"); th.operation = "LESS_THAN"; th.inputs[1].default_value = 0.004
        L(sx.outputs["X"], s1.inputs[0]); L(sx.outputs["Y"], s2.inputs[0]); L(s1.outputs[0], ad.inputs[0]); L(s2.outputs[0], ad.inputs[1])
        L(ad.outputs[0], pp.inputs[0]); L(pp.outputs[0], th.inputs[0]); ws.append(th)
    mx = N("ShaderNodeMath"); mx.operation = "MAXIMUM"; L(ws[0].outputs[0], mx.inputs[0]); L(ws[1].outputs[0], mx.inputs[1])
    L(mx.outputs[0], b.inputs["Alpha"]); return o


def post(loc, height=3.2, radius=0.035):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=loc)
    o = bpy.context.active_object; o.name = "Post"; o.data.materials.append(material("Steel", (0.5, 0.5, 0.52), 0.45, 1)); return o


def mirror(loc, size=(0.9, 1.6), rot_z=0.0, frame=(0.9, 0.9, 0.9)):
    m = plane("Mirror", size, loc, material("MirrorGlass", (0.95, 0.95, 0.95), 0.02, 1), (90, 0, rot_z))
    cube("MirrorFrame", (size[0] + 0.08, 0.03, size[1] + 0.08), Vector(loc) - Vector((0, 0.02, 0)), material("Frame", frame, 0.4), rot_z)
    return m


def neon_text(text, loc, color=(1.0, 0.1, 0.6), size=0.4, strength=25, font="monoton", rot=(90, 0, 180)):
    bpy.ops.object.text_add(location=loc, rotation=tuple(math.radians(r) for r in rot))
    o = bpy.context.active_object; o.name = "Neon"; o.data.body = text; o.data.size = size; o.data.align_x = "CENTER"
    f = glob.glob(os.path.join(LIB, "fonts", font, "*.ttf"))
    if f:
        o.data.font = bpy.data.fonts.load(f[0], check_existing=True)
    o.data.materials.append(material("Neon", color, 0.3, emit=color, strength=strength)); return o


def led_strip(points, color=(0.6, 0.2, 1.0), strength=30, radius=0.012):
    cu = bpy.data.curves.new("LED", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = radius
    sp = cu.splines.new("POLY"); sp.points.add(len(points) - 1)
    for p, c in zip(sp.points, points):
        p.co = (*c, 1)
    o = bpy.data.objects.new("LED", cu); bpy.context.scene.collection.objects.link(o)
    cu.materials.append(material("LEDGlow", color, 0.3, emit=color, strength=strength)); return o


def bokeh_lights(center, count=40, spread=(4, 0.5, 2.5), colors=((1, 0.7, 0.4), (1, 0.4, 0.7)), strength=20, seed=3):
    """Small emissive spheres far behind the subject; with shallow depth of field they become bokeh discs."""
    import random
    r = random.Random(seed); c = Vector(center)
    for i in range(count):
        col = colors[i % len(colors)]
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r.uniform(0.02, 0.05), segments=12, ring_count=6,
                                             location=c + Vector([r.uniform(-s, s) for s in spread]))
        o = bpy.context.active_object; o.name = "Bokeh"; o.data.materials.append(material("BokehGlow", col, 0.5, emit=col, strength=strength))


def import_model(category, name, loc=(0, 0, 0), rot_z=0.0, scale=1.0):
    """glTF model from library/models/<category>/<name>."""
    f = glob.glob(os.path.join(LIB, "models", category, name, "*.gltf"))
    if not f:
        raise ValueError(f"model {category}/{name} not in library/models")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f[0])
    roots = [o for o in set(bpy.data.objects) - before if o.parent is None]
    for o in roots:
        o.location = loc; o.rotation_euler[2] = math.radians(rot_z); o.scale = (scale,) * 3
    return roots


def clean_stray(keep=()):
    """Delete visible, unparented meshes with no material (e.g. a default Plane that washes the floor white)."""
    gone = []
    for o in list(bpy.context.scene.objects):
        if o.type == "MESH" and not o.parent and o.name not in keep and not any(o.data.materials):
            gone.append(o.name); bpy.data.objects.remove(o, do_unlink=True)
    return gone


def skin_clothes(names=None):
    """Bind layered clothing (jacket sleeves, skirts) to the nearest bones so it bends with the limbs.

    Roblox layered clothing comes in rigid, parented to a torso bone; posing the arms then leaves the sleeves behind
    and hands float (chibi bodies have no forearm mesh). Weights: inverse distance to the two nearest bone segments.
    """
    a = arm()
    if names is None:
        names = [o.name for o in bpy.data.objects if o.parent == a and o.parent_bone in ("UpperTorso", "LowerTorso")
                 and o.name.startswith("Handle")]
    pp = a.data.pose_position
    a.data.pose_position = "REST"; bpy.context.view_layer.update()
    segs = [(b.name, a.matrix_world @ b.head_local, a.matrix_world @ b.tail_local) for b in a.data.bones if b.name != "Head"]

    def dist(p, h, t):
        d = t - h; f = max(0.0, min(1.0, (p - h).dot(d) / max(d.length_squared, 1e-9)))
        return (p - (h + d * f)).length

    done = []
    for n in names:
        o = bpy.data.objects[n]; mw = o.matrix_world.copy()
        o.parent = a; o.parent_type = "OBJECT"; o.matrix_world = mw
        for g in list(o.vertex_groups): o.vertex_groups.remove(g)
        groups = {s[0]: o.vertex_groups.new(name=s[0]) for s in segs}
        for v in o.data.vertices:
            p = mw @ v.co
            near = sorted((dist(p, h, t), b) for b, h, t in segs)[:2]
            ws = [1 / (d ** 4 + 1e-6) for d, _ in near]
            for (d, b), w in zip(near, ws):
                groups[b].add([v.index], w / sum(ws), "REPLACE")
        m = next((m for m in o.modifiers if m.type == "ARMATURE"), None) or o.modifiers.new("Armature", "ARMATURE")
        m.object = a
        done.append(n)
    a.data.pose_position = pp; bpy.context.view_layer.update()
    return done


def clear(prefixes):
    for o in list(bpy.data.objects):
        if o.name.split(".")[0] in prefixes:
            bpy.data.objects.remove(o, do_unlink=True)


# ---------------------------------------------------------------- lighting
def area(name, loc, target, energy, size=1.0, color=(1, 1, 1), spread=180):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size; ld.color = color
    ld.spread = math.radians(spread)
    o = bpy.data.objects.new(name, ld); bpy.context.scene.collection.objects.link(o); o.location = Vector(loc)
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o


# offsets in camera terms from the head: (right, up, toward-camera) in metres; energy is per metre of distance²
LIGHTS = {
    "selfie_soft": [("Key", (0.6, 1.4, 0.9), 30, 1.6, (0.92, 0.96, 1.0), 55), ("Rim", (-1.0, 0.9, -1.4), 55, 0.8, (0.72, 0.82, 1.0), 180)],
    "mirror_led": [("Ceiling", (0, 2.0, 0.3), 25, 1.5, (1.0, 0.95, 0.9), 70), ("LEDside", (-1.2, 0.2, -0.3), 40, 0.4, (0.7, 0.3, 1.0), 180)],
    "portrait": [("Key", (0.8, 0.6, 0.8), 20, 1.2, (1.0, 0.95, 0.9), 180), ("Fill", (-0.8, 0.0, 1.0), 4, 2.0, (0.9, 0.95, 1.0), 180),
                 ("Rim", (-0.6, 0.7, -1.0), 50, 0.6, (1.0, 0.85, 0.75), 180)],
    "moon_rim": [("Moon", (-0.8, 1.2, -1.2), 70, 0.8, (0.6, 0.72, 1.0), 180), ("Fill", (0.6, 0.2, 1.0), 2, 2.0, (0.5, 0.6, 1.0), 180)],
    "flat_comic": [("Front", (0.3, 0.4, 1.5), 35, 3.0, (1, 1, 1), 180), ("Rim", (0, 1.0, -1.0), 30, 1.0, (1, 1, 1), 180)],
    "action_backlit": [("Back", (0.4, 0.8, -1.5), 140, 1.0, (0.4, 0.7, 1.0), 180), ("FX", (0.5, -0.3, 0.6), 30, 0.5, (1.0, 0.5, 0.15), 180),
                       ("Fill", (-0.8, 0.3, 0.8), 4, 2.0, (0.6, 0.7, 1.0), 180)],
    "room_practical": [("Lamp", (1.0, 0.5, 0.3), 25, 0.5, (1.0, 0.7, 0.4), 180), ("Screen", (-0.6, 0.0, 0.8), 8, 0.8, (0.5, 0.7, 1.0), 180)],
    "three_point": [("Key", (0.9, 0.7, 1.0), 30, 1.5, (1, 0.97, 0.94), 180), ("Fill", (-1.0, 0.3, 1.0), 10, 2.0, (0.95, 0.97, 1), 180),
                    ("Rim", (0, 1.0, -1.2), 45, 1.0, (1, 1, 1), 180)],
    "flash": [("Flash", (0.05, 0.1, 1.0), 25, 0.15, (1, 1, 1), 180)],
    "horror_under": [("Under", (0, -1.0, 0.6), 25, 0.5, (1.0, 0.15, 0.1), 180), ("Back", (0, 0.6, -1.4), 30, 0.6, (0.3, 1.0, 0.4), 180)],
    "neon_street": [("NeonA", (-1.0, 0.4, 0.2), 45, 0.6, (1.0, 0.1, 0.6), 180), ("NeonB", (1.0, 0.5, -0.4), 45, 0.6, (0.1, 0.8, 1.0), 180)],
    "thumbnail": [("Key", (0.5, 0.5, 1.2), 35, 2.5, (1, 1, 1), 180), ("RimL", (-1, 0.5, -0.8), 50, 0.8, (1, 1, 1), 180),
                  ("RimR", (1, 0.5, -0.8), 50, 0.8, (1, 1, 1), 180)],
}


def light_preset(name, clear_old=True, scale=1.0):
    """Lights placed around the head relative to the current camera, so they follow any framing."""
    scene = bpy.context.scene
    if clear_old:
        for o in [o for o in scene.objects if o.type == "LIGHT"]:
            bpy.data.objects.remove(o, do_unlink=True)
    H = head_center(); fwd = (scene.camera.location - H).normalized()
    right = fwd.cross(Vector((0, 0, 1))).normalized() * -1; up = right.cross(fwd).normalized() * -1
    if up.z < 0:
        up = -up
    out = []
    for nm, (r, u, f), e, size, col, spread in LIGHTS[name]:
        p = H + right * r + up * u + fwd * f
        out.append(area(nm, p, H, e * (p - H).length_squared * scale, size, col, spread))
    return out


def world(color=(0.05, 0.05, 0.06), strength=1.0, haze=0.0, hdri=None):
    """Plain or HDRI world, optional haze (volume scatter density)."""
    w = bpy.context.scene.world; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes["Background"]
    bg.inputs["Color"].default_value = (*color, 1); bg.inputs["Strength"].default_value = strength
    if hdri:
        f = glob.glob(os.path.join(LIB, "hdri", "*", hdri + "*.hdr")) or glob.glob(os.path.join(LIB, "..", "hdri", hdri + "*.hdr"))
        env = nt.nodes.get("HDRI") or nt.nodes.new("ShaderNodeTexEnvironment"); env.name = "HDRI"
        env.image = bpy.data.images.load(f[0], check_existing=True); nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    hz = nt.nodes.get("Haze")
    if haze:
        hz = hz or nt.nodes.new("ShaderNodeVolumeScatter"); hz.name = "Haze"; hz.inputs["Density"].default_value = haze
        nt.links.new(hz.outputs[0], nt.nodes["World Output"].inputs["Volume"])
    elif hz:
        nt.nodes.remove(hz)


# ---------------------------------------------------------------- showing work in the owner's viewport
def view3d_areas():
    """Current 3D views, looked up fresh: never keep areas across timer ticks (a freed area crashes Blender)."""
    return [a for w in bpy.context.window_manager.windows for a in w.screen.areas if a.type == "VIEW_3D"]


def show_camera(shading="SOLID"):
    """Every 3D view: leave local view, look through the scene camera, centre it, Material Preview."""
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type != "VIEW_3D":
                continue
            sp = a.spaces.active; sp.shading.type = shading
            with bpy.context.temp_override(window=w, area=a, region=next(r for r in a.regions if r.type == "WINDOW")):
                if sp.local_view:
                    bpy.ops.view3d.localview(frame_selected=False)
                if sp.region_3d.view_perspective != "CAMERA":
                    bpy.ops.view3d.view_camera()
                bpy.ops.view3d.view_center_camera()


def label(text=None):
    for a in view3d_areas():
        a.header_text_set(text); a.tag_redraw()


def play_steps(steps, interval=2.5):
    """Run [(label, fn), ...] one by one on a Blender timer so the owner can watch each change."""
    steps = list(steps)

    def tick():
        if not steps:
            label(None); return None
        text, fn = steps.pop(0)
        try:
            fn(); label(text)
        except Exception as e:  # keep the UI alive; report in the header instead
            label(f"{text}: failed ({e})")
        return interval
    bpy.app.timers.register(tick, first_interval=0.5)


# ---------------------------------------------------------------- rendering
def setup_cycles(samples=128, look="AgX - Punchy", exposure=0.0, dof_fstop=None):
    scene = bpy.context.scene; scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for dev in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = dev; break
        except TypeError:
            continue
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True  # owner: use the whole GPU and CPU
    scene.cycles.device = "GPU"; scene.cycles.samples = samples; scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "AgX"; scene.view_settings.look = look; scene.view_settings.exposure = exposure
    if dof_fstop:
        scene.camera.data.dof.use_dof = True; scene.camera.data.dof.aperture_fstop = dof_fstop


def render(path, percent=100, samples=None):
    scene = bpy.context.scene; old = scene.cycles.samples
    if samples:
        scene.cycles.samples = samples
    scene.render.resolution_percentage = percent; scene.render.filepath = path
    bpy.ops.render.render(write_still=True); scene.cycles.samples = old


def render_mask(path, percent=100):
    """Render only the avatar with a transparent background: its alpha is the character mask."""
    scene = bpy.context.scene; a = arm()
    keep = {a} | set(a.children_recursive)
    hidden = [o for o in scene.objects if o not in keep and o.type not in {"LIGHT", "CAMERA"} and not o.hide_render]
    for o in hidden:
        o.hide_render = True
    old = (scene.render.film_transparent, scene.cycles.samples, scene.render.image_settings.color_mode)
    scene.render.film_transparent = True; scene.render.image_settings.color_mode = "RGBA"
    render(path, percent, samples=8)
    scene.render.film_transparent, scene.cycles.samples, scene.render.image_settings.color_mode = old
    for o in hidden:
        o.hide_render = False
