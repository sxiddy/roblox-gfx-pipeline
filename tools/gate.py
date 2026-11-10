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


GATES = {"scene": gate_scene, "body": gate_body, "face": gate_face, "frame": gate_frame, "camera": gate_camera}


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
