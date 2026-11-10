"""Glitch Heart Hacker Room GFX for Suhaa_Official.
POSE PLAN: sits on a hidden chair between a front desk (laptop) and a back shelf (three monitors facing the camera). Torso leans
forward ~20 deg toward the laptop, head tilted ~15 deg and dipped so she peeks over the lid, forearms on the desk, hands on the
laptop edge. CAMERA: slightly low, 50mm, head_frac ~0.28, head centre-right, roll -2. The laptop lid back (with stickers) hides
her chest. LIGHT: pink-white screen glow on her face from the lid, purple + cyan RGB rim from behind, monitors emissive.
GRADE: pink/purple, RGB-split bands, scanlines, vignette, grain."""
import sys, importlib, math
sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import bpy
from mathutils import Vector
import gfx_kit as k; importlib.reload(k)
ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
OUT = ROOT + r"\gfx_output\Suhaa_Official"
PREFIX = ("Hk",)


def stage_pose():
    k.apply_pose("sit")
    k.aim("LowerTorso", (0, 0.08, 1)); k.aim("UpperTorso", (0.02, 0.38, 0.92), (0.2, 1, 0))
    k.aim("Head", (0.22, 0.3, 0.92), (0.3, 1, 0.2))
    for sfx, sx in ((".P", 1), (".N", -1)):
        k.aim("UpperLeg" + sfx, (0.08 * sx, 1, 0.0)); k.aim("LowerLeg" + sfx, (0.0, 0.05, -1)); k.aim("Foot" + sfx, (0, 1, -0.2), (0, 0, 1))
        k.aim("UpperArm" + sfx, (0.22 * sx, 0.5, -0.83)); k.aim("LowerArm" + sfx, (-0.15 * sx, 0.95, -0.1)); k.aim("Hand" + sfx, (-0.1 * sx, 0.95, -0.1), (0, 0, 1))
    k.upd()


def stage_camera(head_frac=0.2, head_xy=(0.36, 0.34), view_dir=(0.2, 1, -0.02), lens=50, roll=-2):
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    if not sc.camera:
        cd = bpy.data.cameras.new("Cam"); co = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(co); sc.camera = co
    print(k.frame_head(head_frac, head_xy=head_xy, view_dir=view_dir, lens=lens, roll=roll)); k.show_camera()


def low(parts):
    return min((o.matrix_world @ Vector(c)).z for o in k.arm().children if o.name.split(".")[0] in parts for c in o.bound_box)


