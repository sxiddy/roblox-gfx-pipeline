"""Garage selfie, round 5: implements the Opus review of v4 (37 numbered items, referenced as #n below).
Exec in Blender and call, in order: stage_set(), stage_camera(), stage_layout(), stage_light(), stage_final(out_dir).
"""
import importlib
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

TOOLS = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools"
sys.path.insert(0, TOOLS)
import gfx_kit as k  # noqa: E402
importlib.reload(k)
V4 = {"__name__": "v4"}
exec(open(os.path.join(TOOLS, "style_garage_v4.py"), encoding="utf-8").read(), V4)

BACK = Vector((0, -1.6, 0)); WALL_ROT = math.radians(-18); RW = Matrix.Rotation(WALL_ROT, 4, "Z")


# ---------------------------------------------------------------- helpers
def floor_at(fx, fy, z=0.0):
    """World point on the plane z where the camera ray through frame fraction (fx, fy; y down) lands."""
    scene = bpy.context.scene; cam = scene.camera
    tr, br, bl, tl = cam.data.view_frame(scene=scene)
    p = cam.matrix_world @ (tl + (tr - tl) * fx + (bl - tl) * fy)
    d = p - cam.matrix_world.translation
    t = (z - cam.matrix_world.translation.z) / d.z
    return cam.matrix_world.translation + d * t


def ray_at(fx, fy, dist):
    scene = bpy.context.scene; cam = scene.camera
    tr, br, bl, tl = cam.data.view_frame(scene=scene)
    p = cam.matrix_world @ (tl + (tr - tl) * fx + (bl - tl) * fy)
    o = cam.matrix_world.translation
    return o + (p - o).normalized() * dist


def screen_angle(p1, p2):
    """Degrees a world segment makes on screen; positive = drops to the right."""
    rx, ry = bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y
    a, b = k.project(p1), k.project(p2)
    if b[0] < a[0]:
        a, b = b, a
    return math.degrees(math.atan2((b[1] - a[1]) * ry, (b[0] - a[0]) * rx))


def cyl_between(name, a, b, r, mat):
    a, b = Vector(a), Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(a + b) / 2, vertices=12)
    o = bpy.context.active_object; o.name = name
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); o.data.materials.append(mat); return o


def nodes_of(mat, idname):
    return [n for n in mat.node_tree.nodes if n.bl_idname == idname]


def floor_mat():
    return bpy.data.objects["Floor"].data.materials[0]


