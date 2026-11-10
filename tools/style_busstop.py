"""Rainy Bus Stop GFX for DI3STINY. Stage functions run in Blender via bl.py (exec'd into one namespace)."""
import sys, importlib, math
sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import bpy
from mathutils import Vector
import gfx_kit as k; importlib.reload(k)

def stage_avatar():
    G = {"__name__": "bx", "AVATAR_DIR": r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\avatars\DI3STINY", "POSE": "idle"}
    exec(open(r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools\build_exact_gfx.py", encoding="utf-8").read(), G)
    print("skinned", k.skin_clothes())

def stage_pose():
    k.apply_pose("sit")
    # forward lean, head tilt/turn, elbows on knees, sneakers crossed
    k.aim("LowerTorso", (0.0, 0.2, 1)); k.aim("UpperTorso", (0.05, 0.4, 0.92), (0.2, 1, 0))
    k.aim("Head", (0.22, 0.2, 0.95), (0.3, 1, 0.3))
    k.aim("UpperArm.P", (0.12, 0.55, -0.82)); k.aim("LowerArm.P", (-0.25, 0.85, -0.2)); k.aim("Hand.P", (-0.3, 0.9, -0.1), (0, 0, 1))
    k.aim("UpperArm.N", (-0.12, 0.55, -0.82)); k.aim("LowerArm.N", (0.25, 0.85, -0.2)); k.aim("Hand.N", (0.3, 0.9, -0.1), (0, 0, 1))
    k.aim("LowerLeg.P", (0.1, 0.25, -1)); k.aim("LowerLeg.N", (-0.1, 0.25, -1))
    k.upd()
    a = k.arm()
    for b in ("LowerTorso", "UpperLeg.P", "Foot.P", "Head"):
        print(b, tuple(round(x, 2) for x in a.matrix_world @ a.pose.bones[b].head))

def stage_set():
    for n in ("Backdrop", "Halo"):
        if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    a = k.arm(); k.upd()
    feet = min((o.matrix_world @ Vector(c)).z for o in a.children if o.name.startswith("Foot") for c in o.bound_box)
    a.location.z -= feet - 0.02; k.upd()
    seat = min((o.matrix_world @ Vector(c)).z for o in a.children if o.name.startswith("UpperLeg") for c in o.bound_box)
    # ground: wet asphalt + kerb
    g = k.plane("Ground", (14, 14), (0, 2, 0), k.pbr("asphalt_02", 1.2, tint=(0.35, 0.36, 0.4)))
    b = g.data.materials[0].node_tree.nodes["Principled BSDF"]
    rl = b.inputs["Roughness"].links
    if rl: g.data.materials[0].node_tree.links.remove(rl[0])
    b.inputs["Roughness"].default_value = 0.08
    k.cube("Kerb", (14, 0.3, 0.12), (0, 1.25, 0.06), k.pbr("concrete_floor_worn_001", 1.5, tint=(0.5, 0.5, 0.52)))
    k.plane("Pavement", (14, 1.9), (0, 0.17, 0.121), k.pbr("concrete_floor_02", 1.0, tint=(0.4, 0.4, 0.42)))
    # bench (seat top under her thighs), metal legs
    wood = k.pbr("weathered_brown_planks", 1.5, tint=(0.45, 0.4, 0.38))
    for i in range(3):
        k.cube("Slat", (1.9, 0.11, 0.035), (0.1, -0.2 + i * 0.13, seat - 0.018), wood)
    metal = k.material("DarkMetal", (0.04, 0.045, 0.05), 0.35, 0.9)
    for x in (-0.75, 0.95):
        k.cube("BenchLeg", (0.05, 0.38, seat - 0.12), (x, -0.07, 0.12 + (seat - 0.12) / 2), metal)
    # shelter: back glass with rain-dirt, posts, roof, lit advert
    glass = k.material("Glass", (0.6, 0.7, 0.75), 0.25); gb = glass.node_tree.nodes["Principled BSDF"]
    gb.inputs["Transmission Weight"].default_value = 0.85
    k.cube("BackGlass", (3.0, 0.02, 1.9), (0.3, -0.5, 0.12 + 0.95 + 0.08), glass)
    for x in (-1.2, 1.8):
        k.cube("Post", (0.07, 0.07, 2.3), (x, -0.5, 1.27), metal)
        k.cube("PostF", (0.07, 0.07, 2.3), (x, 0.65, 1.27), metal)
    k.cube("Roof", (3.3, 1.5, 0.06), (0.3, 0.08, 2.43), metal)
    k.cube("Advert", (0.9, 0.04, 1.4), (1.35, -0.47, 1.05), k.material("AdLight", (0.9, 0.95, 1), 0.4, emit=(0.55, 0.75, 1.0), strength=4))
    k.cube("AdFrame", (0.98, 0.05, 1.48), (1.35, -0.475, 1.05), metal)
    # sodium street lamp off left, behind; bus-stop sign
    k.import_model("lighting", "street_lamp_01", loc=(-2.6, -1.4, 0), rot_z=0, scale=1.0)
    k.cube("SignPole", (0.05, 0.05, 2.6), (-1.6, 0.9, 1.3), metal)
    k.cube("Sign", (0.5, 0.03, 0.35), (-1.6, 0.9, 2.45), k.material("SignGlow", (1, 0.55, 0.15), 0.4, emit=(1, 0.5, 0.12), strength=6))
    # far street bokeh behind the glass
    k.bokeh_lights((0.5, -6, 1.5), count=30, spread=(5, 1.5, 1.2), colors=((1, 0.55, 0.2), (0.3, 0.6, 1.0), (1, 0.2, 0.25)), strength=25)
    print("seat", round(seat, 3), "feet", round(feet, 3))
    k.show_camera()

def stage_camera():
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 1080, 1350
    if not sc.camera:
        cd = bpy.data.cameras.new("Cam"); co = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(co); sc.camera = co
    r = k.frame_head(0.2, head_xy=(0.36, 0.3), view_dir=(0.45, 1, -0.22), lens=50, roll=5)
    cam = sc.camera; H = k.head_center(); d = cam.location - H
    el = math.degrees(math.asin(d.z / d.length)); az = math.degrees(math.atan2(d.x, d.y))
    assert -20 < el < 0 and 15 < az < 35, (el, az)
    print("camera", r, "el", round(el, 1), "az", round(az, 1), "z", round(cam.location.z, 2))
    k.show_camera()

def stage_light():
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]: bpy.data.objects.remove(o, do_unlink=True)
    H = k.head_center()
    k.area("SodiumKey", H + Vector((-1.6, 1.4, 1.3)), H, 160, 0.6, (1.0, 0.55, 0.2))
    k.area("BlueRim", H + Vector((1.2, -1.5, 0.6)), H, 140, 0.5, (0.35, 0.6, 1.0))
    k.area("StreetFill", H + Vector((0.5, 2.5, 0.2)), H, 15, 3.0, (0.4, 0.5, 0.75))
    k.area("LampPool", Vector((-2.4, -1.2, 3.2)), Vector((-1.5, 0, 0)), 300, 1.0, (1.0, 0.5, 0.15))
    k.world((0.012, 0.016, 0.03), 1.0, haze=0.025)
    import random; rnd = random.Random(7); import bmesh
    bm = bmesh.new()
    for _ in range(900):
        x, y, z = rnd.uniform(-2.5, 3.0), rnd.uniform(-1.0, 3.5), rnd.uniform(0, 3.0)
        if -0.6 < y < 0.75 and -1.3 < x < 1.9 and z < 2.4: continue
        L = rnd.uniform(0.12, 0.3); w = 0.0025
        vs = [bm.verts.new((x + dx, y, z + dz)) for dx, dz in ((-w, 0), (w, 0), (w + L * 0.12, L), (-w + L * 0.12, L))]
        bm.faces.new(vs)
    me = bpy.data.meshes.new("Rain"); bm.to_mesh(me); o = bpy.data.objects.new("Rain", me); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(k.material("RainMat", (0.8, 0.85, 1), 0.1, emit=(0.6, 0.7, 1.0), strength=0.6, alpha=0.35))
    k.setup_cycles(96, look="AgX - Punchy", exposure=-0.3, dof_fstop=2.8)
    sc = bpy.context.scene; sc.camera.data.dof.focus_object = None
    k.show_camera()

def stage_fix2():
    # arms: forearms resting down onto the knees, hands following
    k.aim("UpperArm.P", (0.15, 0.35, -0.92)); k.aim("LowerArm.P", (-0.1, 0.75, -0.65)); k.aim("Hand.P", (-0.1, 0.6, -0.8), (0, 0, 1))
    k.aim("UpperArm.N", (-0.15, 0.35, -0.92)); k.aim("LowerArm.N", (0.1, 0.75, -0.65)); k.aim("Hand.N", (0.1, 0.6, -0.8), (0, 0, 1))
    k.aim("Head", (0.25, 0.22, 0.94), (0.45, 1, 0.3)); k.upd()
    gb = bpy.data.materials["Glass"].node_tree.nodes["Principled BSDF"]
    gb.inputs["Base Color"].default_value = (0.05, 0.07, 0.09, 1); gb.inputs["Transmission Weight"].default_value = 0.0
    gb.inputs["Roughness"].default_value = 0.06; gb.inputs["Alpha"].default_value = 0.35
    pv = bpy.data.objects["Pavement"]; pv.data.materials[0] = k.pbr("gravel_embedded_concrete", 1.2, tint=(0.3, 0.31, 0.34))
    bpy.data.lights["SodiumKey"].energy *= 0.55; bpy.data.lights["LampPool"].energy *= 0.4
    bpy.data.lights["BlueRim"].energy *= 1.6; bpy.data.lights["StreetFill"].energy *= 2.5
    k.world((0.01, 0.018, 0.04), 1.0, haze=0.02)
    r = k.frame_head(0.3, head_xy=(0.38, 0.3), view_dir=(0.45, 1, -0.2), lens=50, roll=5)
    cam = bpy.context.scene.camera; c = cam.location
    rain = bpy.data.objects["Rain"]; me = rain.data
    import bmesh; bm = bmesh.new(); bm.from_mesh(me)
    bad = [f for f in bm.faces if (f.calc_center_median() - c).length < 1.3]
    bmesh.ops.delete(bm, geom=bad, context="FACES"); bm.to_mesh(me)
    bpy.data.materials["RainMat"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.35
    bpy.context.scene.camera.data.dof.focus_distance = (k.head_center() - c).length
    print(r); k.show_camera()

def stage_fix3():
    k.aim("Head", (0.3, 0.25, 0.92), (0.75, 1, 0.1)); k.upd()   # tilt toward near shoulder, face turned off-lens
    gb = bpy.data.materials["Glass"].node_tree.nodes["Principled BSDF"]
    gb.inputs["Roughness"].default_value = 0.35; gb.inputs["Alpha"].default_value = 0.18
    for o in [o for o in bpy.data.objects if o.name.startswith("Bokeh")]:
        o.scale = (2.2,) * 3; o.location.y = -3.5
    H = k.head_center()
    rim = bpy.data.objects["BlueRim"]; rim.location = H + Vector((0.9, -1.0, 0.9))
    rim.rotation_euler = (H - rim.location).to_track_quat("-Z", "Y").to_euler(); bpy.data.lights["BlueRim"].energy = 220
    ad = bpy.data.objects["Advert"]; ad.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 6
    for n in ("Advert", "AdFrame"): bpy.data.objects[n].location.x = 0.85
    r = k.frame_head(0.24, head_xy=(0.33, 0.3), view_dir=(0.45, 1, -0.2), lens=50, roll=5)
    print(r); k.show_camera()

def stage_fix4():
    import random; rnd = random.Random(11)
    for o in [o for o in bpy.data.objects if o.name.startswith("Bokeh")]:
        o.scale = (rnd.uniform(0.6, 1.5),) * 3; o.location.y = rnd.uniform(-8, -5)
    bpy.data.objects["AdFrame"].location.y = -0.5
    bpy.data.objects["Advert"].location.y = -0.455
    r = k.frame_head(0.3, head_xy=(0.36, 0.27), view_dir=(0.45, 1, -0.2), lens=50, roll=5)
    bpy.context.scene.camera.data.dof.focus_distance = r["dist"]; bpy.context.scene.camera.data.dof.aperture_fstop = 2.0
    print(r); k.show_camera()

def stage_fix5():
    for n in ("Advert", "AdFrame"):
        o = bpy.data.objects[n]; print(n, tuple(round(v, 2) for v in o.location), o.data.materials[0].name, k.project(o.location))
    ad = bpy.data.objects["Advert"]; ad.location = (1.25, -0.44, 1.05)
    bpy.data.objects["AdFrame"].location = (1.25, -0.49, 1.05)
    H = k.head_center(); rim = bpy.data.objects["BlueRim"]; rim.location = H + Vector((0.7, -1.1, 1.0))
    rim.rotation_euler = (H - rim.location).to_track_quat("-Z", "Y").to_euler(); bpy.data.lights["BlueRim"].energy = 450
    bpy.data.lights["BlueRim"].color = (0.3, 0.55, 1.0)
    bpy.data.lights["StreetFill"].energy *= 1.8; bpy.data.lights["StreetFill"].color = (0.3, 0.45, 0.85)
    hz = bpy.context.scene.world.node_tree.nodes["Haze"]; hz.inputs["Color"].default_value = (0.55, 0.7, 1.0, 1)
    print("ad proj", k.project(ad.location)); k.show_camera()

def stage_advert():
    m = bpy.data.objects["Advert"].data.materials[0]; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3; nt.links.new(tc.outputs["Generated"], nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MULTIPLY_ADD"; mx.inputs[1].default_value = 0.85
    nt.links.new(sep.outputs["Z"], mx.inputs[0]); nt.links.new(nz.outputs["Fac"], mx.inputs[2])
    mx.inputs[2].default_value = 0.1
    rp = nt.nodes.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
    el[0].position, el[0].color = 0.1, (0.35, 0.03, 0.08, 1); el[1].position, el[1].color = 0.95, (0.05, 0.18, 0.6, 1)
    nt.links.new(mx.outputs[0], rp.inputs[0]); nt.links.new(rp.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 2.0; k.show_camera()

def stage_v2():
    """Owner preferred preview 1: warm sodium key, dense rain; keep tight framing. Thin blue rim on the hair only."""
    L = bpy.data.lights; H = k.head_center()
    L["SodiumKey"].energy = 160 * (k.Vector if False else 1) * ((bpy.data.objects["SodiumKey"].location - H).length ** 0 ) * 1.0
    # area() scaled energy by nothing; restore stage_light values
    L["SodiumKey"].energy = 160; L["LampPool"].energy = 300; L["StreetFill"].energy = 15; L["StreetFill"].color = (0.4, 0.5, 0.75)
    rim = bpy.data.objects["BlueRim"]; rim.location = H + Vector((0.5, -1.2, 1.1))
    rim.rotation_euler = (H - rim.location).to_track_quat("-Z", "Y").to_euler(); L["BlueRim"].energy = 90; L["BlueRim"].size = 0.3
    hz = bpy.context.scene.world.node_tree.nodes["Haze"]; hz.inputs["Color"].default_value = (1, 1, 1, 1); hz.inputs["Density"].default_value = 0.03
    bpy.context.scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.016, 0.03, 1)
    # dense rain, none within 1.3 m of the lens or inside the shelter
    import random, bmesh; rnd = random.Random(21); c = bpy.context.scene.camera.location
    old = bpy.data.objects["Rain"]; mat = old.data.materials[0]; bpy.data.objects.remove(old, do_unlink=True)
    bm = bmesh.new()
    for _ in range(4000):
        x, y, z = rnd.uniform(-3, 3.5), rnd.uniform(-4, 3.5), rnd.uniform(0, 3.2)
        if (-0.6 < y < 0.75 and -1.3 < x < 1.9 and z < 2.4) or (Vector((x, y, z)) - c).length < 1.3: continue
        Ln = rnd.uniform(0.12, 0.32); w = 0.0022
        bm.faces.new([bm.verts.new((x + dx, y, z + dz)) for dx, dz in ((-w, 0), (w, 0), (w + Ln * 0.12, Ln), (-w + Ln * 0.12, Ln))])
    me = bpy.data.meshes.new("Rain"); bm.to_mesh(me); o = bpy.data.objects.new("Rain", me); bpy.context.scene.collection.objects.link(o)
    me.materials.append(mat); mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.6
    # advert: smaller, dim, at the right edge
    ad = bpy.data.objects["Advert"]; fr = bpy.data.objects["AdFrame"]
    ad.scale = (0.55, 0.04, 0.85); fr.scale = (0.6, 0.05, 0.9)
    ad.location = (-1.0, -0.44, 1.2); fr.location = (-1.0, -0.49, 1.2)
    ad.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.5
    k.show_camera()

def stage_v2b():
    for n in ("Advert", "AdFrame"): bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    import bmesh; o = bpy.data.objects["Rain"]; bm = bmesh.new(); bm.from_mesh(o.data)
    hx, hy, hd = k.project(k.head_center())
    bad = [f for f in bm.faces if (lambda p: abs(p[0] - hx) < 0.2 and abs(p[1] - hy) < 0.16 and p[2] < hd + 0.3)(k.project(f.calc_center_median()))]
    bmesh.ops.delete(bm, geom=bad, context="FACES"); bm.to_mesh(o.data); print("rain removed near face", len(bad))
    k.show_camera()

def _solve_x(y, z, fx, lo=-4, hi=4):
    for _ in range(40):
        m = (lo + hi) / 2; px = k.project(Vector((m, y, z)))[0]
        lo, hi = (m, hi) if (px > fx) == (k.project(Vector((hi, y, z)))[0] > fx) else (lo, m)
    return m

def _solve_z(x, y, fy, lo=0, hi=5):
    for _ in range(40):
        m = (lo + hi) / 2
        if k.project(Vector((x, y, m)))[1] < fy: lo = m   # project y: 0 top? check sign below
        else: hi = m
    return m

def stage_v3():
    """Round 3: bus-stop sign in frame, roof edge across the top, puddles, softer hands. Rest unchanged."""
    # hands rest on the knees instead of hanging down
    k.aim("LowerArm.P", (-0.1, 0.8, -0.58)); k.aim("Hand.P", (-0.25, 0.85, -0.45), (0, 0, 1))
    k.aim("LowerArm.N", (0.1, 0.8, -0.58)); k.aim("Hand.N", (0.25, 0.85, -0.45), (0, 0, 1)); k.upd()
    print("proj y check: head", k.project(k.head_center()))
    metal = bpy.data.materials["DarkMetal"]
    # roof: front edge visible across the top ~4% of frame, with a fluorescent tube underneath
    yf = 0.75; xm = _solve_x(yf, 2.0, 0.5)
    zr = _solve_z(xm, yf, 0.05) if k.project(Vector((xm, yf, 3)))[1] < k.project(Vector((xm, yf, 1)))[1] else 2.3
    roof = bpy.data.objects["Roof"]; roof.location.z = zr + 0.03; roof.location.y = yf - 0.7; roof.scale = (5, 1.5, 0.06)
    k.cube("RoofFascia", (5, 0.04, 0.16), (xm, yf, zr), k.material("Fascia", (0.03, 0.035, 0.04), 0.4, 0.8))
    k.cube("Tube", (1.2, 0.04, 0.03), (xm - 0.3, yf - 0.5, zr - 0.04), k.material("TubeGlow", (1, 1, 1), 0.3, emit=(0.75, 0.9, 1.0), strength=8))
    # bus stop sign on its pole at the right of frame
    sx = _solve_x(1.4, 1.9, 0.86)
    for n in ("SignPole", "Sign"):
        if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    k.cube("SignPole", (0.05, 0.05, 2.8), (sx, 1.4, 1.4), metal)
    k.cube("Sign", (0.04, 0.42, 0.42), (sx, 1.4, 2.05), k.material("SignFace", (0, 0, 0), 0.4, emit=(1, 0.45, 0.1), strength=3))
    t = k.neon_text("BUS", (sx - 0.025, 1.4, 1.98), color=(1, 0.95, 0.85), size=0.13, strength=6, font="anton", rot=(90, 0, -90))
    # puddles: noise mask, mirror-like roughness and darker colour inside
    m = bpy.data.objects["Ground"].data.materials[0]; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.9; nz.inputs["Detail"].default_value = 4
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    rp = nt.nodes.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].position = 0.48; rp.color_ramp.elements[1].position = 0.53
    nt.links.new(nz.outputs["Fac"], rp.inputs["Fac"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[3].default_value = 0.01; mr.inputs[4].default_value = 0.22
    nt.links.new(rp.outputs["Color"], mr.inputs[0]); nt.links.new(mr.outputs[0], b.inputs["Roughness"])
    src = b.inputs["Base Color"].links[0].from_socket
    dk = nt.nodes.new("ShaderNodeMix"); dk.data_type = "RGBA"; dk.blend_type = "MULTIPLY"
    nt.links.new(rp.outputs["Color"], dk.inputs["Factor"]); dk.inputs["Factor"].default_value = 1
    inv = nt.nodes.new("ShaderNodeInvert"); nt.links.new(rp.outputs["Color"], inv.inputs["Color"]); nt.links.new(inv.outputs[0], dk.inputs["Factor"])
    nt.links.new(src, dk.inputs[6]); dk.inputs[7].default_value = (0.35, 0.35, 0.38, 1); nt.links.new(dk.outputs[2], b.inputs["Base Color"])
    print("roof z", round(zr, 2), "sign x", round(sx, 2), "sign proj", k.project(Vector((sx, 1.4, 2.05))))
    k.show_camera()

def _best(f, vals):
    return min(vals, key=f)

def stage_v3_fix():
    for o in [o for o in bpy.data.objects if o.name.split(".")[0] in ("RoofFascia", "Tube", "Sign", "SignPole", "Neon")]:
        bpy.data.objects.remove(o, do_unlink=True)
    xs = [i * 0.02 for i in range(-200, 201)]; zs = [i * 0.01 for i in range(100, 500)]
    yf = 0.75; xm = _best(lambda x: abs(k.project(Vector((x, yf, 2.0)))[0] - 0.5), xs)
    zr = _best(lambda z: abs(k.project(Vector((xm, yf, z)))[1] - 0.05), zs)
    roof = bpy.data.objects["Roof"]; roof.location = (xm, yf - 0.7, zr + 0.06); roof.scale = (5, 1.5, 0.06)
    k.cube("RoofFascia", (5, 0.04, 0.16), (xm, yf, zr), k.material("Fascia", (0.03, 0.035, 0.04), 0.4, 0.8))
    k.cube("Tube", (1.2, 0.04, 0.03), (xm - 0.3, yf - 0.4, zr - 0.04), k.material("TubeGlow", (1, 1, 1), 0.3, emit=(0.75, 0.9, 1.0), strength=8))
    ys = 0.9; sx = _best(lambda x: abs(k.project(Vector((x, ys, 1.8)))[0] - 0.86), xs)
    sz = _best(lambda z: abs(k.project(Vector((sx, ys, z)))[1] - 0.2), zs)
    metal = bpy.data.materials["DarkMetal"]
    k.cube("SignPole", (0.05, 0.05, sz + 0.5), (sx, ys, (sz + 0.5) / 2), metal)
    k.cube("Sign", (0.04, 0.4, 0.4), (sx, ys, sz), k.material("SignFace", (0, 0, 0), 0.4, emit=(1, 0.45, 0.1), strength=3))
    cam = bpy.context.scene.camera.location; ang = math.degrees(math.atan2(cam.y - ys, cam.x - sx))
    s = bpy.data.objects["Sign"]; s.rotation_euler[2] = math.radians(ang)
    k.neon_text("BUS", (sx + 0.03 * math.cos(math.radians(ang)), ys + 0.03 * math.sin(math.radians(ang)), sz - 0.05),
                color=(1, 0.95, 0.85), size=0.13, strength=6, font="anton", rot=(90, 0, ang - 90))
    print("roof", round(zr, 2), k.project(Vector((xm, yf, zr))), "sign", round(sx, 2), round(sz, 2), k.project(Vector((sx, ys, sz))))
    k.show_camera()
