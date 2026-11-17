"""Hands kit (docs/SUPERIOR_PLAN.md step 9): swap an R15 block hand for a chunky five-finger hand in a preset shape.
    import hands_kit as hk
    hk.add("both", "relaxed")        # builds HandKit.P / HandKit.N on the Hand bones, hides the block hands
    hk.shape("P", "grip")            # rebuild one hand in another shape
    hk.remove()                      # delete the kit hands, show the blocks again
Shapes: open, relaxed, fist, grip, point. The hand is sized from the block hand it replaces (rest pose) and takes
its skin colour from the block hand's texture. It is a static mesh per shape: change shape per shot, not per frame.
This changes the avatar's look, so the owner decides per job. Add "Hand_P", "Hand_N" to the job's planned_hidden.
Demo sheet (own headless Blender):
    blender -b --factory-startup -P tools/hands_kit.py -- demo AVATAR_DIR OUT.png

Plan for the demo, written before any Blender call (avatar faces +Y, his right = +X):
  hand close-ups  right arm: upper arm 15 deg forward, forearm 75 deg more, so the fingers point at +Y and the palm
                  faces his left. Camera 0.55 m from the hand on his front-left, slightly above, 60 mm, square frame:
                  it sees the palm, the thumb on top and the finger curl. One tile per shape plus the block hand.
  body tiles      idle pose, camera straight in front at chest height, 50 mm, waist-up with both hands in frame:
                  one tile with the block hands, one with "relaxed", to judge size against the body.
  light           one soft key front-left-high, one cool rim behind right, dark grey world."""
import math, os, sys
try:
    import bpy, bmesh
    from mathutils import Matrix, Vector
except ImportError:  # system Python: only the `sheet` mode works
    bpy = None

# per finger (index, middle, ring, pinky): curl in degrees at the three joints; spread toward the thumb side;
# thumb: base direction and curl target as (down the hand, toward the thumb side, out of the palm), then curl.
_F = lambda a, b, c: [(a, b, c)] * 4
SHAPES = {
    "open":    dict(curl=_F(6, 8, 6), spread=(9, 3, -3, -10), thumb=((0.55, 0.75, 0.2), (0.3, 0.0, 1.0), 10)),
    "relaxed": dict(curl=[(10, 14, 10), (14, 18, 12), (18, 22, 14), (22, 26, 16)], spread=(4, 1, -2, -5),
                    thumb=((0.7, 0.5, 0.45), (0.5, -0.2, 1.0), 20)),
    "fist":    dict(curl=_F(85, 100, 60), spread=(0, 0, 0, 0), thumb=((0.5, 0.3, 0.8), (0.4, -1.0, 0.3), 55)),
    "grip":    dict(curl=_F(60, 65, 35), spread=(0, 0, 0, 0), thumb=((0.45, 0.35, 0.8), (0.3, -1.0, 0.4), 30)),
    "point":   dict(curl=[(4, 5, 4), (85, 100, 60), (85, 100, 60), (85, 100, 60)], spread=(2, 0, 0, 0),
                    thumb=((0.5, 0.3, 0.8), (0.4, -1.0, 0.3), 55)),
}
_LEN = (0.95, 1.0, 0.93, 0.78); _SEG = (0.42, 0.32, 0.26)


def _arm(arm=None):
    return arm or bpy.data.objects.get("Avatar") or next(o for o in bpy.data.objects if o.type == "ARMATURE")


def _blocks(a, side):
    return [o for o in a.children_recursive if o.type == "MESH" and o.parent_bone == "Hand." + side and not o.name.startswith("HandKit")]


def _toward(v, target, deg):
    """Rotation that turns v toward target by deg."""
    ax = v.cross(target)
    return Matrix.Rotation(math.radians(deg), 3, ax.normalized()) if ax.length > 1e-6 else Matrix.Identity(3)


def _skin(block):
    """Median colour of the block hand's texture under its own UVs (linear); falls back to the material colour."""
    m = block.data.materials[0] if block.data.materials else None
    b = m and m.node_tree and m.node_tree.nodes.get("Principled BSDF")
    if not b:
        return (0.8, 0.6, 0.5)
    ln = b.inputs["Base Color"].links
    node = ln[0].from_node if ln else None
    while node and node.type != "TEX_IMAGE":
        nxt = [l.from_node for i in node.inputs for l in i.links]
        node = nxt[0] if nxt else None
    if not node or not node.image or not block.data.uv_layers:
        return tuple(b.inputs["Base Color"].default_value[:3])
    import numpy as np
    img = node.image; w, h = img.size; px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, -1)
    uv = np.array([d.uv[:] for d in block.data.uv_layers.active.data], dtype=np.float32) % 1.0
    c = px[(uv[:, 1] * (h - 1)).astype(int), (uv[:, 0] * (w - 1)).astype(int), :3]
    c = np.median(c, axis=0)
    if img.colorspace_settings.name == "sRGB":
        c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return tuple(float(v) for v in c)


