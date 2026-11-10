"""Gates: the logged mistakes turned into checks that fail loudly. Run before every preview and render.

Headless (own Blender, never the shared GUI one):
    blender -b scene.blend --python-exit-code 1 -P tools/gate.py -- job.json [scene,body,face,frame,camera]
Inside a style script:
    import gate; gate.run(r"...\\job.json", ["scene", "frame"])     # returns True when nothing FAILs

Prints PASS / FAIL / WARN lines, writes <job>.gate.txt next to the spec, exits 1 on any FAIL.
Nothing is rendered: visibility is ray-cast, so a full run takes seconds.

job.json (all frame values are fractions, x right, y DOWN, like gfx2d grid images). See tools/job_example.json.
    name            job name
    avatar_dir      folder with the fetched avatar's meta.json (freshness check)
    avatar_fresh_days   max age of that fetch in days (default 1; raise only for re-checks of old scenes)
    engine          "CYCLES" | "BLENDER_EEVEE" | "BLENDER_WORKBENCH" (optional)
    allow_names     object names allowed although they look like strays
    support         "ground" (default) | "seat" | "none" (jumping, floating on purpose)
    ground_tol      metres the avatar may hover above its support (default 0.02)
    planned_hidden  avatar parts hidden on purpose (hide_render) e.g. ["Handle3"]
    see_through     objects that do not block the view (glass, rain, alpha cards); volumes are skipped by themselves
    face            {"min_visible": 0.7, "max_turn": 75}   share of the face plate seen, max face-to-lens angle (deg)
    head_frac       head width / frame width          head_xy  [x, y] head centre       tol  (default 0.05)
    props           [{"name": "Tomb", "cell": [x0, y0, x1, y1], "may_cross_head": false}]
    out_of_frame    object or bone names that must not show, e.g. ["Hand.P", "LowerLeg.N"]
    camera          {"elevation": [lo, hi], "azimuth": [lo, hi], "roll": [lo, hi], "lens": [lo, hi], "distance": [lo, hi]}
                    elevation: deg the lens sits above the head; azimuth: deg around the avatar, 0 = straight in
                    front, + = toward the avatar's right (.P); roll: deg; lens: mm; distance: m to the head.
    light           (stage "light", renders two 25% frames, run it by name) {"luma": [80, 130], "face_luma": [70, 215],
                    "max_blown": 0.02, "emit_caps": {"default": 5, "Flame": 30, "Window": 2}, "dark_parts": ["Handle1"],
                    "dark_max": 70, "percent": 25, "samples": 16}
    final           (stage "final", run it by name) {"raw": png, "graded": png, "mask": png, "black_point": [0, 18],
                    "white_min": 170, "saturation": [0.15, 0.75], "max_delta_e": 14}
    motion          (stage "motion", run it by name) {"frames": [1, 240], "armatures": ["Avatar"],
                    "max_deg": {"default": 25, "Hand.P": 40}, "max_frozen": 12, "slide_tol": 0.01,
                    "planted": [{"bone": "Foot.P", "frames": [1, 30]}]}
The default run is the five fast stages; add light / final explicitly: ... -- job.json scene,body,face,frame,camera,light
"""
import json
import math
import os
import sys
import time

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from mathutils.kdtree import KDTree

STAGES = ["scene", "body", "face", "frame", "camera"]
R15 = ["Head", "UpperTorso", "LowerTorso"] + [f"{p}.{s}" for s in "PN"
                                             for p in ("UpperArm", "LowerArm", "Hand", "UpperLeg", "LowerLeg", "Foot")]
PRIMS = {"Plane", "Cube", "Sphere", "Cylinder", "Cone", "Torus", "Icosphere", "Suzanne", "Circle", "Grid"}
LOG = []


def out(level, check, detail=""):
    LOG.append((level, check, detail)); print(f"{level:4} {check}: {detail}")


# ---------------------------------------------------------------- helpers
def arm():
    return bpy.data.objects.get("Avatar")


def dg():
    return bpy.context.evaluated_depsgraph_get()


