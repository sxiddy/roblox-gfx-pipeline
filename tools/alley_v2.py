"""Bio_IsHere neon alley v2 (docs/SUPERIOR_PLAN.md step 8, the GFX redo). Own headless Blender:
    blender -b --factory-startup -P tools/alley_v2.py -- build              (saves alley_v2/scene.blend, runs the gates)
    blender -b alley_v2/scene.blend -P tools/alley_v2.py -- render 50 64 prev1
    blender -b alley_v2/scene.blend -P tools/alley_v2.py -- render 100 256 alley_v2_raw
    blender -b alley_v2/scene.blend -P tools/alley_v2.py -- passes          (mask, hair, emission, depth, normal)

Pose and camera plan (avatar faces +Y, his right = +X = screen-LEFT; yaw + = his left, pitch + = chin up, roll + = his left):
  camera  tripod, 4:5 portrait 1080x1350, 40 mm, f/2.8, no roll. 14 deg to his left and 18 deg below the head, about
          1.4 m from it (camera z = head z - dist*sin 18, asserted above 0.2 m). Head 28% of the width (frame_head
          number, gate reads x0.8) centred at (0.44, 0.35): upper third, left of centre so the neon sits upper right.
  body    whole body leans back 12 deg as a plank, feet about 0.3 m out from the wall, back of the head on the wall.
          Chest turned 6 deg to the lens. Legs straight (cut at mid-thigh by the frame bottom, feet out of frame).
  head    8 deg more yaw to the lens (face about 0 deg off in yaw), chin down 8 deg in world terms (20 deg against
          the lean), so he looks down his nose at a lens 10 deg below his eye line. Roll 7 deg to his left.
  arms    upper arms hang beside the torso, forearms folded behind the hips so both block hands are hidden behind
          the body (hands behind the back; solved by counting visible hand vertices, not by eye).
  frame   top: wall, neon and hair; left edge: his right upper arm and a slice of alley; right edge: his left upper
          arm and the wall with the neon ring; bottom: thighs.
  set     he leans on the corner of a building. Screen right: close concrete wall with a wordless neon (a ring with
          a zigzag grin, no letters). Screen left above his shoulder: the alley wall 2 m away with a lit window, a
          sodium lamp, pipes, a small neon triangle, sagging cables, back-lit rain. Wet asphalt and a dumpster are
          built but sit below this low camera's view (reported, not hidden).
  light   one warm sodium key front-left-high 130 W, purple rim from screen right 110 W, teal fill 4 W, no world haze.
Tools: build_exact_gfx.py, gfx_kit.py (frame_head, pbr, area, render_mask), gate.py, then tools/finish.py."""
import json, math, os, random, sys
import bpy, bmesh
from mathutils import Matrix, Vector

ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
OUTDIR = os.path.join(ROOT, "gfx_output", "Bio_IsHere")
OUT = os.path.join(OUTDIR, "alley_v2")
AVATAR = os.path.join(ROOT, "avatars", "Bio_IsHere_2026-11-16")
argv = sys.argv[sys.argv.index("--") + 1:]; MODE = argv[0]
sys.path.insert(0, os.path.join(ROOT, "tools"))
LEAN, AZ, EL, LENS, HEAD_FRAC, HEAD_XY, DMAX = 12.0, 14.0, 18.0, 40, 0.28, (0.44, 0.35), 14.0
SODIUM, PURPLE, PINK = (1.0, 0.62, 0.28), (0.55, 0.14, 1.0), (1.0, 0.15, 0.55)


def wv(o):
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); mw = e.matrix_world
    return [mw @ v.co for v in e.data.vertices]


