"""Pastel Window Seat welcome-back GFX for Suhaa_Official. Stage functions run in Blender via bl.py.
POSE PLAN: tripod camera, 3/4 from avatar's front-left, eye level of the seated head, 70mm, head_frac ~0.30,
head in upper-right third, roll 3. Seated sideways-ish on a window seat hugging knees: thighs forward+up, shins back+down,
left arm (.N) wrapped across shins, right arm (.P) bent up with the hand waving beside the cheek, head tilted ~12 deg to
the camera. Keychain hangs by the cushion edge; text sits on the empty left."""
import sys, importlib, math
sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import bpy
from mathutils import Vector
import gfx_kit as k; importlib.reload(k)
ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
OUT = ROOT + r"\gfx_output\Suhaa_Official"


def stage_avatar():
    bpy.ops.wm.save_as_mainfile(filepath=ROOT + r"\gfx_output\_session_backup_suhaa.blend", copy=True)
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.armatures, bpy.data.lights, bpy.data.cameras):
        for d in list(coll):
            if d.users == 0: coll.remove(d)
    G = {"__name__": "bx", "AVATAR_DIR": ROOT + r"\avatars\Suhaa_Official", "POSE": "idle"}
    exec(open(ROOT + r"\tools\build_exact_gfx.py", encoding="utf-8").read(), G)
    print("skinned", k.skin_clothes())


def stage_pose():
    k.apply_pose("sit")
    k.aim("LowerTorso", (0, 0.15, 1)); k.aim("UpperTorso", (0.04, 0.22, 0.97), (0.2, 1, 0))
    k.aim("Head", (0.2, 0.1, 0.97), (0.3, 1, 0.2))
    k.aim("UpperLeg.P", (0.12, 0.8, 0.55)); k.aim("LowerLeg.P", (0.0, -0.85, -0.52)); k.aim("Foot.P", (0, 0.9, -0.2), (0, 0, 1))
    k.aim("UpperLeg.N", (-0.12, 0.8, 0.55)); k.aim("LowerLeg.N", (0.0, -0.85, -0.52)); k.aim("Foot.N", (0, 0.9, -0.2), (0, 0, 1))
    # left arm (.N) hugs the shins
    k.aim("UpperArm.N", (-0.2, 0.35, -0.9)); k.aim("LowerArm.N", (0.8, 0.5, 0.3)); k.aim("Hand.N", (0.9, 0.3, 0.1), (0, 0, 1))
    # right arm (.P) waves beside the cheek
    k.aim("UpperArm.P", (0.75, 0.15, 0.1)); k.aim("LowerArm.P", (0.3, 0.2, 0.93)); k.aim("Hand.P", (0.2, 0.15, 0.97), (1, 0, 0))
    k.upd()
    a = k.arm()
    for b in ("LowerTorso", "UpperLeg.P", "LowerLeg.P", "Foot.P", "Head", "LowerArm.P", "Hand.P", "Hand.N"):
        print(b, tuple(round(x, 2) for x in a.matrix_world @ a.pose.bones[b].head))


def stage_camera(head_frac=0.30, head_xy=(0.66, 0.34), view_dir=(0.45, 1, 0.0), lens=70, roll=3):
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    if not sc.camera:
        cd = bpy.data.cameras.new("Cam"); co = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(co); sc.camera = co
    r = k.frame_head(head_frac, head_xy=head_xy, view_dir=view_dir, lens=lens, roll=roll)
    print(r); k.show_camera()


def quick(path, pct=40):
    sc = bpy.context.scene; old = sc.render.engine; sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"
    sc.render.resolution_percentage = pct; sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    sc.render.engine = old


def cleanup():
    for n in ("Halo", "Backdrop", "Handle3", "Handle2"):
        if n in bpy.data.objects: bpy.data.objects[n].hide_render = True; bpy.data.objects[n].hide_viewport = True


def low(parts):
    return min((o.matrix_world @ Vector(c)).z for o in k.arm().children if o.name.split(".")[0] in parts for c in o.bound_box)


