"""Concert Barricade GFX (Cortis fan, cool not cutesy) for Suhaa_Official (new black/white avatar).
POSE PLAN: front row, leaning on a steel crowd barricade. Torso leans ~10 deg forward over the rail; both upper arms down-forward,
forearms lying on the rail top pointing forward and inward so the block hands meet near the centre; head tilted up ~15 deg toward
the stage (above the lens) and turned a little to camera-left. Legs hidden behind the barricade panel. Headphones stay on her neck.
CAMERA: in the photo pit (stage side, +Y), slightly low, 3/4 from camera-left, 50mm, roll 4, head ~22% of frame width in the upper
third right of centre, rail runs across the lower frame. Bottom edge cuts at her waist / barricade panel.
SET: steel barricade (top rail, mesh panel, feet), dark crowd silhouettes behind with raised phone screens and red lightsticks, truss
of fixtures at the back, haze volume. LIGHT: white beam spots from the back truss as rim + visible beams, deep red wash from behind,
cold white face spot from the stage side. GRADE: crushed blacks, red/white only, light grain, no text."""
import sys, importlib, math, random
sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import bpy, bmesh
from mathutils import Vector, Matrix
import gfx_kit as k; importlib.reload(k)
ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
OUT = ROOT + r"\gfx_output\Suhaa_Official"
PREFIX = ("Bar", "Crowd", "Phone", "Stick", "Truss", "Fix", "Haze", "Floor", "Beam")


def low(parts):
    return min((o.matrix_world @ Vector(c)).z for o in k.arm().children if o.name.split(".")[0] in parts for c in o.bound_box)


def bone_w(name, tail=False):
    a = k.arm(); b = a.pose.bones[name]
    return a.matrix_world @ (b.tail if tail else b.head)


def stage_pose():
    k.reset_pose()
    k.aim("LowerTorso", (0, 0.0, 1)); k.aim("UpperTorso", (0, 0.18, 1), (0, 1, 0))
    k.aim("Head", (0.08, -0.26, 0.96), (0.2, 1, 0.26))
    for sfx, sx in ((".P", 1), (".N", -1)):
        k.aim("UpperArm" + sfx, (0.12 * sx, 0.45, -0.88)); k.aim("LowerArm" + sfx, (-0.45 * sx, 0.89, 0.05))
        k.aim("Hand" + sfx, (-0.45 * sx, 0.89, 0.0), (0, 0, 1))
        k.aim("UpperLeg" + sfx, (0, 0, -1)); k.aim("LowerLeg" + sfx, (0, 0, -1)); k.aim("Foot" + sfx, (0, 1, 0), (0, 0, 1))
    k.upd()
    for s in (".P", ".N"):
        print("elbow", s, [round(v, 3) for v in bone_w("LowerArm" + s)], "wrist", [round(v, 3) for v in bone_w("LowerArm" + s, True)])
    print("head", [round(v, 3) for v in k.head_center()], "feet low", round(low(("Foot_P", "Foot_N")), 3))