def _box(bm, centre, t, w, l, st, sw, sl):
    """Box with half-axes along unit vectors t, w, l and full sizes st, sw, sl."""
    vs = [bm.verts.new(centre + t * (a * st / 2) + w * (b * sw / 2) + l * (c * sl / 2)) for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)]
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([vs[i] for i in f])


def _mesh(lo, hi, sgn, name):
    """Hand in armature rest space inside the block's box lo..hi. sgn +1 = his right hand (palm faces -X)."""
    S = SHAPES[name]; bm = bmesh.new()
    d = Vector((0, 0, -1)); n = Vector((-sgn, 0, 0)); s = Vector((0, 1, 0))
    L = hi.z - lo.z; W = (hi.y - lo.y) * 0.9; T = (hi.x - lo.x) * 0.42
    c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z)); PL = 0.48 * L; FL = 0.5 * L
    _box(bm, c + d * (PL / 2 - 0.015 * L), n, s, d, T, W, PL + 0.03 * L)
    fw = W * 0.215
    for i in range(4):
        R = _toward(d, s, S["spread"][i]); fd, fn, fs = R @ d, R @ n, R @ s
        p = c + d * (PL - 0.02 * L) + s * (W * (0.375 - 0.25 * i))
        for j, frac in enumerate(_SEG):
            R = _toward(fd, fn, S["curl"][i][j]); fd, fn, fs = R @ fd, R @ fn, R @ fs
            ln = FL * _LEN[i] * frac
            _box(bm, p + fd * (ln / 2), fn, fs, fd, T * (0.85 - 0.07 * j), fw * (1 - 0.06 * j), ln * 1.14)
            p = p + fd * ln
    base, target, curl = S["thumb"]
    vec = lambda k: (d * k[0] + s * k[1] + n * k[2]).normalized()
    td = vec(base); tt = vec(target); p = c + d * (PL * 0.3) + s * (W / 2 - 0.02 * L) + n * (T * 0.15)
    tw = (td.cross(n)).normalized(); tn = tw.cross(td).normalized(); TL = 0.4 * L
    for j, frac in enumerate((0.55, 0.45)):
        if j:
            R = _toward(td, tt, curl); td, tn, tw = R @ td, R @ tn, R @ tw
        ln = TL * frac
        _box(bm, p + td * (ln / 2), tn, tw, td, T * (0.9 - 0.1 * j), W * (0.27 - 0.03 * j), ln * 1.16)
        p = p + td * ln
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("HandKit"); bm.to_mesh(me); bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    return me, L


def add(side="both", shape="relaxed", arm=None, hide_block=True):
    a = _arm(arm); out = []
    for sd in ("P", "N") if side == "both" else (side,):
        blocks = _blocks(a, sd)
        if not blocks:
            raise RuntimeError(f"no block hand on Hand.{sd}")
        old = bpy.data.objects.get("HandKit." + sd)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        # rest-space maths only, no pose switching (a REST switch was not re-evaluated and misplaced the hand)
        bone = a.data.bones["Hand." + sd]; rest = bone.matrix_local @ Matrix.Translation((0, bone.length, 0))
        pts = [rest @ b.matrix_parent_inverse @ b.matrix_basis @ v.co for b in blocks for v in b.data.vertices]
        lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
        me, L = _mesh(lo, hi, 1 if (lo.x + hi.x) > 0 else -1, shape)
        o = bpy.data.objects.new("HandKit." + sd, me); bpy.context.scene.collection.objects.link(o)
        m = bpy.data.materials.get("HandKitSkin")
        if not m:
            m = bpy.data.materials.new("HandKitSkin"); m.use_nodes = True
            bs = m.node_tree.nodes["Principled BSDF"]; bs.inputs["Base Color"].default_value = (*_skin(blocks[0]), 1)
            bs.inputs["Roughness"].default_value = 0.5
        me.materials.append(m)
        bv = o.modifiers.new("Round", "BEVEL"); bv.width = 0.055 * L; bv.segments = 4; bv.limit_method = "ANGLE"
        o.parent = a; o.parent_type = "BONE"; o.parent_bone = "Hand." + sd
        o.matrix_parent_inverse = rest.inverted(); bpy.context.view_layer.update()
        o["shape"] = shape
        for b in blocks:
            b.hide_render = b.hide_viewport = hide_block
        out.append(o)
    return out