def verts(o):
    """World-space vertices of the evaluated mesh (bound_box is stale after posing or hiding)."""
    e = o.evaluated_get(dg()); me = e.to_mesh()
    co = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get("co", co); e.to_mesh_clear()
    m = np.array(o.matrix_world)
    return co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]


def avatar_meshes():
    a = arm()
    return [o for o in a.children_recursive if o.type == "MESH" and not o.hide_render] if a else []


def base(o):
    return o.name.split(".")[0] if o.name.split(".")[-1].isdigit() else o.name


def part_meshes(bone):
    return [o for o in avatar_meshes() if o.parent_bone == bone or o.name == bone or o.name.startswith(bone + ".0")]


def bone_axes(name):
    """World side (x), up (y) and facing (z) axes of a pose bone plus its head position."""
    a = arm(); m = a.matrix_world @ a.pose.bones[name].matrix
    return [Vector(m.col[i][:3]).normalized() for i in range(3)], m.translation.copy()


def proj(p):
    s = bpy.context.scene; v = world_to_camera_view(s, s.camera, Vector(p))
    return v.x, 1 - v.y, v.z


def box2d(pts):
    pr = [proj(p) for p in pts]; pr = [p for p in pr if p[2] > 0]
    if not pr:
        return None
    xs = [p[0] for p in pr]; ys = [p[1] for p in pr]
    return min(xs), min(ys), max(xs), max(ys)


def overlap(a, b):
    return a and b and a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def blocks(o, spec):
    """Does this object hide what is behind it? Hidden, camera-invisible, volume-only and listed objects do not."""
    if o.hide_render or not o.visible_camera or o.name in spec.get("see_through", []):
        return False
    mats = [s.material for s in o.material_slots if s.material]
    if mats and all(m.use_nodes and not any(n.type == "OUTPUT_MATERIAL" and n.inputs["Surface"].is_linked
                                           for n in m.node_tree.nodes) for m in mats):
        return False
    return True


def first_hit(origin, target, spec):
    """First blocking object on the way from origin to target, and how far it is from the target."""
    d = Vector(target) - Vector(origin); dist = d.length; d.normalize(); o = Vector(origin); left = dist
    for _ in range(40):
        hit, loc, _n, _i, ob, _m = bpy.context.scene.ray_cast(dg(), o, d, distance=left + 0.05)
        if not hit:
            return None, 0.0
        if blocks(ob, spec):
            return ob, (Vector(target) - loc).length
        left -= (loc - o).length + 1e-4; o = loc + d * 1e-4
        if left <= 0:
            return None, 0.0
    return None, 0.0


def head_mesh():
    kids = part_meshes("Head")
    named = [o for o in kids if base(o) == "Head"]
    pool = named or [o for o in kids if not o.name.startswith("Handle")] or kids
    return min(pool, key=lambda o: np.ptp(verts(o), axis=0).max()) if pool else None


def head_box():
    h = head_mesh()
    return box2d(verts(h)) if h else None


# ---------------------------------------------------------------- gates
def gate_scene(spec):
    s = bpy.context.scene; allow = set(spec.get("allow_names", []))
    a = arm()
    out("PASS" if a and a.type == "ARMATURE" else "FAIL", "scene.avatar", "armature 'Avatar' found" if a else "no armature named 'Avatar'")
    out("PASS" if s.camera else "FAIL", "scene.camera", s.camera.name if s.camera else "scene has no active camera")
    left = [o.name for o in s.objects if base(o) in ("Backdrop", "Halo") and not o.hide_render]
    out("FAIL" if left else "PASS", "scene.stage_leftovers", f"delete {left}" if left else "no Backdrop/Halo")
    vis = [o for o in s.objects if o.type == "MESH" and not o.hide_render and o.name not in allow]
    bare = [o.name for o in vis if not any(sl.material for sl in o.material_slots)]
    out("FAIL" if bare else "PASS", "scene.no_material", f"{bare[:8]}" if bare else "every visible mesh has a material")
    prim = [o.name for o in vis if base(o) in PRIMS and not o.parent]
    out("FAIL" if prim else "PASS", "scene.default_names", f"stray default primitives {prim[:8]} (name them or delete)" if prim else "none")
    if spec.get("engine"):
        ok = s.render.engine.startswith(spec["engine"])
        out("PASS" if ok else "FAIL", "scene.engine", f"{s.render.engine} (spec {spec['engine']})")
    else:
        out("WARN", "scene.engine", f"{s.render.engine}; spec has no 'engine', set it explicitly")
    ad = spec.get("avatar_dir")
    meta = os.path.join(ad, "meta.json") if ad else None
    if not meta or not os.path.exists(meta):
        out("FAIL", "scene.avatar_fresh", "spec needs avatar_dir with meta.json (re-fetch the avatar for every new job)")
    else:
        age = (time.time() - os.path.getmtime(meta)) / 86400; lim = spec.get("avatar_fresh_days", 1)
        out("PASS" if age <= lim else "FAIL", "scene.avatar_fresh", f"fetched {age:.1f} days ago (limit {lim})")


