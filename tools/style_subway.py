"""Subway Platform GFX (idea 3 of the 50 list) for Suhaa_Official.
POSE PLAN: sits on a low metal bench, feet flat on the floor, thighs on the seat, both hands resting on the seat edge beside her,
torso upright and a little slouched, head tilted ~12 deg toward the camera, flat cool expression.
CAMERA: low 3/4 from front-left, 50mm, head_frac ~0.2, head left-centre, bench and floor visible, yellow safety line behind her.
SET: station platform, yellow edge line, track pit, a train rushing past behind her (long window streaks, motion-blurred in post),
fluorescent tubes overhead. LIGHT: hard cool-green overhead key, warm train-window rim from behind-left, teal grade, grain."""
import sys, importlib, math
sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import bpy
from mathutils import Vector, Matrix
import gfx_kit as k; importlib.reload(k)
ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
OUT = ROOT + r"\gfx_output\Suhaa_Official"
PREFIX = ("Sw",)


def stage_pose():
    k.apply_pose("sit")
    k.aim("LowerTorso", (0, 0.05, 1)); k.aim("UpperTorso", (0.02, 0.1, 1), (0.2, 1, 0))
    k.aim("Head", (0.2, 0.08, 0.98), (0.3, 1, 0.2))
    for sfx, sx in ((".P", 1), (".N", -1)):
        k.aim("UpperLeg" + sfx, (0.1 * sx, 1, 0.0)); k.aim("LowerLeg" + sfx, (0.0, 0.08, -1)); k.aim("Foot" + sfx, (0, 1, -0.2), (0, 0, 1))
        k.aim("UpperArm" + sfx, (0.3 * sx, 0.15, -0.94)); k.aim("LowerArm" + sfx, (0.05 * sx, 0.55, -0.83)); k.aim("Hand" + sfx, (0, 0.8, -0.2), (0, 0, 1))
    k.upd()


def stage_camera(head_frac=0.135, head_xy=(0.6, 0.55), view_dir=(0.2, 1, 0.02), lens=26, roll=1):
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    if not sc.camera:
        cd = bpy.data.cameras.new("Cam"); co = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(co); sc.camera = co
    print(k.frame_head(head_frac, head_xy=head_xy, view_dir=view_dir, lens=lens, roll=roll)); k.show_camera()


def low(parts):
    return min((o.matrix_world @ Vector(c)).z for o in k.arm().children if o.name.split(".")[0] in parts for c in o.bound_box)