def stage_set():
    for n in [o.name for o in bpy.data.objects if o.name.startswith(("Seat", "Wall", "Win", "Sky", "Curt", "Plush", "Floor", "Cush"))]:
        bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    a = k.arm(); k.upd()
    pel = low(("LowerTorso",)); feet = low(("Foot_P", "Foot_N"))
    print("pelvis low", round(pel, 3), "feet low", round(feet, 3))
    a.location.z += 0.40 - min(pel, feet) + 0.005; a.location.y = -0.55; k.upd()
    sc = bpy.context.scene
    pink = k.material("SeatPink", (0.95, 0.62, 0.72), 0.85)
    white = k.material("SillWhite", (0.95, 0.93, 0.93), 0.6)
    wallm = k.material("WallPink", (0.96, 0.78, 0.82), 0.9)
    # window wall behind her (y=-1.25) with a big bright pane, bench body + soft cushion
    k.plane("WallBack", (7, 4), (0, -1.25, 1.6), wallm, rot=(90, 0, 0))
    wg = k.plane("WinGlow", (1.9, 1.5), (0.0, -1.22, 1.5), k.material("SkyGlow", (0, 0, 0), 1, emit=(1.0, 0.82, 0.8), strength=4.6), rot=(90, 0, 0))
    nt = wg.data.materials[0].node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); cr = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["UV"], sp.inputs[0]); nt.links.new(sp.outputs["Y"], cr.inputs[0]); nt.links.new(cr.outputs["Color"], b.inputs["Emission Color"])
    cr.color_ramp.elements[0].color = (1.0, 0.68, 0.5, 1); cr.color_ramp.elements[1].color = (1.0, 0.6, 0.85, 1)
    for nm, sz, lc in (("WinFrameT", (2.1, 0.08, 0.1), (0, -1.2, 2.28)), ("WinFrameB", (2.1, 0.08, 0.1), (0, -1.2, 0.72)),
                       ("WinFrameL", (0.1, 0.08, 1.6), (-1.0, -1.2, 1.5)), ("WinFrameR", (0.1, 0.08, 1.6), (1.0, -1.2, 1.5)),
                       ("WinFrameM", (0.05, 0.08, 1.5), (0, -1.2, 1.5))):
        k.cube(nm, sz, lc, white)
    k.cube("SeatBase", (2.4, 0.75, 0.38), (0, -0.85, 0.19), white)
    c = k.cube("Cushion", (2.2, 0.7, 0.07), (0, -0.85, 0.415), pink)
    bv = c.modifiers.new("b", "BEVEL"); bv.width = 0.03; bv.segments = 3; c.modifiers.new("s", "SUBSURF").levels = 2
    k.plane("Floor", (9, 9), (0, 0, 0), k.material("FloorMat", (0.9, 0.82, 0.8), 0.7))
    # sheer curtains either side
    cur = k.material("Curtain", (1.0, 0.92, 0.94), 0.9)
    k.cube("CurtL", (0.45, 0.04, 2.5), (-1.28, -1.1, 1.45), cur); k.cube("CurtR", (0.45, 0.04, 2.5), (1.28, -1.1, 1.45), cur)
    # plushies: squashed spheres on the seat
    for i, (x, col, r) in enumerate(((-0.9, (1.0, 0.78, 0.86), 0.17), (-0.6, (0.95, 0.95, 1.0), 0.12), (0.98, (0.85, 0.7, 0.95), 0.16))):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(x, -0.85, 0.45 + r * 0.85), segments=48, ring_count=24)
        p = bpy.context.active_object; p.name = "Plush%d" % i; p.scale = (1.15, 0.95, 0.95); p.rotation_euler[2] = 0.4 * (i - 1)
        p.data.materials.append(k.material("PlushM%d" % i, col, 0.95)); bpy.ops.object.shade_smooth()
        for ex in (-0.5, 0.5):  # ears
            bpy.ops.mesh.primitive_uv_sphere_add(radius=r * 0.35, location=(x + ex * r * 1.0, -0.85, 0.45 + r * 1.85), segments=24, ring_count=12)
            e = bpy.context.active_object; e.name = "Plush%d_ear" % i; e.data.materials.append(p.data.materials[0]); bpy.ops.object.shade_smooth()
    k.show_camera()


