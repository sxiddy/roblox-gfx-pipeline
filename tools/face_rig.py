"""Face acting for Roblox avatars whose face is painted on the head texture (classic faces).

    import face_rig as fr
    fr.build()                       # once per avatar, after build_exact_gfx.py; adds object "FaceRig"
    fr.pose("smirk")                 # still GFX: set an expression
    fr.pose("glare", frame=40)       # animation: key an expression on a frame
    fr.pose({"f_mouth_open": 0.6}, frame=52)        # any single control
    fr.blink(frame=70)               # 5-frame blink

How it works: the front of the head is sampled into a square "plate" image, the eyes, brows and mouth are cut
out of it as layers, and a thin plate mesh in front of the face shows skin + layers. Each layer moves, turns
and scales in the shader, driven by custom properties on the Avatar armature (all start with "f_"), so every
control can be keyframed. With every control at rest the plate shows the original face unchanged.

Controls (rest value): f_blink_l/r (0..1), f_eye_x, f_eye_y (plate fractions, about +-0.03), f_eye_s (1),
f_brow_l_y, f_brow_r_y, f_brow_l_rot, f_brow_r_rot (radians, + = inner end down = angry), f_brow_show (0..1,
drawn brows for faces that have none), f_mouth_x, f_mouth_y, f_mouth_rot, f_mouth_sx (1), f_mouth_sy (1,
negative flips a smile into a frown), f_mouth_open (0..1). "l"/"r" are the avatar's own left/right.

Limits: needs a face painted on the head texture with two eye shapes. Pupils cannot move apart from the eye.
Check a close crop after build(): build() returns what it found (eyes, brows, mouth) so a wrong split shows.
"""
import bpy
import numpy as np
from mathutils import Vector
from mathutils.interpolate import poly_3d_calc

N = 256            # plate image size
GRID = 40          # plate mesh cells per side
OFFSET = 0.0015    # metres in front of the head surface
REST = {"f_blink_l": 0.0, "f_blink_r": 0.0, "f_eye_x": 0.0, "f_eye_y": 0.0, "f_eye_s": 1.0,
        "f_brow_l_y": 0.0, "f_brow_r_y": 0.0, "f_brow_l_rot": 0.0, "f_brow_r_rot": 0.0, "f_brow_show": 0.0,
        "f_mouth_x": 0.0, "f_mouth_y": 0.0, "f_mouth_rot": 0.0, "f_mouth_sx": 1.0, "f_mouth_sy": 1.0,
        "f_mouth_open": 0.0}
PRESETS = {
    "neutral": {},
    "smirk": {"f_mouth_rot": 0.2, "f_mouth_x": 0.015, "f_brow_show": 1, "f_brow_l_y": 0.02, "f_brow_r_rot": 0.25,
              "f_blink_r": 0.25},
    "grin": {"f_mouth_sx": 1.2, "f_mouth_sy": 1.3, "f_mouth_open": 0.45, "f_brow_l_y": 0.012, "f_brow_r_y": 0.012,
             "f_blink_l": 0.15, "f_blink_r": 0.15},
    "glare": {"f_brow_show": 1, "f_brow_l_rot": 0.42, "f_brow_r_rot": 0.42, "f_brow_l_y": -0.02, "f_brow_r_y": -0.02,
              "f_blink_l": 0.35, "f_blink_r": 0.35, "f_mouth_sy": 0.5, "f_mouth_sx": 0.9},
    "shock": {"f_brow_show": 1, "f_brow_l_y": 0.035, "f_brow_r_y": 0.035, "f_eye_s": 1.18, "f_mouth_sx": 0.55,
              "f_mouth_open": 1.0},
    "sad": {"f_brow_show": 1, "f_brow_l_rot": -0.35, "f_brow_r_rot": -0.35, "f_brow_l_y": 0.01, "f_brow_r_y": 0.01,
            "f_mouth_sy": -0.8, "f_blink_l": 0.2, "f_blink_r": 0.2},
    "blink": {"f_blink_l": 1.0, "f_blink_r": 1.0},
}


def arm():
    return bpy.data.objects["Avatar"]


def head_mesh():
    a = arm()
    kids = [o for o in a.children if o.type == "MESH" and o.parent_bone == "Head" and not o.hide_render and o.name != "FaceRig"]
    named = [o for o in kids if o.name.split(".")[0] == "Head"]
    pool = named or [o for o in kids if not o.name.startswith("Handle")] or kids
    return min(pool, key=lambda o: o.dimensions.length)