def gate_body(spec):
    a = arm()
    if not a:
        return out("FAIL", "body", "no Avatar")
    meshes = avatar_meshes(); skinned = set()
    for o in meshes:
        if any(m.type == "ARMATURE" for m in o.modifiers):
            skinned |= {g.name for g in o.vertex_groups}
    missing = [b for b in R15 if b in a.pose.bones and not part_meshes(b) and b not in skinned]
    nobone = [b for b in R15 if b not in a.pose.bones]
    out("FAIL" if nobone else "PASS", "body.rig", f"missing bones {nobone}" if nobone else "15 R15 bones")
    out("WARN" if missing else "PASS", "body.parts", f"no mesh on {missing} (fine for chibi only if clothing covers it; look at the preview)" if missing else "every bone carries a mesh")
    hidden = [o.name for o in a.children_recursive if o.type == "MESH" and o.hide_render and base(o) not in spec.get("planned_hidden", []) and o.name not in spec.get("planned_hidden", [])]
    out("FAIL" if hidden else "PASS", "body.hidden", f"hidden but not in planned_hidden: {hidden}" if hidden else "nothing hidden by accident")
    # floating hands: gap between each hand and the rest of the avatar
    cache = {o.name: verts(o) for o in meshes}
    for side in "PN":
        hands = part_meshes(f"Hand.{side}")
        if not hands:
            continue
        rest = [v for n, v in cache.items() if n not in {h.name for h in hands}]
        if not rest:
            continue
        pts = np.concatenate(rest); step = max(1, len(pts) // 20000); pts = pts[::step]
        kd = KDTree(len(pts))
        for i, p in enumerate(pts):
            kd.insert(Vector(p), i)
        kd.balance()
        hv = np.concatenate([cache[h.name] for h in hands])
        gap = min(kd.find(Vector(p))[2] for p in hv[::max(1, len(hv) // 400)])
        out("PASS" if gap <= 0.03 else "FAIL", f"body.hand_attached.{side}", f"gap to the arm {gap * 100:.1f} cm (limit 3)")
    # grounding from evaluated vertices
    sup = spec.get("support", "ground")
    if sup == "none":
        return out("PASS", "body.support", "support none (planned)")
    names = ("LowerTorso", "UpperLeg.P", "UpperLeg.N") if sup == "seat" else None
    pool = [cache[o.name] for o in meshes if not names or o.parent_bone in names or base(o) in names] or list(cache.values())
    allv = np.concatenate(pool); low = allv[allv[:, 2].argmin()]
    mine = {o.name for o in a.children_recursive}; o0 = Vector(low) + Vector((0, 0, 0.05)); gap = None
    for _ in range(40):
        hit, loc, _n, _i, ob, _m = bpy.context.scene.ray_cast(dg(), o0, Vector((0, 0, -1)))
        if not hit:
            break
        if ob.name not in mine and blocks(ob, spec):
            gap = low[2] - loc.z; break
        o0 = loc - Vector((0, 0, 1e-4))
    tol = spec.get("ground_tol", 0.02)
    if gap is None:
        out("FAIL", "body.support", f"nothing under the avatar's lowest point (z {low[2]:.3f}); it floats")
    else:
        out("PASS" if -tol <= gap <= tol else "FAIL", "body.support", f"lowest {'seat' if names else 'body'} point is {gap * 100:+.1f} cm above its support (limit +-{tol * 100:.0f})")


def gate_face(spec):
    h = head_mesh(); cam = bpy.context.scene.camera
    if not h or not cam:
        return out("FAIL", "face", "no head mesh or no camera")
    f = spec.get("face", {}); need = f.get("min_visible", 0.7); max_turn = f.get("max_turn", 75)
    (x, y, z), _ = bone_axes("Head"); v = verts(h); c = Vector(v.mean(axis=0))
    rel = v - np.array(c)
    ex = [(float((rel @ np.array(ax)).min()), float((rel @ np.array(ax)).max())) for ax in (x, y, z)]
    eye = cam.matrix_world.translation
    turn = math.degrees(z.angle(eye - c))
    out("PASS" if turn <= max_turn else "FAIL", "face.turn", f"face is {turn:.0f} deg off the lens (limit {max_turn})")
    seen = total = 0; blockers = {}
    for i in range(9):
        for j in range(9):
            sx = ex[0][0] + (ex[0][1] - ex[0][0]) * (0.19 + 0.62 * i / 8)
            sy = ex[1][0] + (ex[1][1] - ex[1][0]) * (0.18 + 0.60 * j / 8)
            p = c + x * sx + y * sy + z * ex[2][1]
            total += 1
            ob, far = first_hit(eye, p, spec)
            if ob is None or (ob == h and far < (ex[2][1] - ex[2][0]) * 0.35):
                seen += 1
            else:
                blockers[ob.name] = blockers.get(ob.name, 0) + 1
    frac = seen / total; top = sorted(blockers.items(), key=lambda t: -t[1])[:4]
    out("PASS" if frac >= need else "FAIL", "face.visible", f"{frac:.0%} of the face plate reaches the lens (need {need:.0%})" + (f"; blocked by {top}" if top else ""))
    hb = head_box()
    inside = hb and hb[0] >= 0 and hb[1] >= -0.02 and hb[2] <= 1 and hb[3] <= 1.02
    out("PASS" if inside else "WARN", "face.in_frame", f"head box {tuple(round(t, 2) for t in hb)}" if hb else "head behind the camera")


def gate_frame(spec):
    s = bpy.context.scene; tol = spec.get("tol", 0.05); hb = head_box()
    if not hb:
        return out("FAIL", "frame", "head not in front of the camera")
    frac = hb[2] - hb[0]; cx, cy = (hb[0] + hb[2]) / 2, (hb[1] + hb[3]) / 2
    if "head_frac" in spec:
        out("PASS" if abs(frac - spec["head_frac"]) <= tol else "FAIL", "frame.head_frac", f"{frac:.3f} (spec {spec['head_frac']} +-{tol})")
    else:
        out("FAIL", "frame.head_frac", f"measured {frac:.3f} but the spec has no head_frac; measure the reference first")
    if "head_xy" in spec:
        ok = abs(cx - spec["head_xy"][0]) <= tol and abs(cy - spec["head_xy"][1]) <= tol
        out("PASS" if ok else "FAIL", "frame.head_xy", f"({cx:.3f}, {cy:.3f}) (spec {spec['head_xy']} +-{tol})")
    else:
        out("FAIL", "frame.head_xy", f"measured ({cx:.3f}, {cy:.3f}) but the spec has no head_xy")
    for p in spec.get("props", []):
        o = s.objects.get(p["name"])
        if not o or o.hide_render:
            out("FAIL", f"frame.prop.{p['name']}", "missing or hidden"); continue
        pts = verts(o) if o.type == "MESH" else np.array([o.matrix_world.translation])
        if o.type != "MESH" or len(pts) == 0:
            kids = [k for k in o.children_recursive if k.type == "MESH"]
            pts = np.concatenate([verts(k) for k in kids]) if kids else np.array([o.matrix_world.translation])
        b = box2d(pts[::max(1, len(pts) // 3000)])
        if not b:
            out("FAIL", f"frame.prop.{p['name']}", "behind the camera"); continue
        bx, by = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2; c = p.get("cell")
        if c:
            ok = c[0] <= bx <= c[2] and c[1] <= by <= c[3]
            out("PASS" if ok else "FAIL", f"frame.prop.{p['name']}", f"centre ({bx:.2f}, {by:.2f}), planned cell {c}")
        if overlap(b, hb) and not p.get("may_cross_head"):
            out("FAIL", f"frame.prop.{p['name']}.head", f"its box {tuple(round(t, 2) for t in b)} crosses the head box")
    a = arm()
    for n in spec.get("out_of_frame", []):
        objs = part_meshes(n) if a and n in a.pose.bones else [o for o in [s.objects.get(n)] if o and not o.hide_render]
        showing = 0
        for o in objs:
            if o.type != "MESH":
                continue
            v = verts(o); v = v[::max(1, len(v) // 500)]
            showing += sum(1 for p in map(proj, v) if p[2] > 0 and 0.01 < p[0] < 0.99 and 0.01 < p[1] < 0.99)
        out("FAIL" if showing else "PASS", f"frame.out.{n}", "shows in frame: crop tighter or move it" if showing else "out of frame as planned")
    out("PASS", "frame.size", f"{s.render.resolution_x}x{s.render.resolution_y}")


def gate_camera(spec):
    cam = bpy.context.scene.camera; h = head_mesh(); want = spec.get("camera")
    if not cam or not h or not arm():
        return out("FAIL", "camera", "no camera, head or avatar")
    c = Vector(verts(h).mean(axis=0)); d = cam.matrix_world.translation - c
    am = arm().matrix_world.to_3x3(); fwd = (am @ Vector((0, 1, 0))).normalized(); right = (am @ Vector((1, 0, 0))).normalized()
    flat = Vector((d.x, d.y, 0))
    got = {"elevation": math.degrees(math.atan2(d.z, flat.length)),
           "azimuth": math.degrees(math.atan2(flat.dot(right), flat.dot(fwd))),
           "roll": math.degrees(math.asin(max(-1, min(1, Vector(cam.matrix_world.col[0][:3]).normalized().z)))),
           "lens": cam.data.lens, "distance": d.length}
    out("INFO", "camera.measured", ", ".join(f"{k} {v:.1f}" for k, v in got.items()))
    if not want:
        return out("FAIL", "camera.spec", "no 'camera' ranges in the spec: solve them from the reference and assert them")
    for k, v in got.items():
        if k in want:
            lo, hi = want[k]
            out("PASS" if lo <= v <= hi else "FAIL", f"camera.{k}", f"{v:.1f} (spec {lo}..{hi})")
        else:
            out("WARN", f"camera.{k}", f"{v:.1f}, not asserted")


# ---------------------------------------------------------------- light and final (pixels)
def load_px(path):
    """PNG -> float array (h, w, 4) in display values 0..1, top row first."""
    img = bpy.data.images.load(path, check_existing=False); img.colorspace_settings.name = "Non-Color"
    w, h = img.size; a = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[::-1]


def luma(px):
    return (px[..., 0] * 0.2126 + px[..., 1] * 0.7152 + px[..., 2] * 0.0722) * 255


def lab(px):
    c = px[..., :3].astype(np.float64); c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ m.T / np.array([0.9505, 1.0, 1.089])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


def quick_render(path, percent, samples, only_avatar=False):
    s = bpy.context.scene; r = s.render; a = arm()
    keep = ({a} | set(a.children_recursive)) if a else set()
    hid = [o for o in s.objects if only_avatar and o not in keep and o.type not in {"LIGHT", "CAMERA"} and not o.hide_render]
    old = (r.resolution_percentage, r.filepath, r.film_transparent, r.image_settings.file_format, r.image_settings.color_mode)
    for o in hid:
        o.hide_render = True
    r.resolution_percentage = percent; r.filepath = path; r.film_transparent = only_avatar
    r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA"
    if s.render.engine == "CYCLES":
        oc = s.cycles.samples; s.cycles.samples = samples
    bpy.ops.render.render(write_still=True)
    if s.render.engine == "CYCLES":
        s.cycles.samples = oc
    for o in hid:
        o.hide_render = False
    r.resolution_percentage, r.filepath, r.film_transparent, r.image_settings.file_format, r.image_settings.color_mode = old


def emit_strengths():
    """(object, material, strength) for every emissive surface that renders."""
    res = []
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or o.hide_render:
            continue
        for sl in o.material_slots:
            m = sl.material
            if not m or not m.use_nodes:
                continue
            best = 0.0
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED" and "Emission Strength" in n.inputs:
                    col = n.inputs["Emission Color"]
                    lit = col.is_linked or max(col.default_value[:3]) > 0.001
                    st = n.inputs["Emission Strength"]
                    if lit and not st.is_linked:
                        best = max(best, st.default_value)
                elif n.type == "EMISSION" and n.outputs[0].is_linked and not n.inputs["Strength"].is_linked:
                    best = max(best, n.inputs["Strength"].default_value)
            if best > 0:
                res.append((o.name, m.name, best))
    return res


def gate_light(spec):
    """Two small renders (25%, few samples): the real frame and the avatar alone as a mask."""
    L = spec.get("light", {}); caps = L.get("emit_caps", {}); dflt = caps.get("default", 5.0)
    over = []; unlisted = []
    for o, m, st in emit_strengths():
        cap = next((v for k, v in caps.items() if k != "default" and (o.startswith(k) or m.startswith(k))), None)
        if cap is not None and st > cap:
            over.append(f"{o}/{m} {st:.1f}>{cap}")
        elif cap is None and st > dflt:
            unlisted.append(f"{o}/{m} {st:.1f}")
    out("FAIL" if over else "PASS", "light.emit_caps", f"over their cap: {over[:6]}" if over else "listed emitters inside caps")
    if unlisted:
        out("WARN", "light.emit_unlisted", f"above default {dflt} with no cap in spec: {unlisted[:6]}")
    tmp = os.path.join(bpy.app.tempdir, "gate_light"); pct = L.get("percent", 25)
    quick_render(tmp + "_beauty.png", pct, L.get("samples", 16))
    quick_render(tmp + "_mask.png", pct, 1, only_avatar=True)
    px = load_px(tmp + "_beauty.png"); mk = load_px(tmp + "_mask.png")[..., 3] > 0.5; lu = luma(px); h, w = lu.shape
    mean = float(lu.mean()); lo, hi = L.get("luma", [80, 130])
    out("PASS" if lo <= mean <= hi else "FAIL", "light.mean_luma", f"{mean:.0f} (spec {lo}..{hi})")
    blown = float((lu > 250).mean()); lim = L.get("max_blown", 0.02)
    out("PASS" if blown <= lim else "FAIL", "light.blown", f"{blown:.1%} of pixels are pure white (limit {lim:.0%})")
    hb = head_box()
    if mk.mean() > 0.9:
        out("FAIL", "light.mask", f"avatar mask covers {mk.mean():.0%} of the frame; set pieces are parented to the avatar or the film is not transparent, so subject/background numbers below are unreliable")
    if hb and mk.any():
        x0, y0, x1, y1 = [int(max(0, min(1, t)) * s) for t, s in zip(hb, (w, h, w, h))]
        face = np.zeros_like(mk); face[y0:y1, x0:x1] = True; face &= mk
        bg = float(lu[~mk].mean()) if (~mk).any() else 0.0
        if face.any():
            fl = float(lu[face].mean()); flo, fhi = L.get("face_luma", [70, 215])
            out("PASS" if fl > bg else "FAIL", "light.subject_first", f"head luma {fl:.0f} vs background {bg:.0f}")
            out("PASS" if flo <= fl <= fhi else "FAIL", "light.face_luma", f"{fl:.0f} (spec {flo}..{fhi})")
            fb = float((lu[face] > 245).mean())
            out("PASS" if fb <= 0.05 else "FAIL", "light.face_blown", f"{fb:.0%} of the head is washed white (limit 5%)")
        else:
            out("FAIL", "light.subject_first", "head is not in the avatar mask (hidden or out of frame)")
        for name in L.get("dark_parts", []):
            o = bpy.context.scene.objects.get(name); b = box2d(verts(o)) if o else None
            if not b:
                out("FAIL", f"light.dark.{name}", "missing"); continue
            x0, y0, x1, y1 = [int(max(0, min(1, t)) * s) for t, s in zip(b, (w, h, w, h))]
            reg = np.zeros_like(mk); reg[y0:y1, x0:x1] = True; reg &= mk
            v = float(np.median(lu[reg])) if reg.any() else 0.0; cap = L.get("dark_max", 70)
            out("PASS" if v <= cap else "FAIL", f"light.dark.{name}", f"median luma {v:.0f} (must stay under {cap})")
    else:
        out("FAIL", "light.mask", "avatar mask is empty")


def gate_final(spec):
    F = spec.get("final")
    if not F:
        return out("FAIL", "final.spec", "spec needs final {raw, graded, mask}")
    raw, gr, mk = F.get("raw"), F.get("graded"), F.get("mask")
    for k, p in (("raw", raw), ("graded", gr)):
        if not p or not os.path.exists(p):
            return out("FAIL", f"final.{k}", f"file missing: {p}")
    newer = os.path.getmtime(gr) >= os.path.getmtime(raw)
    out("PASS" if newer else "FAIL", "final.fresh", "graded is newer than raw" if newer else "graded is OLDER than the raw render: regrade")
    a, b = load_px(raw), load_px(gr)
    lu = luma(b); bp = float(np.percentile(lu, 2)); wp = float(np.percentile(lu, 99.5))
    lo, hi = F.get("black_point", [0, 18])
    out("PASS" if lo <= bp <= hi else "FAIL", "final.black_point", f"darkest 2% sits at luma {bp:.0f} (spec {lo}..{hi}; higher = milky blacks)")
    wlo = F.get("white_min", 170)
    out("PASS" if wp >= wlo else "FAIL", "final.white_point", f"brightest 0.5% at luma {wp:.0f} (need >= {wlo}; lower = flat, grey image)")
    mx = b[..., :3].max(axis=-1); mn = b[..., :3].min(axis=-1); sat = float(((mx - mn) / np.maximum(mx, 1e-4)).mean())
    slo, shi = F.get("saturation", [0.15, 0.75])
    out("PASS" if slo <= sat <= shi else "FAIL", "final.saturation", f"mean {sat:.2f} (spec {slo}..{shi})")
    if a.shape != b.shape:
        return out("WARN", "final.avatar_colour", f"raw {a.shape[1]}x{a.shape[0]} and graded {b.shape[1]}x{b.shape[0]} differ in size; not compared")
    if mk and os.path.exists(mk):
        m = load_px(mk)
        if m.shape == a.shape:
            sel = m[..., 3] > 0.5
            de = float(np.linalg.norm(lab(a)[sel] - lab(b)[sel], axis=-1).mean()) if sel.any() else 0.0
            cap = F.get("max_delta_e", 14)
            out("PASS" if de <= cap else "FAIL", "final.avatar_colour", f"grade moved the avatar's colours by delta-E {de:.1f} (limit {cap})")
        else:
            out("WARN", "final.avatar_colour", "mask size differs from the render; not compared")
    else:
        out("FAIL", "final.mask", "no avatar mask: grade with --mask so the character keeps its colours")


def gate_motion(spec):
    """Steps through the frames and measures every bone. No rendering."""
    M = spec.get("motion")
    if not M or "frames" not in M:
        return out("FAIL", "motion.spec", "spec needs motion {frames: [first, last]}")
    s = bpy.context.scene; f0, f1 = M["frames"]; names = M.get("armatures", ["Avatar"])
    caps = M.get("max_deg", {}); dcap = caps.get("default", 25.0); planted = M.get("planted", [])
    arms = [bpy.data.objects[n] for n in names if n in bpy.data.objects]
    if len(arms) != len(names):
        return out("FAIL", "motion.armatures", f"missing {set(names) - {a.name for a in arms}}")
    rot = {}; pos = {}
    for f in range(f0, f1 + 1):
        s.frame_set(f)
        for a in arms:
            for pb in a.pose.bones:
                m = a.matrix_world @ pb.matrix
                rot.setdefault((a.name, pb.name), []).append(m.to_quaternion()); pos.setdefault((a.name, pb.name), []).append(m.translation.copy())
    n = f1 - f0; over = {}; flips = {}; worst = (0.0, None, 0); still = np.ones(n, dtype=bool)
    for key, qs in rot.items():
        cap = caps.get(key[1], dcap)
        for i in range(n):
            d = math.degrees(qs[i].rotation_difference(qs[i + 1]).angle); d = min(d, 360 - d)
            mv = (pos[key][i + 1] - pos[key][i]).length
            if d > 0.03 or mv > 0.0003:
                still[i] = False
            if d > 120:
                flips[key] = flips.get(key, 0) + 1
            elif d > cap:
                over[key] = over.get(key, 0) + 1
            if d > worst[0] and d <= 120:
                worst = (d, key, f0 + i)
    out("INFO", "motion.fastest", f"{worst[0]:.1f} deg/frame on {worst[1]} at frame {worst[2]}")
    out("FAIL" if over else "PASS", "motion.speed_cap", f"frames over the cap ({dcap} deg/frame): {dict(sorted(over.items(), key=lambda t: -t[1])[:5])}" if over else f"no bone over {dcap} deg/frame")
    out("FAIL" if flips else "PASS", "motion.flips", f"sudden >120 deg jumps (roll flips): {dict(list(flips.items())[:5])}" if flips else "no rotation flips")
    run = best = 0; at = f0
    for i in range(n):
        run = run + 1 if still[i] else 0
        if run > best:
            best = run; at = f0 + i - run + 1
    lim = M.get("max_frozen", 12)
    out("PASS" if best <= lim else "FAIL", "motion.frozen", f"longest fully frozen stretch {best} frames from frame {at} (limit {lim}); holds must keep breathing")
    tol = M.get("slide_tol", 0.01)
    for p in planted:
        key = (p.get("armature", names[0]), p["bone"]); a0, a1 = p["frames"]
        if key not in pos or a0 < f0 or a1 > f1:
            out("FAIL", f"motion.planted.{p['bone']}", "bone missing or frames outside the checked range"); continue
        pts = pos[key][a0 - f0:a1 - f0 + 1]; slide = max((q - pts[0]).length for q in pts)
        out("PASS" if slide <= tol else "FAIL", f"motion.planted.{p['bone']}", f"moved {slide * 100:.1f} cm while planted in frames {a0}-{a1} (limit {tol * 100:.0f})")
    if not planted:
        out("WARN", "motion.planted", "no planted feet listed in the spec; foot slide was not checked")
    s.frame_set(f0)


GATES = {"scene": gate_scene, "body": gate_body, "face": gate_face, "frame": gate_frame, "camera": gate_camera,
         "light": gate_light, "final": gate_final, "motion": gate_motion}


def run(job, stages=None):
    """Run gates against the open scene. Returns True when no check FAILs."""
    del LOG[:]
    with open(job, encoding="utf-8-sig") as f:
        spec = json.load(f)
    bpy.context.view_layer.update()
    print(f"GATE {spec.get('name', '?')}  file {bpy.data.filepath or '(unsaved)'}")
    for st in stages or STAGES:
        try:
            GATES[st](spec)
        except Exception as e:  # a crashed gate is a failed gate, never a silent pass
            out("FAIL", f"{st}.crash", f"{type(e).__name__}: {e}")
    fails = [l for l in LOG if l[0] == "FAIL"]; warns = [l for l in LOG if l[0] == "WARN"]
    verdict = f"RESULT {'FAIL' if fails else 'PASS'}: {len(fails)} fail, {len(warns)} warn, {len(LOG)} checks"
    print(verdict)
    with open(os.path.splitext(job)[0] + ".gate.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(f"{a:4} {b}: {c}" for a, b, c in LOG) + "\n" + verdict + "\n")
    return not fails


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args:
        print(__doc__); sys.exit(2)
    ok = run(args[0], args[1].split(",") if len(args) > 1 else None)
    sys.exit(0 if ok else 1)