def _img_mat(name, path, strength=3.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(t.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = strength
    b.inputs["Base Color"].default_value = (0, 0, 0, 1); b.inputs["Roughness"].default_value = 0.4
    return m


def stage_set():
    for o in [o for o in bpy.data.objects if o.name.startswith(PREFIX)]:
        bpy.data.objects.remove(o, do_unlink=True)
    a = k.arm(); k.upd(); a.location.z = 0; a.location.y = -0.05; k.upd()
    a.location.z += 0.62 - low(("LowerTorso", "UpperLeg_P", "UpperLeg_N")) + 0.003; k.upd()

    def cube(n, sz, loc, mat, rot=(0, 0, 0)):
        o = k.cube("Hk" + n, sz, loc, mat); o.rotation_euler = tuple(math.radians(r) for r in rot); return o
    black = k.material("HkBlack", (0.025, 0.02, 0.035), 0.5)
    desk = k.material("HkDesk", (0.05, 0.04, 0.07), 0.4)
    k.plane("HkWall", (9, 4.5), (0, -1.9, 2.0), k.material("HkWallM", (0.03, 0.02, 0.05), 0.9), rot=(90, 0, 0))
    k.plane("HkFloor", (9, 9), (0, 0, 0), k.material("HkFloorM", (0.03, 0.025, 0.04), 0.5))
    cube("DeskFront", (2.4, 0.7, 0.05), (0, 0.75, 0.835), desk); cube("DeskFrontL", (0.05, 0.6, 0.82), (-1.15, 0.75, 0.41), black); cube("DeskFrontR", (0.05, 0.6, 0.82), (1.15, 0.75, 0.41), black)
    cube("ShelfBack", (3.0, 0.6, 0.05), (0, -1.2, 0.835), desk); cube("ShelfLegL", (0.05, 0.5, 0.82), (-1.45, -1.2, 0.41), black); cube("ShelfLegR", (0.05, 0.5, 0.82), (1.45, -1.2, 0.41), black)
    cube("ChairSeat", (0.7, 0.6, 0.08), (0, -0.05, 0.58), black)
    # monitors facing the camera (+Y)
    for i, (x, ang, w) in enumerate(((0.0, 0, 1.25), (-1.05, 18, 1.0), (1.05, -18, 1.0))):
        h = w * 9 / 16; z = 1.3 + h / 2 - 0.1
        cube("MonBez%d" % i, (w + 0.05, 0.04, h + 0.05), (x, -1.28, z), black, (0, 0, ang))
        k.plane("HkMon%d" % i, (w, h), (x, -1.255, z), _img_mat("HkMonM%d" % i, OUT + r"\hk_screen%d.png" % (i + 1), 2.0), rot=(90, 0, 180 + ang))
        cube("MonStand%d" % i, (0.08, 0.1, 0.45), (x, -1.3, 1.0), black)
    # laptop at the right, turned toward her (rot Z -30): lid back + stickers + glowing heart logo face the camera
    from mathutils import Matrix
    RZ = 30
    def lw(x, y, z):
        v = Matrix.Rotation(math.radians(RZ), 3, "Z") @ Vector((x, y, 0)); return (-0.42 + v.x, 0.62 + v.y, z)
    lapm = k.material("HkLap", (0.07, 0.065, 0.09), 0.3, 0.7)
    cube("LapBase", (0.52, 0.36, 0.022), lw(0, -0.07, 0.871), lapm, (0, 0, RZ))
    cube("LapLid", (0.52, 0.016, 0.28), lw(0, 0.14, 0.995), lapm, (-20, 0, RZ))
    k.plane("HkLapScreen", (0.48, 0.24), lw(0, 0.125, 0.995), k.material("HkLapScr", (0, 0, 0), 1, emit=(1.0, 0.75, 0.95), strength=5), rot=(90 - 20, 0, RZ))
    keym = bpy.data.materials.new("HkKeys"); keym.use_nodes = True; nt = keym.node_tree; bs = nt.nodes["Principled BSDF"]
    ck = nt.nodes.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 48; ck.inputs["Color1"].default_value = (1, 1, 1, 1); ck.inputs["Color2"].default_value = (0.02, 0.02, 0.02, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); rp = nt.nodes.new("ShaderNodeValToRGB"); mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1
    nt.links.new(tc.outputs["UV"], sp.inputs[0]); nt.links.new(sp.outputs["X"], rp.inputs[0]); nt.links.new(tc.outputs["UV"], ck.inputs["Vector"])
    rp.color_ramp.elements[0].color = (1.0, 0.15, 0.55, 1); rp.color_ramp.elements[1].color = (0.2, 0.7, 1.0, 1)
    nt.links.new(rp.outputs["Color"], mx.inputs[6]); nt.links.new(ck.outputs["Color"], mx.inputs[7]); nt.links.new(mx.outputs[2], bs.inputs["Emission Color"])
    bs.inputs["Emission Strength"].default_value = 2.2; bs.inputs["Base Color"].default_value = (0, 0, 0, 1)
    k.plane("HkKeys", (0.46, 0.2), lw(0, -0.1, 0.8835), keym, rot=(0, 0, RZ))
    # glowing heart logo + stickers on the lid back (+Y side of the lid)
    import bmesh
    def heart(name, s_, col, strength, dx, dz):
        bm = bmesh.new(); pts = []
        for j in range(48):
            t = j / 48 * 2 * math.pi
            pts.append(bm.verts.new((s_ * 16 * math.sin(t) ** 3 / 32, 0, s_ * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 32)))
        bm.faces.new(pts); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); me.materials.append(k.material(name + "M", col, 0.3, emit=col, strength=strength))
        o.location = lw(dx, 0.153, 0.995 + dz); o.rotation_euler = (math.radians(-20), 0, math.radians(180 + RZ)); o.scale.x = -1
    heart("HkLogo", 0.12, (1.0, 0.25, 0.6), 6.0, 0.0, 0.0)
    heart("HkSticker0", 0.06, (0.6, 0.35, 1.0), 1.0, -0.17, 0.06)
    heart("HkSticker1", 0.05, (0.3, 0.9, 1.0), 1.0, 0.17, -0.06)
    heart("HkSticker2", 0.04, (1.0, 0.85, 0.3), 1.0, 0.15, 0.08)
    # hair to true black: multiply the hair texture down
    hm = bpy.data.materials.get("Handle1Mtl")
    if hm and hm.node_tree and not hm.node_tree.nodes.get("HkDarken"):
        nt = hm.node_tree; bsd = nt.nodes["Principled BSDF"]; lk = bsd.inputs["Base Color"].links
        mixn = nt.nodes.new("ShaderNodeMix"); mixn.name = "HkDarken"; mixn.data_type = "RGBA"; mixn.blend_type = "MULTIPLY"
        mixn.inputs["Factor"].default_value = 1; mixn.inputs[7].default_value = (0.3, 0.3, 0.34, 1)
        if lk:
            src = lk[0].from_socket; nt.links.new(src, mixn.inputs[6])
        else:
            mixn.inputs[6].default_value = bsd.inputs["Base Color"].default_value
        nt.links.new(mixn.outputs[2], bsd.inputs["Base Color"])
        for nm in ("Specular IOR Level", "Specular"):
            if nm in bsd.inputs: bsd.inputs[nm].default_value = 0.15
    # clutter: cans
    for i, (x, y, c) in enumerate(((-0.8, -1.1, (1.0, 0.2, 0.6)), (0.78, -1.05, (0.3, 0.9, 1.0)), (-1.05, 0.8, (0.7, 0.4, 1.0)))):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.13, location=(x, y, 0.86 + 0.065), vertices=24)
        o = bpy.context.active_object; o.name = "HkCan%d" % i; o.data.materials.append(k.material("HkCanM%d" % i, c, 0.3, 0.8))
    # RGB strips
    k.led_strip([(-1.5, -0.9, 0.86), (1.5, -0.9, 0.86)], (1.0, 0.15, 0.55), 22, 0.012).name = "HkLEDa"
    k.led_strip([(-1.5, -1.8, 0.2), (-1.5, -1.8, 2.8), (1.5, -1.8, 2.8), (1.5, -1.8, 0.2)], (0.55, 0.25, 1.0), 14, 0.01).name = "HkLEDb"
    k.led_strip([(-1.2, 1.1, 0.83), (1.2, 1.1, 0.83)], (0.2, 0.85, 1.0), 14, 0.01).name = "HkLEDc"
    k.led_strip([(-0.66, -1.5, 1.28), (-0.66, -1.5, 2.1), (0.66, -1.5, 2.1), (0.66, -1.5, 1.28), (-0.66, -1.5, 1.28)], (1.0, 0.2, 0.6), 20, 0.01).name = "HkLEDd"
    k.show_camera()


def stage_light():
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)
    H = k.head_center()
    k.area("ScreenGlow", Vector((-0.32, 0.55, 1.05)), H, 7, 0.5, (1.0, 0.6, 0.9), 110)
    k.area("PurpleRim", Vector((-1.3, -0.9, 1.9)), H, 130, 0.8, (0.6, 0.3, 1.0), 100)
    k.area("CyanRim", Vector((1.4, -0.6, 1.7)), H, 110, 0.8, (0.25, 0.85, 1.0), 100)
    k.area("MonFill", Vector((0, -1.0, 1.5)), H, 15, 1.5, (1.0, 0.35, 0.75), 140)
    k.area("DeskPink", Vector((0.2, 1.2, 1.2)), Vector((0, 0.5, 0.9)), 6, 1.0, (1.0, 0.4, 0.8), 120)
    k.world((0.02, 0.01, 0.04), 0.1, haze=0.0008)
    k.setup_cycles(64, look="AgX - Punchy", exposure=0.0, dof_fstop=2.2)
    bpy.context.scene.camera.data.dof.focus_distance = (H - bpy.context.scene.camera.location).length
    k.show_camera()