def _tex(o):
    """Base colour image of the head and its pixels (h, w, 4), row 0 at the bottom."""
    for sl in o.material_slots:
        m = sl.material
        if not m or not m.use_nodes:
            continue
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED" and n.inputs["Base Color"].is_linked:
                src = n.inputs["Base Color"].links[0].from_node
                seen = 0
                while src.type != "TEX_IMAGE" and seen < 6:
                    ins = [i for i in src.inputs if i.is_linked and i.type in {"RGBA", "VECTOR"}]
                    if not ins:
                        break
                    src = ins[-1].links[0].from_node; seen += 1
                if src.type == "TEX_IMAGE" and src.image:
                    img = src.image; w, h = img.size
                    px = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(px)
                    return m, n, px.reshape(h, w, 4)
    raise RuntimeError("face_rig: the head has no image on Base Color; this face cannot be rigged")


def _hide_overlays(o, seeds):
    """Hide the small loose pieces of the head mesh that sit in front of the face (lash cards, eye rims).
    Some heads are built from loose pieces. DI3STINY: 4064 faces in 77 pieces: a face shell of two 589-face
    halves with eye sockets, eye pieces of 272, eye rims of 96, single lashes of 28 and 6. The plate passed
    behind the small ones and they poked through as jagged triangles. They stay painted on the eye layers.
    Tried and dropped: lifting the plate over them (lumpy cheeks, plate through the hair fringe), hiding only
    the lashes (the rim then poked through), hiding the eye pieces too (the sockets behind them are holes).
    Uses a Mask modifier, nothing is deleted. seeds: polygons with a front-facing surface close behind them."""
    md = o.modifiers.get("FaceRigHide")
    if md:
        o.modifiers.remove(md)
    vg = o.vertex_groups.get("FaceRigHide")
    if vg:
        o.vertex_groups.remove(vg)
    if not seeds:
        return frozenset()
    me = o.data; v2p = {}
    for p in me.polygons:
        for v in p.vertices:
            v2p.setdefault(v, []).append(p.index)
    seen = set(); hidden = set(); limit = max(8, 0.03 * len(me.polygons))
    for s in seeds:
        if s in seen:
            continue
        isl = {s}; stack = [s]
        while stack:
            for v in me.polygons[stack.pop()].vertices:
                for q in v2p[v]:
                    if q not in isl:
                        isl.add(q); stack.append(q)
        seen |= isl
        if len(isl) <= limit:
            hidden |= isl
    if hidden:
        vg = o.vertex_groups.new(name="FaceRigHide")
        vg.add(sorted({v for p in hidden for v in me.polygons[p].vertices}), 1.0, "REPLACE")
        md = o.modifiers.new("FaceRigHide", "MASK"); md.vertex_group = "FaceRigHide"; md.invert_vertex_group = True
    return frozenset(hidden)