def shape(side, name, arm=None):
    return add(side, name, arm)


def remove(arm=None):
    a = _arm(arm)
    for sd in "PN":
        o = bpy.data.objects.get("HandKit." + sd)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
        for b in _blocks(a, sd):
            b.hide_render = b.hide_viewport = False


def _demo(avatar, out):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(root, "tools"))
    G = {"__name__": "bx", "AVATAR_DIR": avatar, "POSE": "idle"}
    exec(open(os.path.join(root, "tools", "build_exact_gfx.py"), encoding="utf-8").read(), G)
    import gfx_kit as k
    for o in list(bpy.data.objects):
        if o.name in ("Backdrop", "Halo") or o.type == "LIGHT":
            bpy.data.objects.remove(o, do_unlink=True)
    s = bpy.context.scene; a = k.arm(); tmp = os.path.splitext(out)[0] + "_tiles"; os.makedirs(tmp, exist_ok=True)
    if not s.camera:
        c = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); s.collection.objects.link(c); s.camera = c
    s.render.resolution_x = s.render.resolution_y = 560; s.camera.data.dof.use_dof = False

    def setrot(bone, ypr):
        pb = a.pose.bones[bone]; pb.rotation_mode = "QUATERNION"
        y, p, r = (math.radians(v) for v in ypr)
        R = Matrix.Rotation(y, 3, "Z") @ Matrix.Rotation(p, 3, "X") @ Matrix.Rotation(r, 3, "Y")
        B = pb.bone.matrix_local.to_3x3(); pb.rotation_quaternion = (B.inverted() @ R @ B).to_quaternion()
    k.world((0.03, 0.032, 0.04), 1.0); k.setup_cycles(64, "AgX - Punchy", 0.0); tiles = []

    def shot(tag, target, cam, lens):
        for o in [o for o in s.objects if o.type == "LIGHT"]:
            bpy.data.objects.remove(o, do_unlink=True)
        k.place_camera(cam, target, lens)
        k.area("Key", target + Vector((-0.9, 1.1, 0.9)), target, 60, 0.7, (1.0, 0.9, 0.8))
        k.area("Rim", target + Vector((0.9, -0.8, 0.5)), target, 60, 0.4, (0.6, 0.75, 1.0))
        p = os.path.join(tmp, tag + ".png"); k.render(p, 100, 64); tiles.append(p)
    H = k.head_center(); chest = Vector((H.x, H.y, H.z * 0.62))
    shot("body_block", chest, chest + Vector((0, 2.3, 0.05)), 50)
    add("both", "relaxed"); shot("body_relaxed", chest, chest + Vector((0, 2.3, 0.05)), 50)
    remove(); setrot("UpperArm.P", (0, 15, 0)); setrot("LowerArm.P", (0, 75, 0)); k.upd()
    hand = lambda: a.matrix_world @ ((a.pose.bones["Hand.P"].head + a.pose.bones["Hand.P"].tail) / 2)
    cam = lambda: hand() + Vector((-0.62, 0.42, 0.24))
    shot("hand_block", hand(), cam(), 60)
    for nm in SHAPES:
        add("P", nm); shot("hand_" + nm, hand(), cam(), 60)
    print("SKIN", tuple(round(v, 3) for v in bpy.data.materials["HandKitSkin"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value[:3]))
    print("TILES", tmp, "-> now run:  python -I tools/hands_kit.py sheet", tmp, out)


def _sheet(tiles_dir, out):
    """System Python (Blender's Python has no Pillow): tile the demo renders 4 x 2 with their names."""
    from PIL import Image, ImageDraw
    order = ["body_block", "body_relaxed", "hand_block"] + ["hand_" + n for n in SHAPES]
    ims = [Image.open(os.path.join(tiles_dir, n + ".png")).convert("RGB") for n in order]; w = ims[0].width
    sheet = Image.new("RGB", (w * 4, w * 2), (10, 10, 12))
    for i, (im, n) in enumerate(zip(ims, order)):
        ImageDraw.Draw(im).text((10, 8), n, fill=(255, 255, 255)); sheet.paste(im, ((i % 4) * w, (i // 4) * w))
    sheet.save(out); print("SHEET", out)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if args and args[0] == "demo":
        _demo(args[1], args[2])
    elif args and args[0] == "sheet":
        _sheet(args[1], args[2])
