"""Build a stage member as a proper Roblox R15 avatar: official ClassicMannequin body parts (rigs_official) hung on a joint
chain of empties (same convention as anim_concert2: root local = avatar space, +X right, +Y forward, +Z up, segments hang
along local -Z), dressed in real catalog clothing, K-pop style catalog hair and a classic face decal (library/cortis_items/*, assets-thumbnail-3d
exports). Shirt/pants exports come on an R6 dummy: each R6 block is box-fitted over the matching R15 parts and its UVs are
transferred, so the clothing texture lands on the jointed R15 body."""
import os, json, math
import bpy
from mathutils import Vector, Matrix

ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
FBX = os.path.join(ROOT, "rigs_official", "ClassicMannequin.fbx")
HEIGHT = 1.62
SKIN = (0.93, 0.78, 0.66)
_base = {}


def upd():
    bpy.context.view_layer.update()


def bounds(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def vbounds(o):  # from mesh data, valid even while hidden (hidden objects keep stale bound_box)
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    return (Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))),
            Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs))))


def load_base():
    """Import the mannequin once, bake transforms, scale to HEIGHT, feet on z=0, facing +Y; keep it hidden as a template."""
    if _base:
        return _base
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=FBX)
    new = [o for o in bpy.data.objects if o not in before]
    parts = {}
    for o in new:
        if o.type == "MESH":
            mw = o.matrix_world.copy(); o.parent = None; o.data.transform(mw); o.matrix_world = Matrix.Identity(4)
            parts[o.name.replace("_Geo", "").split(".")[0]] = o
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    upd()
    lo = Vector((min(bounds(o)[0][i] for o in parts.values()) for i in range(3)))
    hi = Vector((max(bounds(o)[1][i] for o in parts.values()) for i in range(3)))
    s = HEIGHT / (hi.z - lo.z); c = (lo + hi) / 2
    M = Matrix.Scale(s, 4) @ Matrix.Translation((-c.x, -c.y, -lo.z))
    # facing: the foot sticks out to the front of the lower leg
    f = sum(bounds(parts["RightFoot"]), Vector()) / 2; l = sum(bounds(parts["RightLowerLeg"]), Vector()) / 2
    if f.y < l.y:
        M = Matrix.Rotation(math.pi, 4, "Z") @ M
    for o in parts.values():
        o.data.transform(M)
    upd()
    tops = {k: top_centre(o) for k, o in parts.items()}
    for o in parts.values():
        o.hide_render = True; o.hide_viewport = True; o.name = "Tpl_" + o.name
    _base.update(parts); _base["_tops"] = tops
    return _base


def top_centre(o):  # of a visible object
    lo, hi = bounds(o); return Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z))


def import_export(d, split=False):
    """Import an assets-thumbnail-3d export folder: returns (mesh objects, texture path, meta)."""
    meta = json.load(open(os.path.join(d, "meta.json")))
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=os.path.join(d, meta["obj"]), use_split_groups=split)
    objs = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    for o in objs:
        o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
    return objs, os.path.join(d, meta["textures"][0]), meta