def _sample(o, tex, n, frame, skip=(), overlays=None):
    """Shoot n x n rays at the face. Returns colours (n, n, 4, row 0 bottom), valid mask and hit points.
    skip: polygon indices to pass through. overlays: a set that collects polygons with a front-facing surface
    close behind them."""
    c, x, y, z, half, front = frame; eps = front * 1e-4
    me = o.data; uvl = me.uv_layers.active.data; h, w = tex.shape[:2]
    col = np.zeros((n, n, 4), dtype=np.float32); ok = np.zeros((n, n), dtype=bool); pts = np.zeros((n, n, 3), dtype=np.float32)
    for j in range(n):
        for i in range(n):
            p = c + x * (half * (2 * i / (n - 1) - 1)) + y * (half * (2 * j / (n - 1) - 1)) + z * (front * 1.5)
            hit, loc, nor, idx = o.ray_cast(p, -z)
            first = (hit, loc, nor, idx)
            while hit and idx in skip:
                hit, loc, nor, idx = o.ray_cast(loc - z * eps, -z)
            if not hit or nor.dot(z) < 0.3 or (first[1] - loc).dot(z) > front * 0.1:
                # Nothing usable close behind a skipped piece: keep the first hit. Without the distance test
                # the plate dived to surfaces deep inside the head and the head's own eye showed in front.
                hit, loc, nor, idx = first
            if not hit or nor.dot(z) < 0.3:
                continue
            if overlays is not None:
                h2, l2, n2, _i2 = o.ray_cast(loc - z * eps, -z)
                if h2 and n2.dot(z) > 0.3 and (loc - l2).dot(z) < front * 0.1:
                    overlays.add(idx)
            poly = me.polygons[idx]
            wts = poly_3d_calc([me.vertices[v].co for v in poly.vertices], loc)
            u = sum((uvl[li].uv * wt for li, wt in zip(poly.loop_indices, wts)), Vector((0, 0)))
            col[j, i] = tex[int((u.y % 1) * (h - 1) + 0.5), int((u.x % 1) * (w - 1) + 0.5)]
            ok[j, i] = True; pts[j, i] = loc
    # Rays that land exactly on a mesh edge miss. Each miss used to become a transparent spot in the plate
    # (the border feather widened it to ~15 px), and the head's own open eye showed through during a blink.
    # Fill misses that are enclosed by hits from their neighbours.
    todo = ~_grow(~_grow(ok, 3), 3) & ~ok
    for _ in range(8):
        if not todo.any():
            break
        acc_c = np.zeros_like(col); acc_p = np.zeros_like(pts); cnt = np.zeros(ok.shape, dtype=np.float32)
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            kk = np.roll(ok, (dj, di), axis=(0, 1))
            acc_c += np.roll(col, (dj, di), axis=(0, 1)) * kk[..., None]
            acc_p += np.roll(pts, (dj, di), axis=(0, 1)) * kk[..., None]; cnt += kk
        new = todo & (cnt > 0)
        col[new] = acc_c[new] / cnt[new][:, None]; pts[new] = acc_p[new] / cnt[new][:, None]
        ok = ok | new; todo = todo & ~new
    return col, ok, pts


def _grow(m, k=1):
    for _ in range(k):
        g = m.copy(); g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]; m = g
    return m


def _components(mask):
    lab = np.zeros(mask.shape, dtype=np.int32); comps = []; n = mask.shape[0]
    for j0, i0 in zip(*np.nonzero(mask)):
        if lab[j0, i0]:
            continue
        stack = [(j0, i0)]; lab[j0, i0] = len(comps) + 1; px = []
        while stack:
            j, i = stack.pop(); px.append((j, i))
            for dj in (-1, 0, 1):
                for di in (-1, 0, 1):
                    a, b = j + dj, i + di
                    if 0 <= a < n and 0 <= b < n and mask[a, b] and not lab[a, b]:
                        lab[a, b] = len(comps) + 1; stack.append((a, b))
        px = np.array(px)
        comps.append({"px": px, "area": len(px), "cx": px[:, 1].mean() / n, "cy": px[:, 0].mean() / n,
                      "x0": px[:, 1].min() / n, "x1": px[:, 1].max() / n, "y0": px[:, 0].min() / n, "y1": px[:, 0].max() / n})
    return comps