def stage_set():
    k.clear(PREFIX)
    a = k.arm(); a.location.z += -low(("Foot_P", "Foot_N")); k.upd()
    el = [bone_w("LowerArm" + s) for s in (".P", ".N")]; wr = [bone_w("LowerArm" + s, True) for s in (".P", ".N")]
    fore_low = min(min(e.z, w.z) for e, w in zip(el, wr)) - 0.045  # forearm thickness ~ 0.09
    rail_y = sum(e.y for e in el) / 2 + 0.06
    steel = k.material("BarSteel", (0.55, 0.56, 0.58), 0.32, 0.9)
    dark = k.material("BarDark", (0.08, 0.08, 0.09), 0.6, 0.6)
    W = 8.0
    k.cube("BarRail", (W, 0.09, 0.05), (0, rail_y, fore_low - 0.025), steel)
    k.cube("BarPanel", (W, 0.03, fore_low - 0.1), (0, rail_y + 0.03, (fore_low - 0.1) / 2 + 0.05), dark)
    for i in range(-4, 5):
        k.cube("BarPost%d" % i, (0.05, 0.06, fore_low), (i * 1.0, rail_y + 0.02, fore_low / 2), steel)
    k.plane("Floor", (60, 60), (0, -10, 0), k.material("FloorM", (0.02, 0.02, 0.022), 0.5))
    print("rail top", round(fore_low, 3), "rail y", round(rail_y, 3))
    # crowd: one mesh of silhouettes (capsule bodies + heads), phones and red lightsticks as two emissive meshes
    rnd = random.Random(7)
    bm, bp, bs = bmesh.new(), bmesh.new(), bmesh.new()
    for i in range(260):
        x = rnd.uniform(-9, 9); y = rnd.uniform(-1.3, -16)
        if abs(x) < 0.7 and y > -2.2:
            continue
        h = rnd.uniform(1.45, 1.85)
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.LocRotScale((x, y, h * 0.42), None, (0.42, 0.25, h * 0.84)))
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.12, matrix=Matrix.Translation((x, y, h * 0.84 + 0.12)))
        r = rnd.random()
        if r < 0.22:  # raised phone
            px, pz = x + rnd.uniform(-0.25, 0.25), h + rnd.uniform(0.15, 0.45)
            bmesh.ops.create_cube(bp, size=1.0, matrix=Matrix.LocRotScale((px, y + 0.05, pz), None, (0.075, 0.01, 0.14)))
        elif r < 0.45:  # red lightstick
            sx, sz = x + rnd.uniform(-0.3, 0.3), h + rnd.uniform(0.1, 0.5)
            bmesh.ops.create_cone(bs, cap_ends=True, segments=8, radius1=0.025, radius2=0.025, depth=0.28,
                                  matrix=Matrix.LocRotScale((sx, y, sz), Matrix.Rotation(rnd.uniform(-0.5, 0.5), 3, "Y").to_quaternion(), (1, 1, 1)))
    for name, b, m in (("Crowd", bm, k.material("CrowdM", (0.012, 0.012, 0.014), 0.8)),
                       ("PhoneAll", bp, k.material("PhoneM", (0, 0, 0), 0.4, emit=(0.85, 0.9, 1.0), strength=6)),
                       ("StickAll", bs, k.material("StickM", (0, 0, 0), 0.4, emit=(1.0, 0.05, 0.04), strength=12))):
        me = bpy.data.meshes.new(name); b.to_mesh(me); b.free()
        o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); me.materials.append(m)
    # back truss with fixtures
    tm = k.material("TrussM", (0.15, 0.15, 0.16), 0.5, 0.8)
    k.cube("TrussBar", (20, 0.3, 0.3), (0, -18, 7.5), tm)
    for i, x in enumerate([-8 + 2 * j for j in range(9)]):
        k.cube("FixBody%d" % i, (0.35, 0.35, 0.4), (x, -17.7, 7.1), k.material("FixM", (0.03, 0.03, 0.03), 0.5))
        k.cube("FixLens%d" % i, (0.26, 0.02, 0.26), (x, -17.5, 7.1), k.material("FixLensM", (0, 0, 0), 0.3, emit=(1, 0.95, 0.9), strength=40))
    # haze: one volume box over the crowd / back of the hall (not around her face)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -10, 5)); hz = bpy.context.active_object; hz.name = "Haze"; hz.scale = (30, 17, 12)
    hm = bpy.data.materials.new("HazeM"); hm.use_nodes = True; nt = hm.node_tree; nt.nodes.clear()
    vs = nt.nodes.new("ShaderNodeVolumePrincipled"); vs.inputs["Density"].default_value = 0.05; vs.inputs["Anisotropy"].default_value = 0.55
    mo = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(vs.outputs[0], mo.inputs["Volume"]); hz.data.materials.append(hm)
    k.show_camera()


def stage_camera(head_frac=0.22, head_xy=(0.58, 0.3), view_dir=(-0.45, 1, -0.12), lens=50, roll=4):
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    if not sc.camera:
        cd = bpy.data.cameras.new("Cam"); co = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(co); sc.camera = co
    print(k.frame_head(head_frac, head_xy=head_xy, view_dir=view_dir, lens=lens, roll=roll)); k.show_camera()
    c = sc.camera; print("cam", [round(v, 2) for v in c.location])


def stage_light(beam=1500, red=900, face=60):
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)
    H = k.head_center()
    def spot(name, loc, target, energy, color, size_deg, blend=0.3, radius=0.05):
        ld = bpy.data.lights.new(name, "SPOT"); ld.energy = energy; ld.color = color; ld.spot_size = math.radians(size_deg)
        ld.spot_blend = blend; ld.shadow_soft_size = radius
        o = bpy.data.objects.new(name, ld); bpy.context.scene.collection.objects.link(o); o.location = loc
        o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o
    # white beams from the back truss, two of them grazing her head as rim
    for i, (x, tx) in enumerate(((-6, -0.4), (-2, 0.2), (2, -0.2), (6, 0.5))):
        spot("BeamW%d" % i, (x, -17.4, 7.1), H + Vector((tx, 0, 0.1)), beam, (1, 0.97, 0.92), 7, 0.15)
    spot("BeamRed", (0, -15, 9), H + Vector((0, -3, -1)), red * 3, (1, 0.04, 0.03), 40, 0.6, 0.5)
    k.area("RedWash", H + Vector((-1.5, -3.0, 1.6)), H, red, 2.5, (1.0, 0.05, 0.04), 120)
    k.area("FaceSpot", H + Vector((-1.3, 3.2, 1.9)), H, face, 0.6, (0.82, 0.9, 1.0), 60)
    k.world((0.003, 0.003, 0.004), 1.0)
    k.setup_cycles(64, look="AgX - High Contrast", exposure=0.0, dof_fstop=2.0)
    sc = bpy.context.scene; sc.camera.data.dof.focus_distance = (H - sc.camera.location).length
    k.show_camera()


def lint():
    a = k.arm(); keep = {a} | set(a.children_recursive)
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and o not in keep and not o.name.startswith(PREFIX):
            print("STRAY", o.name, o.active_material)
    for p in ("BarRail", "FixLens4", "Crowd"):
        if p in bpy.data.objects: print(p, "proj", [round(v, 2) for v in k.project(bpy.data.objects[p].location)])