def tex_mat(name, img_path, under=None, rough=0.7):
    """Texture material. `under` = colour shown where the texture is transparent (skin under clothing),
    otherwise the texture alpha cuts the surface (hair strands on heads)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(img_path, check_existing=True)
    t.image.colorspace_settings.name = "sRGB"; t.image.alpha_mode = "STRAIGHT"
    if under is not None:  # the dummy's grey body colour is baked in opaque: key it out so skin shows through
        import numpy as np
        im = t.image.copy(); im.name = name + "Tex"; px = np.empty(len(im.pixels), np.float32); im.pixels.foreach_get(px)
        px = px.reshape(-1, 4); body = np.array([229, 228, 223]) / 255.0
        lin = np.where(body <= 0.04045, body / 12.92, ((body + 0.055) / 1.055) ** 2.4)  # pixels() are linear for sRGB images
        hit = (np.abs(px[:, :3] - lin) < 0.012).all(1) | (np.abs(px[:, :3] - body) < 0.008).all(1)
        px[hit, 3] = 0.0; im.pixels.foreach_set(px.ravel()); im.pack(); t.image = im
    if under is None:
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    else:
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
        nt.links.new(t.outputs["Alpha"], mix.inputs["Factor"]); mix.inputs["A"].default_value = (*under, 1)
        nt.links.new(t.outputs["Color"], mix.inputs["B"]); nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    return m


R15_OF_R6 = {"torso": ("UpperTorso", "LowerTorso"), "armR": ("RightUpperArm", "RightLowerArm", "RightHand"),
             "armL": ("LeftUpperArm", "LeftLowerArm", "LeftHand"), "legR": ("RightUpperLeg", "RightLowerLeg", "RightFoot"),
             "legL": ("LeftUpperLeg", "LeftLowerLeg", "LeftFoot")}


def r6_blocks(d, P):
    """Import an R6 clothing export (legs 0-2, arms/torso 2-4, head 4-5 studs) and fit each block over the matching
    group of R15 template parts."""
    objs, tex, _ = import_export(d, split=True)
    blocks = {}
    for o in objs:  # the clothing thumbnail dummy faces -Y after import: turn it to face +Y like the template
        o.data.transform(Matrix.Rotation(math.pi, 4, "Z"))
    for o in objs:
        lo, hi = vbounds(o); c = (lo + hi) / 2
        if c.z > 4.0:  # head block
            bpy.data.objects.remove(o, do_unlink=True); continue
        key = "torso" if abs(c.x) < 0.5 and c.z > 2 else ("arm" if c.z > 2 else "leg") + ("R" if c.x > 0 else "L")
        blocks[key] = o
    for key, o in blocks.items():
        lo, hi = vbounds(o)
        tl = Vector((min(vbounds(P[k])[0][i] for k in R15_OF_R6[key]) for i in range(3)))
        th = Vector((max(vbounds(P[k])[1][i] for k in R15_OF_R6[key]) for i in range(3)))
        S = Matrix.Diagonal([(th[i] - tl[i]) / max(hi[i] - lo[i], 1e-6) for i in range(3)] + [1])
        o.data.transform(Matrix.Translation(tl) @ S @ Matrix.Translation(-lo))
        o.hide_render = True
    upd()
    return blocks, tex


def transfer_uv(dst, src):
    for uv in list(dst.data.uv_layers):  # the mannequin's own R15 UVs would otherwise stay the render layer
        dst.data.uv_layers.remove(uv)
    dst.data.uv_layers.new(name="UVMap")
    md = dst.modifiers.new("uvx", "DATA_TRANSFER"); md.object = src
    md.use_loop_data = True; md.data_types_loops = {"UV"}; md.loop_mapping = "POLYINTERP_LNORPROJ"
    md.layers_uv_select_src = "ALL"; md.layers_uv_select_dst = "INDEX"
    with bpy.context.temp_override(object=dst, active_object=dst):
        bpy.ops.object.modifier_apply(modifier=md.name)


def fit_hair(d, head_lo, head_hi, name, width=1.0, lift=0.12):
    """Catalog hair accessory: front toward +Y, at true stud scale (the classic head is 1.2 studs wide), crown `lift` studs
    above the head top."""
    objs, tex, meta = import_export(d)
    if len(objs) > 1:
        with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs):
            bpy.ops.object.join()
    h = objs[0]; h.name = name
    a, c = meta["aabb"], meta["camera"]["position"]
    ctr = [(a["min"][k] + a["max"][k]) / 2 for k in "xyz"]
    front = Vector((c["x"] - ctr[0], -(c["z"] - ctr[2]), 0))  # thumbnail camera sits in front; roblox (x,y,z) -> (x,-z,y)
    h.data.transform(Matrix.Rotation(math.atan2(front.x, front.y), 4, "Z"))  # that direction onto +Y
    stud = (head_hi.x - head_lo.x) / 1.2
    h.data.transform(Matrix.Scale(stud * width, 4)); lo, hi = vbounds(h)
    tgt = Vector(((head_lo.x + head_hi.x) / 2, (head_lo.y + head_hi.y) / 2 - 0.08 * stud, head_hi.z + lift * stud))
    h.data.transform(Matrix.Translation(tgt - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z))))
    h.data.materials.clear(); h.data.materials.append(tex_mat(name + "Mat", tex, rough=0.5))
    upd()
    return h


def face_mat(name, face_png):
    """Skin with a classic Roblox face decal projected onto the front of the head (FaceUV, front-facing normals only)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.5
    uv = nt.nodes.new("ShaderNodeUVMap"); uv.uv_map = "FaceUV"
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(face_png, check_existing=True); t.extension = "CLIP"
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    front = nt.nodes.new("ShaderNodeMath"); front.operation = "MULTIPLY"; front.use_clamp = True; front.inputs[1].default_value = 4.0
    k = nt.nodes.new("ShaderNodeMath"); k.operation = "MULTIPLY"
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.inputs["A"].default_value = (*SKIN, 1)
    nt.links.new(uv.outputs["UV"], t.inputs["Vector"]); nt.links.new(tc.outputs["Normal"], sep.inputs[0])
    nt.links.new(sep.outputs["Y"], front.inputs[0]); nt.links.new(front.outputs[0], k.inputs[0]); nt.links.new(t.outputs["Alpha"], k.inputs[1])
    nt.links.new(k.outputs[0], mix.inputs["Factor"]); nt.links.new(t.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    return m


def face_uv(o, size=0.95, dz=0.0):
    """Front orthographic UVs over the head: the face image spans `size` of the head width."""
    lo, hi = vbounds(o); w = (hi.x - lo.x) * size; cx = (lo.x + hi.x) / 2; cz = (lo.z + hi.z) / 2 + dz * (hi.z - lo.z)
    lay = o.data.uv_layers.new(name="FaceUV")
    for lp in o.data.loops:
        v = o.data.vertices[lp.vertex_index].co
        lay.data[lp.index].uv = ((v.x - cx) / w + 0.5, (v.z - cz) / w + 0.5)


def build_member(i, look, hair_dir=None, front_y=0.0):
    """look: dict(shirt=dir, pants=dir, hair=dir, face=png[, hair_w, hair_lift]) from library/cortis_items."""
    P = load_base(); n = f"M{i}"
    col = bpy.context.scene.collection
    shirt, shirt_tex = r6_blocks(look["shirt"], P); pants, pants_tex = r6_blocks(look["pants"], P)
    m_shirt = tex_mat(n + "Shirt", shirt_tex, SKIN); m_pants = tex_mat(n + "Pants", pants_tex, SKIN)
    src = {}
    for key, ks in R15_OF_R6.items():
        for k in ks:
            src[k] = (shirt[key], m_shirt) if key.startswith(("torso", "arm")) else (pants[key], m_pants)

    def part(key):
        o = P[key].copy(); o.data = P[key].data.copy(); o.name = f"{n}_{key}"; col.objects.link(o)
        o.animation_data_clear()  # the FBX ships keyframes on every part that would override our transforms
        o.matrix_parent_inverse.identity(); o.rotation_euler = (0, 0, 0); o.location = (0, 0, 0); o.scale = (1, 1, 1)
        o.hide_render = o.hide_viewport = False; o.data.materials.clear(); upd()
        b, m = src[key]; transfer_uv(o, b); o.data.materials.append(m)
        return o

    def empty(name, loc, parent=None):
        e = bpy.data.objects.new(name, None); col.objects.link(e); e.rotation_mode = "QUATERNION"
        if parent:
            e.parent = parent; upd()
        e.matrix_world = Matrix.Translation(loc); upd(); return e

    def attach(o, e, keep_world=False):
        """Body mesh data is in rest world coords and joints are unrotated at rest, so the local transform is -joint."""
        upd(); jt = e.matrix_world.translation.copy(); mw = o.matrix_world.copy()
        o.parent = e; o.matrix_parent_inverse.identity()
        if keep_world:
            o.matrix_basis = Matrix.Translation(-jt) @ mw
        else:
            o.rotation_mode = "XYZ"; o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1); o.location = -jt
        upd()

    root = empty(n, (0, 0, 0))
    attach(part("LowerTorso"), root)
    waist = empty(n + "_Hip", P["_tops"]["LowerTorso"], root)
    attach(part("UpperTorso"), waist)
    neck = empty(n + "_Neck", P["_tops"]["UpperTorso"], waist)
    parts = {"root": root, "hip": waist, "neck": neck, "hipj": {}}
    for side, S in (("R", "Right"), ("L", "Left")):
        sh = empty(f"{n}_Sh{side}", P["_tops"][S + "UpperArm"] - Vector((0, 0, 0.04)), waist)
        attach(part(S + "UpperArm"), sh)
        el = empty(f"{n}_El{side}", P["_tops"][S + "LowerArm"], sh)
        attach(part(S + "LowerArm"), el); attach(part(S + "Hand"), el)
        hj = P["_tops"][S + "UpperLeg"] - Vector((0, 0, 0.03))
        lg = empty(f"{n}_Leg{side}", hj, root)
        attach(part(S + "UpperLeg"), lg)
        kn = empty(f"{n}_Kn{side}", P["_tops"][S + "LowerLeg"], lg)
        attach(part(S + "LowerLeg"), kn); attach(part(S + "Foot"), kn)
        parts.update({"sh" + side: sh, "el" + side: el, "leg" + side: lg, "kn" + side: kn})
        parts["hipj"][side] = hj.copy()
        parts["Lt"] = hj.z - kn.matrix_world.translation.z; parts["Ls"] = kn.matrix_world.translation.z
    for o in list(shirt.values()) + list(pants.values()):
        bpy.data.objects.remove(o, do_unlink=True)
    head = P["Head"].copy(); head.data = P["Head"].data.copy(); head.name = n + "_Head"; col.objects.link(head)
    head.animation_data_clear(); head.matrix_parent_inverse.identity(); head.location = (0, 0, 0); head.rotation_euler = (0, 0, 0)
    head.scale = (1, 1, 1); head.hide_render = head.hide_viewport = False; upd()
    face_uv(head); head.data.materials.clear(); head.data.materials.append(face_mat(n + "Face", look["face"])); attach(head, neck)
    klo, khi = vbounds(P["Head"])
    hr = fit_hair(look["hair"], klo, khi, n + "_Hair", look.get("hair_w", 1.0), look.get("hair_lift", 0.12)); attach(hr, neck, keep_world=True)
    root.rotation_quaternion = (0, 0, 0, 1)  # 180 deg about Z: face the crowd (-Y)
    return parts