def build():
    os.makedirs(OUT, exist_ok=True)
    G = {"__name__": "bx", "AVATAR_DIR": AVATAR, "POSE": "idle"}
    exec(open(os.path.join(ROOT, "tools", "build_exact_gfx.py"), encoding="utf-8").read(), G)
    import gfx_kit as k, gate
    for o in list(bpy.data.objects):
        if o.name in ("Backdrop", "Halo") or o.type == "LIGHT":
            bpy.data.objects.remove(o, do_unlink=True)
    s = bpy.context.scene; a = k.arm(); s.render.resolution_x, s.render.resolution_y = 1080, 1350
    parts = lambda bone: [o for o in a.children_recursive if o.type == "MESH" and o.parent_bone == bone]
    for o in sorted(a.children_recursive, key=lambda o: o.name):
        if o.type == "MESH":
            print("PART", o.name, o.parent_bone, tuple(round(d, 2) for d in o.dimensions), len(o.data.polygons),
                  o.data.materials[0].name if o.data.materials else "-")

    def setrot(bone, ypr):
        pb = a.pose.bones[bone]; pb.rotation_mode = "QUATERNION"
        y, p, r = (math.radians(v) for v in ypr)
        R = Matrix.Rotation(y, 3, "Z") @ Matrix.Rotation(p, 3, "X") @ Matrix.Rotation(r, 3, "Y")
        B = pb.bone.matrix_local.to_3x3()
        pb.rotation_quaternion = (B.inverted() @ R @ B).to_quaternion()

    # ---- pose: plank lean, chest and head to the lens
    print("ARM rot before", tuple(round(math.degrees(v), 1) for v in a.rotation_euler), "head", tuple(round(v, 2) for v in k.head_center()))
    a.rotation_euler.x += math.radians(LEAN)
    setrot("UpperTorso", (6, 0, 0)); setrot("Head", (8, -8 - LEAN, 7))
    k.upd()
    a.location.z -= min(v.z for o in a.children_recursive if o.type == "MESH" and o.parent_bone.startswith("Foot") for v in wv(o))
    k.upd()
    H = k.head_center(); head = k.head_obj()
    wy = min(v.y for o in [head] + parts("UpperTorso") for v in wv(o)) - 0.005
    print("HEAD", tuple(round(v, 2) for v in H), "WALL_Y", round(wy, 3))

    # ---- camera
    if not s.camera:
        c = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); s.collection.objects.link(c); s.camera = c
    cam = s.camera
    view = (-math.sin(math.radians(AZ)), math.cos(math.radians(AZ)), -math.tan(math.radians(EL)))
    print("FRAME", k.frame_head(HEAD_FRAC, head_xy=HEAD_XY, view_dir=view, lens=LENS))
    C = cam.matrix_world.translation.copy()
    assert C.z > 0.2, f"camera {C.z:.2f} m is at or under the floor"
    print("CAM", tuple(round(v, 2) for v in C), "dist", round((C - H).length, 2))

    def ray(fx, fy):
        tr, br, bl, tl = cam.data.view_frame(scene=s)
        p = tl + (tr - tl) * fx + (bl - tl) * fy
        return (cam.matrix_world.to_3x3() @ p).normalized()

    def on_plane(fx, fy, axis, value):
        d = ray(fx, fy); t = (value - C[axis]) / d[axis]
        assert t > 0, f"frame point {fx},{fy} never reaches plane {axis}={value}"
        return C + d * t
    hb = [k.project(v) for v in wv(head)]
    hx0, hx1 = min(p[0] for p in hb), max(p[0] for p in hb); hy0, hy1 = min(p[1] for p in hb), max(p[1] for p in hb)
    hdepth = k.project(H)[2]
    print("HEADBOX", [round(v, 3) for v in (hx0, hy0, hx1, hy1)], "ray check", [round(v, 3) for v in k.project(C + ray(0.3, 0.7) * 2)])

    # ---- sparkle aura: keep it unless it crosses the face
    aura = bpy.data.objects.get("Handle2"); hidden = []
    if aura:
        aw = aura.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world; cross = 0
        mx, my = (hx1 - hx0) * 0.1, (hy1 - hy0) * 0.1
        for p in aura.data.polygons:
            x, y, d = k.project(aw @ p.center)
            cross += hx0 + mx < x < hx1 - mx and hy0 + my < y < hy1 - my and d < hdepth
        print("AURA", aura.name, "faces over the face:", cross, "size", tuple(round(d, 2) for d in aura.dimensions), "faces", len(aura.data.polygons))
        if cross:
            aura.hide_render = True; hidden.append("Handle2")

    # ---- set
    CX = H.x + 0.22; XA = CX + 2.0
    conc = k.pbr("concrete_layers_02", 0.9, tint=(0.22, 0.21, 0.23))
    conc2 = k.pbr("concrete_layers_02", 0.6, tint=(0.17, 0.16, 0.19))
    g = k.plane("Ground", (30, 30), (0, 0, -0.002), k.pbr("asphalt_02", 1.2, tint=(0.3, 0.3, 0.34)))
    gb = g.data.materials[0].node_tree.nodes["Principled BSDF"]
    for l in list(gb.inputs["Roughness"].links):
        g.data.materials[0].node_tree.links.remove(l)
    gb.inputs["Roughness"].default_value = 0.1
    k.cube("Wall", (CX + 4, 8, 10), ((CX - 4) / 2, wy - 4, 5), conc)
    k.cube("WallA", (0.3, 14, 10), (XA + 0.15, wy - 6, 5), conc2)
    k.cube("WallF", (6, 0.3, 10), (CX + 1, wy - 11, 5), conc2)
    metal = k.material("DarkMetal", (0.04, 0.045, 0.05), 0.35, 0.9)
    rust = k.pbr("rust_coarse_01", 1.5, tint=(0.45, 0.36, 0.3))

    def cyl(name, loc, r, depth, mat, rot=(0, 0, 0)):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=20)
        o = bpy.context.active_object; o.name = name; o.data.materials.append(mat)
        bpy.ops.object.shade_smooth(); return o

    def tube(name, pts, mat, r=0.011, cyclic=False):
        cu = bpy.data.curves.new(name + "C", "CURVE"); cu.dimensions = "3D"; sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
        for p, q in zip(sp.points, pts):
            p.co = (*q, 1)
        sp.use_cyclic_u = cyclic; cu.bevel_depth = r; cu.bevel_resolution = 3
        co = bpy.data.objects.new(name + "C", cu); s.collection.objects.link(co); k.upd()
        me = bpy.data.meshes.new_from_object(co.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        bpy.data.objects.remove(co, do_unlink=True)
        o = bpy.data.objects.new(name, me); s.collection.objects.link(o); me.materials.clear(); me.materials.append(mat); return o

    # wordless neon on the close wall, upper right: a ring with a zigzag grin
    P = on_plane(0.815, 0.145, 1, wy + 0.045); R = 0.125
    neon_p = k.material("NeonPurple", (0, 0, 0), 0.4, emit=PURPLE, strength=8)
    neon_k = k.material("NeonPink", (0, 0, 0), 0.4, emit=PINK, strength=8)
    tube("NeonRing", [(P.x + R * math.cos(t), P.y, P.z + R * math.sin(t)) for t in (i * math.tau / 40 for i in range(40))], neon_p, cyclic=True)
    # inner shape: a four-point sparkle like his aura (a zigzag grin read as the letters "WV" in preview 1)
    star = [((0.082 if i % 2 == 0 else 0.024) * math.cos(i * math.tau / 8 + math.pi / 2), (0.082 if i % 2 == 0 else 0.024) * math.sin(i * math.tau / 8 + math.pi / 2)) for i in range(8)]
    tube("NeonStar", [(P.x + u, P.y, P.z + v) for u, v in star], neon_k, r=0.009, cyclic=True)
    k.cube("NeonPlate", (2 * R + 0.1, 0.02, 2 * R + 0.1), (P.x, wy + 0.011, P.z), k.material("Plate", (0.012, 0.012, 0.016), 0.7, 0.6))
    for dx in (-R - 0.03, R + 0.03):
        cyl("NeonWire", (P.x + dx, wy + 0.02, P.z + 1.2), 0.006, 2.2, metal)
    pr = on_plane(0.965, 0.3, 1, wy + 0.05)
    cyl("PipeR", (pr.x, wy + 0.05, 2.5), 0.045, 5, rust)
    for z in (0.9, 1.5, 2.1, 2.7):
        cyl("PipeRClamp", (pr.x, wy + 0.05, z), 0.056, 0.05, metal)

    # the alley wall seen above his right shoulder (screen left), every piece placed from its frame position
    w = on_plane(0.075, 0.095, 0, XA)
    k.cube("WinGlow", (0.02, 0.8, 1.1), (XA - 0.01, w.y, w.z), k.material("WinGlow", (0, 0, 0), 0.5, emit=(1.0, 0.55, 0.2), strength=2.5))
    k.cube("WinFrame", (0.06, 0.92, 0.07), (XA - 0.03, w.y, w.z - 0.58), metal)
    for dy in (-0.27, 0.0, 0.27):
        k.cube("WinBar", (0.035, 0.03, 1.1), (XA - 0.04, w.y + dy, w.z), metal)
    lp = on_plane(0.165, 0.27, 0, XA - 0.22)
    k.cube("LampArm", (0.24, 0.03, 0.03), (XA - 0.11, lp.y, lp.z + 0.09), metal)
    cyl("LampShade", (lp.x, lp.y, lp.z + 0.07), 0.11, 0.05, metal)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=lp, segments=16, ring_count=8)
    o = bpy.context.active_object; o.name = "LampBulb"; o.data.materials.append(k.material("LampGlow", (0, 0, 0), 0.5, emit=SODIUM, strength=18))
    ld = bpy.data.lights.new("AlleyLamp", "POINT"); ld.energy = 70; ld.color = SODIUM; ld.shadow_soft_size = 0.05
    lo = bpy.data.objects.new("AlleyLamp", ld); s.collection.objects.link(lo); lo.location = lp + Vector((0, 0, -0.08))
    t = on_plane(0.225, 0.115, 0, XA - 0.04); q = 0.3
    tube("NeonTri", [(t.x, t.y - q, t.z - q * 0.58), (t.x, t.y + q, t.z - q * 0.58), (t.x, t.y, t.z + q * 1.15)], neon_k, r=0.014, cyclic=True)
    for i, fx in enumerate((0.022, 0.125)):
        pp = on_plane(fx, 0.3, 0, XA - 0.07)
        cyl(f"PipeA{i}", (pp.x, pp.y, 5), 0.06 - 0.015 * i, 10, rust)
        for z in (1.8, 2.7, 3.6, 4.5):
            cyl(f"PipeA{i}Clamp", (pp.x, pp.y, z), 0.075 - 0.015 * i, 0.06, metal)
    ac = on_plane(0.06, 0.4, 0, XA - 0.2)
    k.cube("ACBox", (0.4, 0.75, 0.5), ac, k.pbr("green_metal_rust", 1.5, tint=(0.3, 0.33, 0.33)))
    for i, (y, z0, z1) in enumerate(((wy - 3.3, 3.6, 4.0), (wy - 4.4, 3.1, 3.3), (wy - 5.4, 4.3, 3.9))):
        pts = [(CX + (XA - CX) * u, y - 0.4 * u, z0 + (z1 - z0) * u - 0.35 * math.sin(math.pi * u)) for u in (j / 16 for j in range(17))]
        tube(f"Cable{i}", pts, metal, r=0.012)
    k.cube("Dumpster", (1.3, 0.8, 1.0), (CX + 1.3, wy - 2.2, 0.5), k.pbr("green_metal_rust", 1.5, tint=(0.35, 0.45, 0.4)))
    k.cube("DumpLid", (1.36, 0.86, 0.05), (CX + 1.3, wy - 2.2, 1.03), metal)

    # ---- arms: forearms behind the hips, pick the pose that shows the fewest hand vertices
    def hands_showing():
        k.upd(); dg = bpy.context.evaluated_depsgraph_get(); n = 0
        for side in "PN":
            for o in parts("Hand." + side):
                vs = wv(o)
                for p in vs[::max(1, len(vs) // 80)]:
                    x, y, d = k.project(p)
                    if not (0 < x < 1 and 0 < y < 1):
                        continue
                    v = p - C; hit, loc, *_ = s.ray_cast(dg, C, v.normalized(), distance=v.length - 0.004)
                    n += not hit
        return n
    best = None
    for up in (-8, -14):
        for lp_ in (-10, -20):
            for roll in (35, 50, 65):
                for sd, sg in (("P", 1), ("N", -1)):
                    setrot("UpperArm." + sd, (0, up, 0)); setrot("LowerArm." + sd, (0, lp_, sg * roll)); setrot("Hand." + sd, (0, 0, 0))
                n = hands_showing()
                if best is None or n < best[0]:
                    best = (n, up, lp_, roll)
    n, up, lp_, roll = best
    for sd, sg in (("P", 1), ("N", -1)):
        setrot("UpperArm." + sd, (0, up, 0)); setrot("LowerArm." + sd, (0, lp_, sg * roll))
    k.upd(); print("ARMS upper pitch", up, "forearm pitch", lp_, "roll", roll, "hand vertices showing", n)

    # ---- rain: one mesh, none within 1.3 m of the lens, none over the face
    rnd = random.Random(7); bm = bmesh.new(); made = 0
    for _ in range(3200):
        p = Vector((rnd.uniform(-1.6, XA), rnd.uniform(wy - 9, C.y), rnd.uniform(0.3, 7.0)))
        dist = (p - C).length
        if dist < 1.3 or (p.x < CX + 0.03 and p.y < wy + 0.03):
            continue
        x, y, d = k.project(p)
        if hx0 - 0.03 < x < hx1 + 0.03 and hy0 - 0.03 < y < hy1 + 0.05 and d < hdepth + 0.3:
            continue
        L = rnd.uniform(0.12, 0.25); wd = 0.0011 * max(1.0, dist / 2.2); dv = Vector((0.03, 0.0, -L))
        side = Vector((ray(0.5, 0.5).y, -ray(0.5, 0.5).x, 0)).normalized() * wd
        bm.faces.new([bm.verts.new(p - side), bm.verts.new(p + side), bm.verts.new(p + dv + side), bm.verts.new(p + dv - side)]); made += 1
    me = bpy.data.meshes.new("Rain"); bm.to_mesh(me); bm.free()
    ro = bpy.data.objects.new("Rain", me); s.collection.objects.link(ro)
    me.materials.append(k.material("RainMat", (0.8, 0.85, 1.0), 0.1, emit=(0.6, 0.7, 1.0), strength=0.25, alpha=0.25))
    ro.visible_shadow = False
    print("RAIN streaks", made)

    # ---- light: one warm key, purple rim, weak fill; the alley has its own lamp and a purple back light
    k.area("Key", H + Vector((1.5, 1.3, 1.5)), H, 130, 0.4, SODIUM, 80)
    # preview 1 was purple everywhere: the rim is now a narrow beam from high on the wall side, the alley is lit warm
    # preview 2: the rim turned the black hair grey and the face sat at luma 149: rim 120 -> 60, key 130 -> 95,
    # hair textures multiplied down (Handle4/Handle5 are the hair pieces on the Head)
    bpy.data.objects["Key"].data.energy = 95
    for mn in ("Handle4Mtl", "Handle5Mtl"):
        m = bpy.data.materials.get(mn); b = m and m.node_tree.nodes.get("Principled BSDF")
        if b and b.inputs["Base Color"].links:
            src = b.inputs["Base Color"].links[0].from_socket; mix = m.node_tree.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 1
            mix.inputs[7].default_value = (0.45, 0.45, 0.45, 1)
            m.node_tree.links.new(src, mix.inputs[6]); m.node_tree.links.new(mix.outputs[2], b.inputs["Base Color"])
            b.inputs["Specular IOR Level"].default_value = 0.25
    k.area("Rim", H + Vector((-0.95, 0.02, 0.85)), H + Vector((0, 0, 0.05)), 60, 0.3, PURPLE, 50)
    k.area("NeonSpill", P + Vector((0, 0.3, 0)), P + Vector((0.2, -0.05, -0.45)), 9, 0.3, PURPLE)
    k.area("Fill", H + Vector((-0.3, 1.6, -0.9)), H, 4, 2.0, (0.25, 0.6, 0.8))
    k.area("AlleyBack", Vector((CX + 1.0, wy - 8.5, 6.0)), Vector((CX + 1.6, wy - 3.5, 2.5)), 180, 1.5, PURPLE)
    ld.energy = 170
    k.world((0.004, 0.005, 0.012), 1.0)
    k.setup_cycles(256, "AgX - Punchy", 0.0, dof_fstop=2.8)
    for nm in ("Dumpster", "Ground", "NeonRing", "LampBulb", "WinGlow", "NeonTri", "PipeR", "ACBox"):
        ob = bpy.data.objects[nm]; vs = wv(ob); b = [k.project(v) for v in vs[::max(1, len(vs) // 400)]]
        inside = sum(1 for x, y, d in b if d > 0 and 0 < x < 1 and 0 < y < 1)
        print("INFRAME", nm, f"{inside}/{len(b)}", "centre", [round(v, 2) for v in k.project(sum(vs, Vector()) / len(vs))])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "scene.blend"))

    keep = {a} | set(a.children_recursive)
    job = {"name": "alley_v2", "avatar_dir": AVATAR.replace("\\", "/"), "avatar_fresh_days": 1, "engine": "CYCLES",
           "allow_names": [o.name for o in s.objects if o not in keep], "support": "ground", "ground_tol": 0.02,
           "planned_hidden": hidden, "see_through": ["Rain"], "face": {"min_visible": 0.7, "max_turn": 30},
           "head_frac": round(HEAD_FRAC * 0.8, 3), "head_xy": list(HEAD_XY), "tol": 0.05,
           "props": [{"name": "NeonRing", "cell": [0.62, 0.0, 1.0, 0.3], "may_cross_head": False},
                     {"name": "LampBulb", "cell": [0.0, 0.1, 0.3, 0.4], "may_cross_head": False}],
           "out_of_frame": ["Foot.P", "Foot.N"],
           "camera": {"elevation": [-23, -13], "azimuth": [-19, -9], "roll": [-2, 2], "lens": [39, 41], "distance": [0.8, 2.5]},
           "light": {"luma": [18, 90], "face_luma": [55, 215], "samples": 24,
                     "emit_caps": {"Neon": 12, "Lamp": 25, "Win": 4, "Rain": 1, "default": 5}},
           "final": {"raw": os.path.join(OUTDIR, "alley_v2_raw.png"), "graded": os.path.join(OUTDIR, "alley_v2_final.png"),
                     "mask": os.path.join(OUT, "passes", "mask.png"), "black_point": [0, 18], "white_min": 170,
                     "saturation": [0.15, 0.8], "max_delta_e": 14}}
    jp = os.path.join(OUT, "job.json"); json.dump(job, open(jp, "w"), indent=1)
    print("GATE", gate.run(jp, ["scene", "body", "face", "frame", "camera", "light"]))


def render(pct, samples, name):
    import gfx_kit as k
    k.setup_cycles(samples, "AgX - Punchy", bpy.context.scene.view_settings.exposure, dof_fstop=2.8)
    k.render(os.path.join(OUTDIR, name + ".png"), pct, samples); print("RENDERED", name)


def passes():
    """Material-override passes, no compositor: mask, hair, emission-only, depth, camera-space normal."""
    import gfx_kit as k
    s = bpy.context.scene; P = os.path.join(OUT, "passes"); os.makedirs(P, exist_ok=True)
    k.setup_cycles(256, "AgX - Punchy", s.view_settings.exposure, dof_fstop=2.8)
    a = k.arm(); head = k.head_obj(); rain = bpy.data.objects.get("Rain")
    k.render_mask(os.path.join(P, "mask.png"))
    body = [o for o in a.children_recursive if o.type == "MESH" and not o.hide_render and (o.parent_bone != "Head" or o == head)]
    for o in body:
        o.is_holdout = True
    k.render_mask(os.path.join(P, "hair.png"))
    for o in body:
        o.is_holdout = False
    if rain:
        rain.hide_render = True
    # emission only: lights off, black world, no bounces
    lights = [o for o in s.objects if o.type == "LIGHT"]; bg = s.world.node_tree.nodes["Background"].inputs["Strength"]
    old = (bg.default_value, s.cycles.max_bounces)
    for l in lights:
        l.hide_render = True
    bg.default_value = 0.0; s.cycles.max_bounces = 0
    k.render(os.path.join(P, "emission.png"), 100, 48)
    for l in lights:
        l.hide_render = False
    bg.default_value, s.cycles.max_bounces = old

    def override(name, wire):
        m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(em.outputs[0], out.inputs["Surface"]); wire(nt, em); return m

    def depth(nt, em):
        cd = nt.nodes.new("ShaderNodeCameraData"); dv = nt.nodes.new("ShaderNodeMath"); dv.operation = "DIVIDE"
        dv.inputs[1].default_value = DMAX; nt.links.new(cd.outputs["View Distance"], dv.inputs[0]); nt.links.new(dv.outputs[0], em.inputs["Color"])

    def normal(nt, em):
        ge = nt.nodes.new("ShaderNodeNewGeometry"); vt = nt.nodes.new("ShaderNodeVectorTransform")
        vt.vector_type = "NORMAL"; vt.convert_from = "WORLD"; vt.convert_to = "CAMERA"
        ma = nt.nodes.new("ShaderNodeVectorMath"); ma.operation = "MULTIPLY_ADD"
        ma.inputs[1].default_value = (0.5, 0.5, 0.5); ma.inputs[2].default_value = (0.5, 0.5, 0.5)
        nt.links.new(ge.outputs["Normal"], vt.inputs[0]); nt.links.new(vt.outputs[0], ma.inputs[0]); nt.links.new(ma.outputs[0], em.inputs["Color"])
    vl = bpy.context.view_layer; vs = s.view_settings; im = s.render.image_settings
    old = (vs.view_transform, vs.look, vs.exposure, s.cycles.use_denoising, im.color_depth, im.color_mode)
    vs.view_transform = "Raw"; vs.look = "None"; vs.exposure = 0.0; s.cycles.use_denoising = False; s.cycles.max_bounces = 0
    im.color_depth = "16"; im.color_mode = "BW"
    vl.material_override = override("PassDepth", depth); k.render(os.path.join(P, "depth.png"), 100, 24)
    im.color_mode = "RGB"
    vl.material_override = override("PassNormal", normal); k.render(os.path.join(P, "normal.png"), 100, 24)
    vl.material_override = None
    vs.view_transform, vs.look, vs.exposure, s.cycles.use_denoising, im.color_depth, im.color_mode = old
    if rain:
        rain.hide_render = False
    hb = [k.project(v) for v in wv(head)]
    meta = {"dmax": DMAX, "head_box": [min(p[0] for p in hb), min(p[1] for p in hb), max(p[0] for p in hb), max(p[1] for p in hb)],
            "normal_space": "camera: x right, y up, z to the lens; stored as n*0.5+0.5", "depth": "view distance / dmax, 0 = nothing hit"}
    json.dump(meta, open(os.path.join(P, "meta.json"), "w"), indent=1); print("PASSES", os.listdir(P))


if MODE == "build":
    build()
elif MODE == "render":
    render(int(argv[1]), int(argv[2]), argv[3])
elif MODE == "passes":
    passes()
elif MODE == "gate":
    import gate
    print("GATE", gate.run(os.path.join(OUT, "job.json"), argv[1].split(",")))