def _split(col, ok):
    """Find eye / brow / mouth pixels on the plate. Side 'r' = avatar's right = plate x > 0.5."""
    skin = np.median(col[ok][:, :3], axis=0)
    feat = ok & (np.linalg.norm(col[..., :3] - skin, axis=-1) > 0.16) & ~_grow(~ok, 5)
    comps = [c for c in _components(feat) if c["area"] >= 10]
    side = lambda c: "r" if c["cx"] > 0.5 else "l"
    eyes = {}
    for s in "lr":
        cand = [c for c in comps if side(c) == s and c["cy"] > 0.4 and abs(c["cx"] - 0.5) > 0.07 and c["area"] >= N * N * 0.0012]
        if cand:
            eyes[s] = max(cand, key=lambda c: c["area"])
    if len(eyes) < 2:
        raise RuntimeError(f"face_rig: found {len(eyes)} eye shape(s) on the head texture; this face cannot be rigged")
    ye = (eyes["l"]["cy"] + eyes["r"]["cy"]) / 2
    eh = max((eyes["l"]["y1"] - eyes["l"]["y0"] + eyes["r"]["y1"] - eyes["r"]["y0"]) / 2, 0.03)
    groups = {k: [] for k in ("eye_l", "eye_r", "brow_l", "brow_r", "mouth")}
    for c in comps:
        if c["y0"] > ye + 0.25 * eh and c["cy"] > ye + 0.7 * eh and c not in eyes.values():
            groups["brow_" + side(c)].append(c)
        elif c["cy"] > ye - 0.9 * eh:
            if abs(c["cx"] - 0.5) > 0.05 or c in eyes.values():
                groups["eye_" + side(c)].append(c)
        elif abs(c["cx"] - 0.5) < 0.33:
            groups["mouth"].append(c)
    layers = {}
    for k, cs in groups.items():
        if not cs:
            continue
        m = np.zeros(ok.shape, dtype=bool)
        for c in cs:
            m[c["px"][:, 0], c["px"][:, 1]] = True
        m = ~_grow(~_grow(m, 4), 4) & ok          # close holes (highlights, skin-coloured gaps inside an eye)
        js, is_ = np.nonzero(m)
        layers[k] = {"mask": m, "c": ((is_.min() + is_.max()) / 2 / (N - 1), (js.min() + js.max()) / 2 / (N - 1)),
                     "w": (is_.max() - is_.min() + 1) / N, "h": (js.max() - js.min() + 1) / N,
                     "top": js.max() / (N - 1)}
    dark = col[eyes["l"]["px"][:, 0], eyes["l"]["px"][:, 1], :3]
    dark = dark[np.argsort(dark.sum(axis=1))[:max(3, len(dark) // 5)]].mean(axis=0)
    return skin, layers, dark, ye, eh


def _inpaint(col, hole, ok):
    out = col.copy(); known = ok & ~hole
    for _ in range(60):
        todo = hole & ~known
        if not todo.any():
            break
        acc = np.zeros_like(out[..., :3]); cnt = np.zeros(hole.shape, dtype=np.float32)
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = np.roll(known, (dj, di), axis=(0, 1)); v = np.roll(out[..., :3], (dj, di), axis=(0, 1))
            acc += v * k[..., None]; cnt += k
        new = todo & (cnt > 0)
        out[new, :3] = acc[new] / cnt[new][:, None]; known = known | new
    return out


def _image(name, arr):
    old = bpy.data.images.get(name)
    if old:
        bpy.data.images.remove(old)
    img = bpy.data.images.new(name, N, N, alpha=True); img.alpha_mode = "STRAIGHT"
    img.pixels.foreach_set(np.ascontiguousarray(arr, dtype=np.float32).ravel()); img.pack()
    return img


def _layer_img(name, col, mask):
    # carry the feature's soft fringe with it (the base under it is flat skin), fading out over 2 px
    a = np.zeros((N, N, 4), dtype=np.float32); core = _grow(mask, 3); soft = _grow(mask, 5)
    a[soft] = col[soft]; a[..., 3] = 0; a[soft, 3] = 0.3; a[_grow(mask, 4), 3] = 0.65; a[core, 3] = 1
    return _image(name, a)


def _drive(nt, node, inp, index, expr, a, **vars_):
    path = f'nodes["{node.name}"].inputs[{inp}].default_value'
    fc = nt.driver_add(path, index) if index is not None else nt.driver_add(path)
    d = fc.driver; d.type = "SCRIPTED"
    for k, prop in vars_.items():
        v = d.variables.new(); v.name = k; v.type = "SINGLE_PROP"
        v.targets[0].id_type = "OBJECT"; v.targets[0].id = a; v.targets[0].data_path = f'["{prop}"]'
    d.expression = expr


def _sock(sockets, ident):
    return next(s for s in sockets if s.identifier == ident)


def _layer_nodes(nt, uv, img, c, a, tx, ty, ang, sx, sy):
    """uv -> move/turn/scale about the layer centre -> image. tx.. are (expression, {var: prop}) pairs."""
    N_ = nt.nodes; L = nt.links
    sub = N_.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; L.new(uv, sub.inputs[0])
    sub.inputs[1].default_value = (c[0], c[1], 0)
    _drive(nt, sub, 1, 0, f"{c[0]:.5f}+({tx[0]})", a, **tx[1]); _drive(nt, sub, 1, 1, f"{c[1]:.5f}+({ty[0]})", a, **ty[1])
    rot = N_.new("ShaderNodeVectorRotate"); rot.rotation_type = "Z_AXIS"; L.new(sub.outputs[0], rot.inputs["Vector"])
    rot.inputs["Center"].default_value = (0, 0, 0)
    ai = list(rot.inputs).index(rot.inputs["Angle"]); _drive(nt, rot, ai, None, ang[0], a, **ang[1])
    div = N_.new("ShaderNodeVectorMath"); div.operation = "DIVIDE"; L.new(rot.outputs[0], div.inputs[0])
    div.inputs[1].default_value = (1, 1, 1)
    _drive(nt, div, 1, 0, sx[0], a, **sx[1]); _drive(nt, div, 1, 1, sy[0], a, **sy[1])
    add = N_.new("ShaderNodeVectorMath"); add.operation = "ADD"; L.new(div.outputs[0], add.inputs[0])
    add.inputs[1].default_value = (c[0], c[1], 0)
    tex = N_.new("ShaderNodeTexImage"); tex.image = img; tex.extension = "CLIP"; tex.interpolation = "Cubic"
    L.new(add.outputs[0], tex.inputs["Vector"])
    return tex


def _over(nt, base, tex, factor_expr, a):
    """Mix a layer over the running colour; factor = layer alpha. Layers are hidden by pushing their UV off the
    image (a driven x offset of 100), not by a driven factor: driven Math-node values rendered stale in EEVEE."""
    N_ = nt.nodes; L = nt.links
    mul = N_.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; L.new(tex.outputs["Alpha"], mul.inputs[0])
    mul.inputs[1].default_value = 1.0
    if factor_expr:
        _drive(nt, mul, 1, None, factor_expr[0], a, **factor_expr[1])
    mix = N_.new("ShaderNodeMix"); mix.data_type = "RGBA"
    L.new(mul.outputs[0], _sock(mix.inputs, "Factor_Float")); L.new(base, _sock(mix.inputs, "A_Color"))
    L.new(tex.outputs["Color"], _sock(mix.inputs, "B_Color"))
    return _sock(mix.outputs, "Result_Color")


def build(debug_dir=None):
    """Build the plate, layers, material and controls. Safe to call again (rebuilds).
    debug_dir: folder to save plate.png (what was sampled) and split.png (what was cut out)."""
    a = arm(); bpy.context.view_layer.update()
    old = bpy.data.objects.get("FaceRig")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    o = head_mesh(); head_mat, bsdf, tex = _tex(o)
    inv = o.matrix_world.inverted().to_3x3(); bm = (a.matrix_world @ a.pose.bones["Head"].matrix).to_3x3()
    x, y, z = [(inv @ Vector(bm.col[i])).normalized() for i in range(3)]
    co = np.array([v.co for v in o.data.vertices]); c = Vector(co.mean(axis=0)); rel = co - np.array(c)
    ex = [np.ptp(rel @ np.array(ax)) for ax in (x, y, z)]
    half = 0.43 * min(ex[0], ex[1]); frame = (c, x, y, z, half, ex[2])
    over = set(); col, ok, dense_pts = _sample(o, tex, N, frame, overlays=over)
    hidden = _hide_overlays(o, over)
    if ok.mean() < 0.4:
        raise RuntimeError("face_rig: under 40% of the face plate hit the head; is the head mesh the right object?")
    skin, layers, dark, ye, eh = _split(col, ok)
    if debug_dir:
        dbg = col.copy(); dbg[..., 3] = 1; im = _image("FaceRig_dbg_plate", dbg)
        im.filepath_raw = debug_dir + "/plate.png"; im.file_format = "PNG"; im.save()
        dbg = np.zeros_like(col); dbg[..., 3] = 1
        for i, (k, l) in enumerate(sorted(layers.items())):
            dbg[l["mask"], :3] = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1)][i % 5]
        im = _image("FaceRig_dbg_split", dbg); im.filepath_raw = debug_dir + "/split.png"; im.file_format = "PNG"; im.save()
        print("FACE_RIG skin", np.round(skin, 2), {k: (round(l["w"], 2), round(l["h"], 2), int(l["mask"].sum())) for k, l in layers.items()})
    hole = np.zeros(ok.shape, dtype=bool)
    for l in layers.values():
        hole |= _grow(l["mask"], 7)
    # Fill with flat skin. A diffusion fill dragged the grey/white fringe of the eye inward and left a ghost
    # eye in the base, which showed whenever the eye layer was hidden (blink).
    # The fill takes the local skin tone (clean skin pixels only, spread inward, then blurred): one flat median
    # colour left a pale patch around a closed eye wherever the face texture is shaded.
    clean = ok & ~hole & (np.linalg.norm(col[..., :3] - skin, axis=-1) < 0.09)
    fill = _inpaint(col, ~clean, clean)[..., :3]
    for _ in range(3):
        p = np.pad(fill, ((6, 6), (6, 6), (0, 0)), mode="edge"); cs = np.cumsum(np.cumsum(p, axis=0), axis=1)
        cs = np.pad(cs, ((1, 0), (1, 0), (0, 0)))
        fill = (cs[13:, 13:] - cs[:-13, 13:] - cs[13:, :-13] + cs[:-13, :-13]) / 169.0
    base = col.copy(); base[hole & ok, :3] = fill[hole & ok]
    ring = _grow(hole, 3) & ~hole & ok
    base[ring, :3] = base[ring, :3] * 0.5 + fill[ring] * 0.5
    edge = ok.copy(); alpha = np.zeros(ok.shape, dtype=np.float32)
    for k in range(8):                      # feather the plate border into the head
        alpha += edge / 8.0
        edge = ~_grow(~edge, 1)
    base[..., 3] = alpha
    imgs = {"base": _image("FaceRig_base", base)}
    for k, l in layers.items():
        imgs[k] = _layer_img("FaceRig_" + k, col, l["mask"])
    jj, ii = np.mgrid[0:N, 0:N] / (N - 1.0)
    drawn = {}
    for s in "lr":                          # drawn brows for faces without them
        if "brow_" + s in layers:
            continue
        e = layers["eye_" + s]; bc = (e["c"][0], e["top"] + 0.4 * e["h"]); hw = 0.5 * e["w"]; ht = max(1.5 / N, 0.045 * e["h"])
        dx = np.clip(np.abs(ii - bc[0]) - (hw - ht), 0, None); d = np.sqrt(dx ** 2 + (jj - bc[1]) ** 2)
        m = d <= ht; arr = np.zeros((N, N, 4), dtype=np.float32); arr[..., :3] = dark * 0.65 + skin * 0.35
        arr[..., 3] = np.clip((ht * 1.35 - d) / (ht * 0.35), 0, 1)
        imgs["brow_" + s] = _image("FaceRig_brow_" + s, arr); drawn[s] = True
        layers["brow_" + s] = {"mask": m, "c": bc, "w": 2 * hw, "h": 2 * ht}
    mo = layers.get("mouth")
    for s in "lr":                          # closed-eye lid line, shown when the eye is nearly shut
        e = layers["eye_" + s]; hw = 0.5 * e["w"]; ht = max(1.5 / N, 0.05 * e["h"])
        yy = e["c"][1] - 0.12 * e["h"] * (1 - ((ii - e["c"][0]) / hw) ** 2)          # shallow downward arc
        d = np.sqrt(np.clip(np.abs(ii - e["c"][0]) - hw, 0, None) ** 2 + (jj - yy) ** 2)
        arr = np.zeros((N, N, 4), dtype=np.float32); arr[..., :3] = dark
        arr[..., 3] = np.clip((ht * 1.35 - d) / (ht * 0.35), 0, 1)
        imgs["lid_" + s] = _image("FaceRig_lid_" + s, arr)
    mc = mo["c"] if mo else (0.5, max(0.12, ye - 1.15 * eh)); mw = mo["w"] if mo else 0.2
    d = np.sqrt(((ii - mc[0]) / (0.36 * mw)) ** 2 + ((jj - mc[1]) / (0.30 * mw)) ** 2)
    arr = np.zeros((N, N, 4), dtype=np.float32); arr[..., :3] = np.array([0.16, 0.03, 0.05]) * 0.6 + dark * 0.4
    arr[..., 3] = np.clip((1.0 - d) / 0.12, 0, 1)
    imgs["open"] = _image("FaceRig_open", arr)
    for k, v in REST.items():
        a[k] = float(v)
    # plate mesh
    g = GRID + 1; _c2, ok2, pts = _sample(o, tex, g, frame)
    verts = []; index = {}; faces = []; uvs = []
    off = z * (OFFSET / max(o.matrix_world.to_scale()))
    # The plate is a smooth cover over the finely sampled face, not a copy of the coarse grid hits. On heads
    # built from loose pieces the eye piece steps up to 24 mm from the face shell (measured); a plate on the
    # grid hits sat behind those steps and the head's own eye showed as a ring during a blink. Tried and
    # dropped: per-vertex highest point (lumpy cheeks), a 96-cell plate hugging the hits (eyeball relief and
    # facets in the shading), one constant push forward (plate edge off the jaw).
    zv = np.array(z, dtype=np.float32); depth = (dense_pts @ zv).astype(np.float32); w = ok.astype(np.float32)
    rb = 2 * int(np.ceil((N - 1) / GRID)); kb = 2 * rb + 1
    def blur(arr):
        pd = np.pad(arr, rb, mode="edge"); cs = np.pad(np.cumsum(np.cumsum(pd, axis=0), axis=1), ((1, 0), (1, 0)))
        return cs[kb:, kb:] - cs[:-kb, kb:] - cs[kb:, :-kb] + cs[:-kb, :-kb]
    wsum = np.maximum(blur(w), 1e-6); env = depth * w
    for _ in range(12):
        env = np.maximum(blur(env * w) / wsum, depth * w)
    env = blur(env * w) / wsum                               # last pass smooths ...
    core = ~_grow(~ok, 3 * rb)                               # ... and the inside rises by what that took away
    env += max(float((depth - env)[core].max()), 0.0) if core.any() else 0.0
    gi = np.round(np.arange(g) * (N - 1) / GRID).astype(int)
    lift = np.clip(env[np.ix_(gi, gi)] - pts @ zv, 0, None) * ok2
    inner = ok2.copy(); fade = np.zeros(ok2.shape, dtype=np.float32)
    for _ in range(4):                      # no lift at the plate border, so the edge stays on the head
        inner = ~_grow(~inner, 1); inner[0] = inner[-1] = False; inner[:, 0] = inner[:, -1] = False
        fade += inner / 4.0
    lift = lift * fade * fade * (3 - 2 * fade)
    for j in range(g):
        for i in range(g):
            if ok2[j, i]:
                index[(j, i)] = len(verts); verts.append(Vector(pts[j, i]) + z * float(lift[j, i]) + off)
    for j in range(GRID):
        for i in range(GRID):
            q = [(j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)]
            if all(k in index for k in q):
                faces.append([index[k] for k in q]); uvs += [(k[1] / GRID, k[0] / GRID) for k in q]
    me = bpy.data.meshes.new("FaceRig"); me.from_pydata(verts, [], faces); me.update()
    uv = me.uv_layers.new(name="plate")
    for li, t in enumerate(uvs):
        uv.data[li].uv = t
    for p in me.polygons:
        p.use_smooth = True
    plate = bpy.data.objects.new("FaceRig", me); o.users_collection[0].objects.link(plate)
    plate.parent = a; plate.parent_type = "BONE"; plate.parent_bone = "Head"
    plate.matrix_parent_inverse = o.matrix_parent_inverse.copy(); plate.matrix_basis = o.matrix_basis.copy()
    plate.visible_shadow = False
    # material
    old = bpy.data.materials.get("FaceRigMat")
    if old:
        bpy.data.materials.remove(old)
    mat = bpy.data.materials.new("FaceRigMat"); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
    outn = nt.nodes.new("ShaderNodeOutputMaterial"); pb = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(pb.outputs[0], outn.inputs["Surface"])
    for nm in ("Roughness", "Specular IOR Level", "Metallic"):
        if nm in bsdf.inputs and not bsdf.inputs[nm].is_linked:
            pb.inputs[nm].default_value = bsdf.inputs[nm].default_value
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "plate"; U = uvn.outputs[0]
    bt = nt.nodes.new("ShaderNodeTexImage"); bt.image = imgs["base"]; bt.extension = "EXTEND"; nt.links.new(U, bt.inputs["Vector"])
    nt.links.new(bt.outputs["Alpha"], pb.inputs["Alpha"])
    run = bt.outputs["Color"]; no = ("0", {}); one = ("1", {})
    mxy = (("mx", {"mx": "f_mouth_x"}), ("my", {"my": "f_mouth_y"}))
    if mo:
        t = _layer_nodes(nt, U, imgs["mouth"], mc, a, ("mx + 100 * (mo >= 0.02)", {"mx": "f_mouth_x", "mo": "f_mouth_open"}), mxy[1], ("mr", {"mr": "f_mouth_rot"}),
                         ("sx if abs(sx) > 0.05 else 0.05", {"sx": "f_mouth_sx"}), ("sy if abs(sy) > 0.05 else 0.05", {"sy": "f_mouth_sy"}))
        run = _over(nt, run, t, None, a)
    t = _layer_nodes(nt, U, imgs["open"], mc, a, ("mx + 100 * (mo < 0.02)", {"mx": "f_mouth_x", "mo": "f_mouth_open"}), mxy[1], ("mr", {"mr": "f_mouth_rot"}),
                     ("0.35 + 0.65 * sx", {"sx": "f_mouth_sx"}), ("0.06 + 0.94 * mo", {"mo": "f_mouth_open"}))
    run = _over(nt, run, t, None, a)
    exy = (("ex", {"ex": "f_eye_x"}), ("ey", {"ey": "f_eye_y"}))
    for s in "lr":
        e = layers["eye_" + s]
        t = _layer_nodes(nt, U, imgs["eye_" + s], e["c"], a, ("ex + 100 * (b > 0.85)", {"ex": "f_eye_x", "b": "f_blink_" + s}), exy[1], no, ("es", {"es": "f_eye_s"}),
                         ("es * (1 - 0.8 * b)", {"es": "f_eye_s", "b": "f_blink_" + s}))
        run = _over(nt, run, t, None, a)
        t = _layer_nodes(nt, U, imgs["lid_" + s], e["c"], a, ("ex + 100 * (b <= 0.85)", {"ex": "f_eye_x", "b": "f_blink_" + s}), exy[1], no, ("es", {"es": "f_eye_s"}), one)
        run = _over(nt, run, t, None, a)
        b = layers["brow_" + s]; sign = "" if s == "l" else "-"
        t = _layer_nodes(nt, U, imgs["brow_" + s], b["c"], a, ("100 * (bs < 0.5)", {"bs": "f_brow_show"}) if drawn.get(s) else no, ("by", {"by": f"f_brow_{s}_y"}),
                         (f"{sign}br", {"br": f"f_brow_{s}_rot"}), one, one)
        run = _over(nt, run, t, None, a)
    nt.links.new(run, pb.inputs["Base Color"])
    me.materials.append(mat)
    # Blender evaluates a driver once while it is still half built, marks it invalid and then writes 0 (a zero
    # scale = black face). Re-assigning the expression clears that flag.
    for fc in nt.animation_data.drivers:
        fc.driver.expression = fc.driver.expression
    a.update_tag(); nt.update_tag(); bpy.context.view_layer.update()
    bad = [fc.data_path for fc in nt.animation_data.drivers if not fc.driver.is_valid]
    if bad:
        raise RuntimeError(f"face_rig: {len(bad)} drivers are invalid, e.g. {bad[0]}")
    return {"found": sorted(k for k in layers if not (k.startswith("brow") and drawn.get(k[-1]))),
            "drawn_brows": sorted(drawn), "plate_faces": len(faces), "coverage": round(float(ok.mean()), 2),
            "hidden_overlay_faces": len(hidden),
            "max_lift_mm": round(float(lift.max() * max(o.matrix_world.to_scale())) * 1000, 1)}


def pose(expr="neutral", frame=None):
    """Set an expression (preset name or {control: value}); with frame, key every control there."""
    a = arm(); vals = dict(REST); vals.update(PRESETS[expr] if isinstance(expr, str) else expr)
    for k, v in vals.items():
        a[k] = float(v)
        if frame is not None:
            a.keyframe_insert(data_path=f'["{k}"]', frame=frame)
    a.update_tag(); s = bpy.context.scene; s.frame_set(s.frame_current)      # drivers must re-run before a render
    return vals


def blink(frame, length=5):
    """Close and reopen both eyes around `frame` without touching the rest of the expression."""
    a = arm(); mid = frame + length // 2
    for s in "lr":
        k = f"f_blink_{s}"; rest = float(a[k])
        for f, v in ((frame, rest), (mid, 1.0), (frame + length, rest)):
            a[k] = v; a.keyframe_insert(data_path=f'["{k}"]', frame=f)
        a[k] = rest