def stage_set():
    import bmesh
    for o in [o for o in bpy.data.objects if o.name.startswith(PREFIX)]:
        bpy.data.objects.remove(o, do_unlink=True)
    a = k.arm(); a.location = (0.0, -0.1, 0.0); k.upd()
    a.location.z = -low(("Foot_P", "Foot_N")) + 0.002; k.upd()           # feet on the floor
    seat = low(("LowerTorso", "UpperLeg_P", "UpperLeg_N")) - 0.003          # bench seat top = the lowest thigh point
    print("seat top", round(seat, 3))
    def cube(n, sz, loc, mat, rot=(0, 0, 0)):
        o = k.cube("Sw" + n, sz, loc, mat); o.rotation_euler = tuple(math.radians(r) for r in rot); return o
    metal = k.material("SwMetal", (0.35, 0.37, 0.4), 0.35, 0.9)
    floor = k.material("SwFloor", (0.1, 0.11, 0.12), 0.3)
    k.plane("SwFloor", (40, 7), (0, 1.0, 0), floor)
    cube("Yellow", (40, 0.32, 0.01), (0, -1.9, 0.006), k.material("SwYellow", (0.9, 0.7, 0.05), 0.6))
    cube("Edge", (40, 0.3, 0.02), (0, -2.15, -0.005), k.material("SwEdge", (0.2, 0.2, 0.2), 0.6))
    cube("Pit", (40, 1.4, 0.05), (0, -3.0, -0.6), k.material("SwPit", (0.01, 0.01, 0.012), 0.9))
    # bench under her (seat slats + backrest + legs)
    cube("Seat", (2.0, 0.5, 0.05), (0, -0.28, seat - 0.025), metal)
    cube("Back", (2.0, 0.05, 0.22), (0, -0.55, seat + 0.11), metal)
    for sx in (-0.9, 0.9):
        cube("BenchLeg%d" % sx, (0.06, 0.45, seat), (sx, -0.28, seat / 2), metal)
    # BULLET TRAIN behind (shinkansen-style): long pointed nose to screen-right (-X), white body, blue stripes, window band, doors.
    # axis along X; the camera-facing side is at y = YC + W/2.
    TY = -3.55; W = 3.0; YC = TY - W / 2; ZB, ZT = 0.45, 3.35; ZC = (ZB + ZT) / 2; HH = (ZT - ZB) / 2
    TIP, FULL = -4.4, 0.1          # nose tip x, x where the full cross-section starts
    white = k.material("SwBullet", (0.86, 0.88, 0.92), 0.38, 0.1)
    _nt = white.node_tree; _b = _nt.nodes["Principled BSDF"]
    _g = _nt.nodes.new("ShaderNodeNewGeometry"); _sp = _nt.nodes.new("ShaderNodeSeparateXYZ"); _mr = _nt.nodes.new("ShaderNodeMapRange"); _cr = _nt.nodes.new("ShaderNodeValToRGB")
    _mr.inputs["From Min"].default_value = 0.0; _mr.inputs["From Max"].default_value = 4.0
    _nt.links.new(_g.outputs["Position"], _sp.inputs[0]); _nt.links.new(_sp.outputs["Z"], _mr.inputs["Value"]); _nt.links.new(_mr.outputs["Result"], _cr.inputs[0])
    _cr.color_ramp.interpolation = "CONSTANT"; _e = _cr.color_ramp.elements
    _W, _B = (0.86, 0.88, 0.92, 1), (0.02, 0.2, 0.7, 1)
    _e[0].position = 0.0; _e[0].color = _W; _e[1].position = 0.175; _e[1].color = _B
    for pos, col in ((0.215, _W), (0.37, _B), (0.405, _W), (0.745, _B), (0.775, _W)):
        el = _cr.color_ramp.elements.new(pos); el.color = col
    _nt.links.new(_cr.outputs["Color"], _b.inputs["Base Color"])
    blue = k.material("SwBlue", (0.02, 0.18, 0.62), 0.3, 0.3)
    dark = k.material("SwDark", (0.02, 0.022, 0.028), 0.4)
    def prof(u):                       # width/height scale along the nose, long pointed beak
        return max(u, 1e-3) ** 0.62
    def ring(x, u, n=40, nsup=4.0):
        sc_ = prof(u); zc = ZC - (1 - u) ** 1.6 * 0.55          # nose dips toward the rails at the tip
        pts = []
        for i in range(n):
            t = i / n * 2 * math.pi; c, sn = math.cos(t), math.sin(t)
            yy = YC + (W / 2) * sc_ * math.copysign(abs(c) ** (2 / nsup), c)
            zz = zc + HH * sc_ * math.copysign(abs(sn) ** (2 / nsup), sn)
            pts.append((x, yy, zz))
        return pts
    bm = bmesh.new(); rings = []
    K = 28
    for i in range(K + 1):
        u = i / K; x = TIP + (FULL - TIP) * u
        rings.append([bm.verts.new(p) for p in ring(x, max(u, 0.012))])
    # body continues straight from FULL to +45
    for x in (FULL + 0.01, 45.0):
        rings.append([bm.verts.new(p) for p in ring(x, 1.0)])
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for i in range(len(r0)):
            j = (i + 1) % len(r0); bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("SwBulletMesh"); bm.to_mesh(me); bm.free()
    for pg in me.polygons: pg.use_smooth = True
    bo = bpy.data.objects.new("SwBullet", me); bpy.context.scene.collection.objects.link(bo); me.materials.append(white)
    SY = YC + W / 2 + 0.012
    cube("Skirt", (49, 3.0, 0.5), (21.0, YC, 0.22), dark); cube("SkirtNose", (4.6, 1.6, 0.5), (-2.2, YC, 0.22), dark)
    # windows + doors (emissive meshes), cab side window on the nose
    wins = bmesh.new(); doors = bmesh.new()
    x = FULL + 0.8
    while x < 44:
        if int((x - FULL) / 1.4) % 6 == 5:      # door every 6th slot
            bmesh.ops.create_cube(doors, size=1.0, matrix=Matrix.LocRotScale((x, SY + 0.005, 1.95), None, (1.3, 0.04, 2.2))); x += 1.4
        else:
            bmesh.ops.create_cube(wins, size=1.0, matrix=Matrix.LocRotScale((x, SY + 0.005, 2.35), None, (0.85, 0.04, 0.55))); x += 1.4
    for ux in (0.78,):                          # cab window
        xm = TIP + (FULL - TIP) * ux; ys = YC + (W / 2) * prof(ux) + 0.01
        bmesh.ops.create_cube(doors, size=1.0, matrix=Matrix.LocRotScale((xm, ys, 2.55), None, (0.9, 0.04, 0.55)))
    for bm_, nm, col, st in ((wins, "SwWindows", (1.0, 0.78, 0.45), 3.0), (doors, "SwDoors", (0.3, 0.55, 0.7), 0.35)):
        me2 = bpy.data.meshes.new(nm + "Mesh"); bm_.to_mesh(me2); bm_.free()
        o = bpy.data.objects.new(nm, me2); bpy.context.scene.collection.objects.link(o); me2.materials.append(k.material(nm + "M", (0, 0, 0), 0.4, emit=col, strength=st))
    # ceiling, fluorescent tubes, pillar
    k.plane("SwCeil", (40, 7), (0, 1.0, 3.6), k.material("SwCeilM", (0.05, 0.055, 0.06), 0.9), rot=(180, 0, 0))
    tube = k.material("SwTube", (1, 1, 1), 0.3, emit=(0.8, 1.0, 0.92), strength=14)
    for i in range(-5, 6):
        cube("Tube%d" % i, (1.3, 0.12, 0.05), (i * 2.6, -0.2, 3.5), tube)
    cube("Pillar", (0.5, 0.5, 3.6), (5.0, -1.0, 1.8), k.material("SwPillar", (0.16, 0.17, 0.19), 0.6))
    cube("Sign", (0.38, 0.03, 0.2), (5.0, -0.73, 2.3), k.material("SwSign", (0, 0, 0), 0.5, emit=(0.2, 0.9, 0.7), strength=4))
    k.show_camera()


def stage_light():
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)
    H = k.head_center()
    k.area("Overhead", Vector((0.2, 0.0, 3.3)), H, 260, 1.2, (0.8, 1.0, 0.93), 110)          # hard cool overhead key
    k.area("TrainRim", Vector((-1.4, -3.0, 1.6)), H, 160, 1.5, (1.0, 0.82, 0.5), 110)        # warm rim from the train windows
    k.area("TrainKey", Vector((0.5, -1.2, 3.3)), Vector((-0.5, -4.0, 1.8)), 170, 4.0, (0.85, 0.95, 1.0), 120)
    k.area("CoolFill", H + Vector((1.8, 2.2, 0.0)), H, 16, 2.5, (0.55, 0.8, 0.95), 140)
    k.world((0.02, 0.04, 0.05), 0.2, haze=0.0012)
    k.setup_cycles(64, look="AgX - Punchy", exposure=0.15, dof_fstop=2.8)
    bpy.context.scene.camera.data.dof.focus_distance = (H - bpy.context.scene.camera.location).length
    k.show_camera()