# ---------------------------------------------------------------- set (#10 #11 #13 #15 #17 #18 #19)
def stage_set():
    V4["stage_set"]()
    k.label("v5 1/5 set: fence, posts, wall, floor detail")
    m = floor_mat(); nt = m.node_tree; N = nt.nodes.new; L = nt.links.new
    for mp in nodes_of(m, "ShaderNodeMapping"):  # #19 texture repeats 0.6 -> 2 per metre
        if any(l.to_node.bl_idname == "ShaderNodeTexImage" for l in mp.outputs[0].links):
            mp.inputs["Scale"].default_value = (2, 2, 2)
    for nm in nodes_of(m, "ShaderNodeNormalMap"):
        nm.inputs["Strength"].default_value = 1.2
    for th in nodes_of(m, "ShaderNodeMath"):  # #16 line width 0.16 -> 0.12
        if th.operation == "LESS_THAN" and abs(th.inputs[1].default_value - 0.08) < 1e-4:
            th.inputs[1].default_value = 0.06
    for mr in nodes_of(m, "ShaderNodeMapRange"):  # #17 more worn gaps
        mr.inputs["From Min"].default_value = 0.42
    mixc = next(n for n in nodes_of(m, "ShaderNodeMix") if n.blend_type == "MIX" and n.data_type == "RGBA"
                and n.inputs[7].default_value[1] < 0.6 and n.inputs[7].default_value[0] > 0.5)
    mixc.inputs[7].default_value = (0.80, 0.45, 0.015, 1)  # #17 deeper yellow
    b = nt.nodes["Principled BSDF"]
    lines_map = next(n for n in nodes_of(m, "ShaderNodeMapping") if abs(n.inputs["Rotation"].default_value[2] - math.radians(32)) < 1e-3)
    lines_map.name = "LinesMap"
    # #18 saw-cut joints every 1.2 m along the bays
    sx = N("ShaderNodeSeparateXYZ"); L(lines_map.outputs[0], sx.inputs[0]); js = []
    for ax in ("X", "Y"):
        pp = N("ShaderNodeMath"); pp.operation = "PINGPONG"; pp.inputs[1].default_value = 0.6
        lt = N("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.004
        L(sx.outputs[ax], pp.inputs[0]); L(pp.outputs[0], lt.inputs[0]); js.append(lt)
    joint = N("ShaderNodeMath"); joint.operation = "MAXIMUM"; L(js[0].outputs[0], joint.inputs[0]); L(js[1].outputs[0], joint.inputs[1])
    tc = N("ShaderNodeTexCoord")
    # #19 clustered oil speckles
    vor = N("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 60; vor.inputs["Randomness"].default_value = 1
    L(tc.outputs["Object"], vor.inputs["Vector"])
    sp = N("ShaderNodeMath"); sp.operation = "LESS_THAN"; sp.inputs[1].default_value = 0.06; L(vor.outputs["Distance"], sp.inputs[0])
    cl = N("ShaderNodeTexNoise"); cl.inputs["Scale"].default_value = 3; L(tc.outputs["Object"], cl.inputs["Vector"])
    clm = N("ShaderNodeMath"); clm.operation = "GREATER_THAN"; clm.inputs[1].default_value = 0.45; L(cl.outputs["Fac"], clm.inputs[0])
    spk = N("ShaderNodeMath"); spk.operation = "MULTIPLY"; L(sp.outputs[0], spk.inputs[0]); L(clm.outputs[0], spk.inputs[1])
    # #18 hairline cracks: thin band of a distorted noise, masked
    cn = N("ShaderNodeTexNoise"); cn.inputs["Scale"].default_value = 2; cn.inputs["Distortion"].default_value = 4
    L(tc.outputs["Object"], cn.inputs["Vector"])
    cs = N("ShaderNodeMath"); cs.operation = "SUBTRACT"; cs.inputs[1].default_value = 0.5; L(cn.outputs["Fac"], cs.inputs[0])
    ca = N("ShaderNodeMath"); ca.operation = "ABSOLUTE"; L(cs.outputs[0], ca.inputs[0])
    cb = N("ShaderNodeMath"); cb.operation = "LESS_THAN"; cb.inputs[1].default_value = 0.005; L(ca.outputs[0], cb.inputs[0])
    cmn = N("ShaderNodeTexNoise"); cmn.inputs["Scale"].default_value = 1.5; L(tc.outputs["Object"], cmn.inputs["Vector"])
    cmk = N("ShaderNodeMath"); cmk.operation = "GREATER_THAN"; cmk.inputs[1].default_value = 0.6; L(cmn.outputs["Fac"], cmk.inputs[0])
    crack = N("ShaderNodeMath"); crack.operation = "MULTIPLY"; L(cb.outputs[0], crack.inputs[0]); L(cmk.outputs[0], crack.inputs[1])
    # darkening factor = (1-.55 joint)(1-.65 speckle)(1-.7 crack), applied after the paint so it marks the lines too
    def one_minus(src, amt):
        mm = N("ShaderNodeMath"); mm.operation = "MULTIPLY_ADD"; mm.inputs[1].default_value = -amt; mm.inputs[2].default_value = 1
        L(src.outputs[0], mm.inputs[0]); return mm
    f1, f2, f3 = one_minus(joint, 0.55), one_minus(spk, 0.65), one_minus(crack, 0.7)
    m12 = N("ShaderNodeMath"); m12.operation = "MULTIPLY"; L(f1.outputs[0], m12.inputs[0]); L(f2.outputs[0], m12.inputs[1])
    fac = N("ShaderNodeMath"); fac.operation = "MULTIPLY"; L(m12.outputs[0], fac.inputs[0]); L(f3.outputs[0], fac.inputs[1])
    dirt = N("ShaderNodeMix"); dirt.data_type = "RGBA"; dirt.blend_type = "MULTIPLY"; dirt.inputs["Factor"].default_value = 1
    L(mixc.outputs[2], dirt.inputs[6]); L(fac.outputs[0], dirt.inputs[7]); L(dirt.outputs[2], b.inputs["Base Color"])
    bump = N("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.4; bump.invert = True
    hsum = N("ShaderNodeMath"); hsum.operation = "ADD"; L(joint.outputs[0], hsum.inputs[0]); L(crack.outputs[0], hsum.inputs[1])
    L(hsum.outputs[0], bump.inputs["Height"])
    nm = nodes_of(m, "ShaderNodeNormalMap")[0]; L(nm.outputs["Normal"], bump.inputs["Normal"]); L(bump.outputs["Normal"], b.inputs["Normal"])

    # #10 chain-link: bigger, dull diamonds
    fm = bpy.data.objects["Fence"].data.materials[0]
    for n in nodes_of(fm, "ShaderNodeMath"):
        if n.operation == "PINGPONG":
            n.inputs[1].default_value = 0.06
        if n.operation == "LESS_THAN":
            n.inputs[1].default_value = 0.006
    fb = fm.node_tree.nodes["Principled BSDF"]
    fb.inputs["Metallic"].default_value = 0.6; fb.inputs["Roughness"].default_value = 0.65
    fb.inputs["Base Color"].default_value = (0.32, 0.32, 0.3, 1)
    bpy.context.scene.cycles.filter_width = 1.5

    # #11 posts every 1.6 m, thinner, with diagonal brace wires
    k.clear({"Post", "Brace"})
    steel = k.material("Steel", (0.5, 0.5, 0.52), 0.45, 1)
    tops = []
    for i in range(-6, 7):
        p = BACK + RW @ Vector((i * 1.6, 0, 0))
        cyl_between("Post", p + Vector((0, 0, 1.0)), p + Vector((0, 0, 4.2)), 0.03, steel); tops.append(p)
    for a, b2 in zip(tops, tops[1:]):
        cyl_between("Brace", a + Vector((0, 0.01, 4.1)), b2 + Vector((0, 0.01, 1.15)), 0.006, steel)

    # #13 wall: real-scale concrete with vertical water streaks, plus a lighter coping ledge
    wall = bpy.data.objects["Wall"]
    bpy.ops.object.select_all(action="DESELECT"); wall.select_set(True); bpy.context.view_layer.objects.active = wall
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    wall.data.materials.clear(); wm = k.pbr("concrete_floor_02", 1.2, tint=(0.62, 0.62, 0.6)); wall.data.materials.append(wm)
    wnt = wm.node_tree; wb = wnt.nodes["Principled BSDF"]; src = wb.inputs["Base Color"].links[0].from_socket
    sn = wnt.nodes.new("ShaderNodeTexNoise"); sn.inputs["Scale"].default_value = 4
    smp = wnt.nodes.new("ShaderNodeMapping"); smp.inputs["Scale"].default_value = (8, 8, 0.5)
    stc = wnt.nodes.new("ShaderNodeTexCoord"); wnt.links.new(stc.outputs["Object"], smp.inputs["Vector"]); wnt.links.new(smp.outputs[0], sn.inputs["Vector"])
    sr = wnt.nodes.new("ShaderNodeValToRGB"); sr.color_ramp.elements[0].position = 0.35
    sr.color_ramp.elements[0].color = (0.9, 0.9, 0.9, 1); wnt.links.new(sn.outputs["Fac"], sr.inputs["Fac"])
    smx = wnt.nodes.new("ShaderNodeMix"); smx.data_type = "RGBA"; smx.blend_type = "MULTIPLY"; smx.inputs["Factor"].default_value = 0.25
    wnt.links.new(src, smx.inputs[6]); wnt.links.new(sr.outputs["Color"], smx.inputs[7]); wnt.links.new(smx.outputs[2], wb.inputs["Base Color"])
    k.clear({"Coping"})
    k.cube("Coping", (12, 0.36, 0.06), BACK + Vector((0, 0, 1.13)), k.material("CopingConcrete", (0.62, 0.57, 0.5), 0.85), math.degrees(WALL_ROT))
    k.clean_stray()
    k.show_camera()


# ---------------------------------------------------------------- pose + camera (#1-#6 #12 #35 #36)
def _head_aim(ht):
    H = k.head_center(); cam_dir = (bpy.context.scene.camera.location - H).normalized()
    z = Vector((0, 0, 1))
    up = (z - cam_dir * (0.7 * cam_dir.z) + Vector((ht, 0, 0))).normalized()  # tip back ~70% of the way to face the high lens
    k.aim("Head", up, cam_dir)


def _axis_angle():
    a = k.arm(); pb = a.pose.bones
    return screen_angle(a.matrix_world @ pb["Head"].head, a.matrix_world @ pb["Head"].tail) * 0 + _up_angle()


def _up_angle():
    a = k.arm(); pb = a.pose.bones; rx, ry = bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y
    c, t = k.project(a.matrix_world @ pb["Head"].head), k.project(a.matrix_world @ pb["Head"].tail)
    return math.degrees(math.atan2((t[0] - c[0]) * rx, -(t[1] - c[1]) * ry))


def _rail_angle():
    return screen_angle(BACK + RW @ Vector((-2, 0, 1.16)), BACK + RW @ Vector((2, 0, 1.16)))


def stage_camera(head_frac=0.9, head_xy=(0.5, 0.42), torso_xy=(0.35, 0.80), lens=16, rail_deg=23, head_deg=18):
    k.label("v5 2/5 pose + camera: high front camera (el 40-60), crown to lens, rail roll 23 deg")
    k.apply_pose("idle")
    k.aim("LowerTorso", (0.04, 0.14, 1), (0.2, 1, 0)); k.aim("UpperTorso", (0.1, 0.35, 0.93), (0.25, 1, 0))  # #4
    k.aim("UpperLeg.P", (0.05, 0.15, -1)); k.aim("UpperLeg.N", (-0.05, 0.15, -1))
    k.aim("UpperArm.N", (-0.25, 0.25, -0.93)); k.aim("LowerArm.N", (-0.05, 0.45, -0.89)); k.aim("Hand.N", (-0.05, 0.45, -0.89), (0, 0, 1))  # #6
    a = k.arm(); pb = a.pose.bones; W = a.matrix_world
    torso = lambda: W @ ((pb["UpperTorso"].head + pb["UpperTorso"].tail) / 2)
    cam = bpy.context.scene.camera
    best = None
    for az in range(-10, 31, 10):  # #1 hard limits: in front, high
        for el in (40, 45, 50, 55, 60):
            d = (math.sin(math.radians(az)) * math.cos(math.radians(el)), math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el)))
            k.frame_head(head_frac, head_xy, d, lens, 0, iters=3); _head_aim(0.0)
            r = k.frame_head(head_frac, head_xy, d, lens, 0, iters=3)
            t = k.project(torso())
            sc = 4 * (abs(t[0] - torso_xy[0]) + abs(t[1] - torso_xy[1])) + 2 * abs(r["head_frac"] - head_frac)
            if best is None or sc < best[0]:
                best = (sc, az, el, d)
    _, az, el, d = best
    # #12 roll so the wall/rail line drops right by rail_deg
    k.frame_head(head_frac, head_xy, d, lens, 0); _head_aim(0.0)
    rolls = []
    for rl in range(-60, 61, 2):
        k.frame_head(head_frac, head_xy, d, lens, rl, iters=2); rolls.append((abs(_rail_angle() - rail_deg), rl))
    roll = min(rolls)[1]
    # #35 head roll to the measured screen angle
    hts = []
    for ht in [x / 20 for x in range(-6, 7)]:  # small sideways roll only; a big one turns the face away
        _head_aim(ht); hts.append((abs(_up_angle() - head_deg), ht))
    ht = min(hts)[1]; _head_aim(ht)
    r = k.frame_head(head_frac, head_xy, d, lens, roll)
    # #5 near arm: from the shoulder down-left out of the frame, elbow near the bottom-left corner
    sh = W @ pb["UpperArm.P"].head; arm_best = None
    for aa in range(-30, 91, 10):
        for ae in range(-70, 31, 10):
            v = Vector((math.sin(math.radians(aa)) * math.cos(math.radians(ae)), math.cos(math.radians(aa)) * math.cos(math.radians(ae)), math.sin(math.radians(ae))))
            for bn in ("UpperArm.P", "LowerArm.P", "Hand.P"):
                k.aim(bn, v, (0, 0, 1))
            hp, tp, ep = (k.project(W @ x) for x in (pb["Hand.P"].head, pb["Hand.P"].tail, pb["LowerArm.P"].head))
            out = lambda p: p[2] <= 0 or p[0] < 0 or p[1] > 1
            if not (out(hp) and out(tp)):
                continue
            sc = abs(ep[0] - 0.03) + abs(ep[1] - 0.85) if ep[2] > 0 else 1.0
            if arm_best is None or sc < arm_best[0]:
                arm_best = (sc, v)
    if arm_best:
        for bn in ("UpperArm.P", "LowerArm.P", "Hand.P"):
            k.aim(bn, arm_best[1], (0, 0, 1))
    r = k.frame_head(head_frac, head_xy, d, lens, roll)
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 5.6; cam.data.dof.focus_distance = r["dist"]  # #33
    k.show_camera()
    el_now = math.degrees(math.asin((cam.location - k.head_center()).normalized().z))
    assert 38 <= el_now <= 62, f"camera elevation {el_now:.0f} outside 40-60"
    return {"az": az, "el": el, "el_now": round(el_now), "roll": roll, "head_roll": ht, "rail": round(_rail_angle()),
            "head_angle": round(_up_angle()), "arm_found": bool(arm_best), "torso": tuple(round(v, 2) for v in k.project(torso())), **r,
            "shoulder": tuple(round(v, 2) for v in k.project(sh)),
            "handN": tuple(round(v, 2) for v in k.project(W @ pb["Hand.N"].tail))}


# ---------------------------------------------------------------- layout from the camera (#7 #14 #15 #16 #25)
def stage_layout():
    k.label("v5 3/5 layout: floor lines, boxes, sky, building placed through the camera")
    m = floor_mat(); nt = m.node_tree; lm = nt.nodes["LinesMap"]
    a1, a2, b1, c = floor_at(0.62, 0.60), floor_at(0.66, 1.0), floor_at(0.88, 0.64), floor_at(0.85, 0.60)
    d1 = (a2 - a1); theta = math.atan2(d1.x, d1.y)
    R = Matrix.Rotation(theta, 3, "Z")
    lx = -(R @ a1).x; ly = -(R @ c).y
    period = min(max(abs((R @ b1).x + lx), 1.5), 4.0)
    lm.inputs["Rotation"].default_value = (0, 0, theta); lm.inputs["Location"].default_value = (lx, ly, 0)
    for n in nodes_of(m, "ShaderNodeMath"):
        if n.operation == "PINGPONG" and abs(n.inputs[1].default_value - 1.3) < 1e-3:
            n.inputs[1].default_value = period / 2
    # #14 #15 boxes on the floor where the reference has them
    k.clear({"Box", "Tape", "BoxLabel", "BoxIcon"})
    card = k.material("CardboardWorn", (0.55, 0.42, 0.27), 0.85); cnt = card.node_tree
    bn = cnt.nodes.new("ShaderNodeTexNoise"); bn.inputs["Scale"].default_value = 18; bmp = cnt.nodes.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = 0.15; cnt.links.new(bn.outputs["Fac"], bmp.inputs["Height"])
    cnt.links.new(bmp.outputs["Normal"], cnt.nodes["Principled BSDF"].inputs["Normal"])
    tape = k.material("PaperTape", (0.15, 0.3, 0.6), 0.6); label = k.material("Label", (0.9, 0.9, 0.88), 0.7)
    ink = k.material("Ink", (0.03, 0.03, 0.03), 0.8)
    camxy = bpy.context.scene.camera.location.copy(); camxy.z = 0
    def box(pos, size, rz):
        o = k.cube("Box", size, pos, card, rz)
        k.cube("Tape", (size[0] * 1.002, 0.05, 0.004), pos + Vector((0, 0, size[2] / 2 + 0.002)), tape, rz)
        face = (camxy - pos); face.z = 0; face.normalize()
        k.plane("BoxLabel", (0.18, 0.07), pos + face * (size[1] / 2 + 0.003) + Vector((0, 0, 0.03)), label,
                (90, 0, math.degrees(math.atan2(-face.x, face.y))))
        k.plane("BoxIcon", (0.05, 0.05), pos + face * (size[1] / 2 + 0.004) + Vector((0.12, 0, -0.08)), ink,
                (90, 0, math.degrees(math.atan2(-face.x, face.y))))
        return o
    p1 = floor_at(0.88, 0.58); p2 = floor_at(0.93, 0.50)
    box(p1 + Vector((0, 0, 0.15)), (0.5, 0.36, 0.30), 25)
    box(p2 + Vector((0, 0, 0.11)), (0.36, 0.28, 0.22), 10)
    box(p2 + Vector((0, 0, 0.32)), (0.30, 0.25, 0.20), 35)
    # #7 #25 warm sky plane far behind the fence, dark building block top-right, tiny green light
    k.clear({"Sky", "Building", "GreenLight"})
    k.plane("Sky", (40, 15), BACK + RW @ Vector((0, -8, 0)) + Vector((0, 0, 6)), k.material("SkyM", (0.85, 0.78, 0.65), emit=(0.85, 0.78, 0.65), strength=2.5),
            (90, 0, math.degrees(WALL_ROT)))
    bpos = ray_at(0.91, 0.2, 9.0)
    k.cube("Building", (4, 4, 14), bpos, k.pbr("concrete_layers_02", 0.4, tint=(0.22, 0.21, 0.2)), math.degrees(WALL_ROT))
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.03, location=ray_at(0.84, 0.08, 7.5))
    g = bpy.context.active_object; g.name = "GreenLight"; g.data.materials.append(k.material("GreenGlow", (0.2, 1, 0.3), emit=(0.2, 1, 0.3), strength=30))
    k.show_camera()
    return {"theta": round(math.degrees(theta)), "period": round(period, 2), "box1": tuple(round(v, 2) for v in p1)}