def stage_light():
    for o in [o for o in bpy.data.objects if o.type == "LIGHT" or o.name.startswith(("Bokeh", "FairyB", "WinFrameM"))]:
        bpy.data.objects.remove(o, do_unlink=True)
    H = k.head_center()
    # warm backlight through the window (the emissive pane lights the room too)
    k.area("WindowKey", Vector((0.2, -1.1, 1.5)), H, 380, 2.2, (1.0, 0.9, 0.78), 120)
    k.area("PinkFill", H + Vector((1.6, 1.8, 0.2)), H, 32, 2.5, (1.0, 0.62, 0.78), 150)
    k.area("PinkRim", H + Vector((-1.0, -0.9, 0.7)), H, 40, 0.8, (1.0, 0.55, 0.8), 100)
    k.area("FaceKey", H + Vector((0.9, 1.6, 0.35)), H, 22, 1.5, (1.0, 0.92, 0.9), 150)
    # fairy-light bokeh outside the glass
    k.bokeh_lights(Vector((0, -1.1, 1.5)), count=45, spread=(0.9, 0.04, 0.7), colors=((1, 0.8, 0.5), (1, 0.55, 0.75)), strength=9, seed=5)
    k.world((0.95, 0.72, 0.8), 0.35, haze=0.004)
    sc = bpy.context.scene
    k.setup_cycles(64, look="AgX - Punchy", exposure=-0.35, dof_fstop=2.2)
    sc.camera.data.dof.focus_distance = (k.head_center() - sc.camera.location).length
    k.show_camera()


def _font(name):
    import glob
    f = glob.glob(ROOT + r"\libraryonts\%s\*.ttf" % name) + glob.glob(ROOT + r"\libraryonts\%s\*.otf" % name)
    return bpy.data.fonts.load(f[0]) if f else None


def _text(name, body, size, font, mat, extrude, bevel, offset=0.0):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    cu.extrude = extrude; cu.bevel_depth = bevel; cu.bevel_resolution = 4; cu.offset = offset
    if font: cu.font = font
    o = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(o); o.data.materials.append(mat)
    o.rotation_euler = (math.radians(90), 0, math.radians(180)); return o


def stage_text(target=(0.27, 0.5)):
    for o in [o for o in bpy.data.objects if o.name.startswith("Txt")]: bpy.data.objects.remove(o, do_unlink=True)
    sc = bpy.context.scene; font = _font("pacifico"); cam = sc.camera
    pink = k.material("TxtPink", (1.0, 0.3, 0.6), 0.2)
    b = pink.node_tree.nodes["Principled BSDF"]; b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = 0.05
    b.inputs["Emission Color"].default_value = (1.0, 0.25, 0.55, 1); b.inputs["Emission Strength"].default_value = 0.6
    white = k.material("TxtWhite", (0.42, 0.04, 0.2), 0.35)
    objs = []
    for nm, body, size, dz in (("Txt1", "welcome back", 0.2, 0.15), ("Txt2", "Suhie", 0.34, -0.12)):
        t = _text(nm, body, size, font, pink, 0.035, 0.012)
        o = _text(nm + "_outline", body, size, font, white, 0.02, 0.03)
        objs.append((t, o, dz))
    C = Vector((0.2, -0.98, 1.35))
    for _ in range(10):
        x, y, d = k.project(C)
        right = cam.matrix_world.to_quaternion() @ Vector((1, 0, 0))
        w = d * 36 / cam.data.lens; h = w * 9 / 16
        C += right * (target[0] - x) * w; C.z -= (target[1] - y) * h
    for t, o, dz in objs:
        t.scale = o.scale = (0.55, 0.55, 0.55); dz *= 0.55
        t.location = C + Vector((0, 0, dz)); o.location = C + Vector((0, -0.03, dz))
        print(t.name, [round(v, 2) for v in t.location], [round(v, 2) for v in k.project(t.location)])
    k.show_camera()