# ---------------------------------------------------------------- light (#8 #9 #20-#23 #37)
def stage_light(exposure=-0.4):
    k.label("v5 4/5 light: top-behind daylight, haze box + shaft, rim on hair")
    for o in [o for o in bpy.context.scene.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)
    k.clear({"HazeBox"})
    H = k.head_center(); scene = bpy.context.scene
    k.area("Daylight", H + Vector((0.3, -0.9, 3.0)), H, 900, 6.0, (1.0, 0.88, 0.72))
    k.area("Bounce", H + Vector((0, 0.9, -0.9)), H, 10, 3.0, (1.0, 0.8, 0.55))
    fwd = (scene.camera.location - H).normalized(); right = -fwd.cross(Vector((0, 0, 1))).normalized(); up = -right.cross(fwd).normalized()
    if up.z < 0:
        up = -up
    k.area("Rim", H + right * 0.9 + up * 0.8 - fwd * 1.2, H, 150, 0.8, (1.0, 0.92, 0.8))
    shaft_at = BACK + RW @ Vector((0.5, -4, 9))
    k.area("Shaft", shaft_at, shaft_at - Vector((0, 0, 5)), 2000, 1.5, (1.0, 0.92, 0.8), spread=15)
    hb = k.cube("HazeBox", (20, 10, 10), BACK + RW @ Vector((0, -5.5, 0)) + Vector((0, 0, 5)), bpy.data.materials.new("HazeVol"), math.degrees(WALL_ROT))
    hm = hb.data.materials[0]; hm.use_nodes = True; hn = hm.node_tree
    hn.nodes.remove(hn.nodes["Principled BSDF"]); pv = hn.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = 0.04; pv.inputs["Color"].default_value = (1, 0.9, 0.75, 1); pv.inputs["Anisotropy"].default_value = 0.5
    hn.links.new(pv.outputs[0], hn.nodes["Material Output"].inputs["Volume"])
    k.world((0.9, 0.75, 0.55), 1.0, haze=0)
    scene.view_settings.exposure = exposure
    k.show_camera()


def stage_render(path, percent=40, samples=64):
    k.label("v5 rendering preview"); k.render(path, percent, samples); k.label(None)


def stage_final(out_dir, samples=320):
    k.label("v5 5/5 final render (no denoise smearing: accurate prefilter) + mask")
    scene = bpy.context.scene; scene.cycles.denoising_prefilter = "ACCURATE"
    os.makedirs(out_dir, exist_ok=True)
    k.render(os.path.join(out_dir, "v5_raw.png"), 100, samples)
    k.render_mask(os.path.join(out_dir, "v5_mask.png"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "sttvr_l1ght_garage_v5.blend"), copy=True)
    k.label(None)
