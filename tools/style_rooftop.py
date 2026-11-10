"""Rooftop Blue Hour GFX (Cortis-style, cool not cutesy) for Suhaa_Official.
POSE PLAN: sits on a concrete parapet ledge facing camera-left 3/4. Right leg (.P) knee up, hugged by the right arm; left leg (.N)
dangles over the edge; left hand rests on the ledge beside her; torso leaning slightly back-and-forward relaxed; head tilted ~12 deg
toward camera, flat cool expression.
CAMERA: low 3/4 from front-left, ~eye level of the head, 60mm, head_frac ~0.30, head in the right third, roll 3, skyline behind.
SET: dusk rooftop, city skyline with warm windows, rusty railing, water tank. LIGHT: cool blue fill + hard warm rim from the
horizon, skyline glow. GRADE: teal/orange, contrast, grain; her pink is the only soft colour."""
import sys, importlib, math, random
sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import bpy
from mathutils import Vector
import gfx_kit as k; importlib.reload(k)
ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
OUT = ROOT + r"\gfx_output\Suhaa_Official"


def stage_pose():
    k.apply_pose("sit")
    k.aim("LowerTorso", (0, 0.05, 1)); k.aim("UpperTorso", (0.02, 0.1, 1), (0.2, 1, 0))
    k.aim("Head", (0.2, 0.08, 0.98), (0.3, 1, 0.2))
    for sfx, sx in ((".P", 1), (".N", -1)):
        k.aim("UpperLeg" + sfx, (0.1 * sx, 1, 0.0)); k.aim("LowerLeg" + sfx, (0.0, 0.08, -1)); k.aim("Foot" + sfx, (0, 1, -0.2), (0, 0, 1))
        k.aim("UpperArm" + sfx, (0.3 * sx, 0.15, -0.94)); k.aim("LowerArm" + sfx, (0.05 * sx, 0.55, -0.83)); k.aim("Hand" + sfx, (0, 0.8, -0.2), (0, 0, 1))
    k.upd()


def stage_camera(head_frac=0.17, head_xy=(0.64, 0.24), view_dir=(0.5, 1, 0.0), lens=60, roll=3):
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    if not sc.camera:
        cd = bpy.data.cameras.new("Cam"); co = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(co); sc.camera = co
    print(k.frame_head(head_frac, head_xy=head_xy, view_dir=view_dir, lens=lens, roll=roll)); k.show_camera()


def low(parts):
    return min((o.matrix_world @ Vector(c)).z for o in k.arm().children if o.name.split(".")[0] in parts for c in o.bound_box)


def stage_set():
    for n in [o.name for o in bpy.data.objects if o.name.startswith(("Ledge", "Roof", "Sky", "Bld", "Win", "Rail", "Tank", "Floor", "Bokeh"))]:
        bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    a = k.arm(); k.upd()
    pel = low(("LowerTorso", "UpperLeg_P", "UpperLeg_N"))
    a.location.z += 0.685 - pel + 0.003; a.location.y = -0.6; a.location.x = 0.0; k.upd()
    conc = k.material("Concrete", (0.16, 0.17, 0.2), 0.9)
    dark = k.material("RoofDark", (0.04, 0.045, 0.055), 0.95)
    rust = k.material("Rust", (0.30, 0.13, 0.07), 0.7, 0.3)
    k.plane("RoofFloor", (60, 14), (0, 6.9, 0), dark)
    sky = k.plane("SkyBack", (1400, 400), (0, -330, 150), k.material("SkyGrad", (0, 0, 0), 1, emit=(1, 0.5, 0.2), strength=2.5), rot=(90, 0, 0))
    snt = sky.data.materials[0].node_tree; sb = snt.nodes["Principled BSDF"]
    stc = snt.nodes.new("ShaderNodeTexCoord"); ssp = snt.nodes.new("ShaderNodeSeparateXYZ"); sr = snt.nodes.new("ShaderNodeValToRGB")
    snt.links.new(stc.outputs["UV"], ssp.inputs[0]); snt.links.new(ssp.outputs["Y"], sr.inputs[0]); snt.links.new(sr.outputs["Color"], sb.inputs["Emission Color"])
    se = sr.color_ramp.elements; se[0].position = 0.11; se[0].color = (1.0, 0.4, 0.12, 1); se[1].position = 0.42; se[1].color = (0.02, 0.06, 0.26, 1)
    sm = sr.color_ramp.elements.new(0.19); sm.color = (0.42, 0.16, 0.38, 1)
    k.cube("LedgeWall", (6.0, 0.95, 0.62), (0, -0.5, 0.31), conc)
    k.cube("LedgeCap", (6.1, 1.05, 0.06), (0, -0.5, 0.65), k.material("ConcreteCap", (0.22, 0.23, 0.27), 0.85))
    # railing behind the ledge
    for i, x in enumerate([-2.4 + 0.6 * j for j in range(0, 9, 2)]):
        k.cube("RailPost%d" % i, (0.025, 0.025, 0.9), (x, -1.05, 1.1), rust)
    k.cube("RailTop", (5.0, 0.03, 0.03), (0, -1.05, 1.55), rust); pass
    # water tank on a low roof to the left
    bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=1.4, location=(-7.5, -4, 1.9), vertices=32)
    t = bpy.context.active_object; t.name = "TankBody"; t.data.materials.append(rust)
    k.cube("TankRoofBlock", (2.0, 2.0, 1.1), (-7.5, -4, 0.55), conc)
    # skyline: tiered buildings, rooftop boxes, antennas, grid windows (all lit windows in ONE mesh)
    import bmesh
    from mathutils import Matrix
    rnd = random.Random(11); wins = []; extra = []
    for i in range(150):
        x = rnd.uniform(-280, 280); y = rnd.uniform(-260, -90); far = (-y - 90) / 170
        w = rnd.uniform(12, 32); dp = rnd.uniform(10, 20)
        top = rnd.uniform(-45, 6) if rnd.random() < 0.85 else rnd.uniform(6, 38)
        shade = 0.03 + 0.05 * far
        col = (shade * 0.7, shade * 0.85, shade * 1.5 + 0.01)
        k.cube("Bld%d" % i, (w, dp, 120), (x, y, top - 60), k.material("BldM%d" % i, col, 0.9))
        if rnd.random() < 0.5:  # setback tier
            tw, tz = w * rnd.uniform(0.45, 0.7), rnd.uniform(4, 12)
            k.cube("Bld%d_t" % i, (tw, dp * 0.6, tz), (x + rnd.uniform(-w * 0.15, w * 0.15), y, top + tz / 2), k.material("BldT%d" % i, col, 0.9))
        if rnd.random() < 0.6:
            extra.append(((x + rnd.uniform(-w / 3, w / 3), y, top + 1.2), (rnd.uniform(1.5, 4), rnd.uniform(1.5, 4), 2.4)))  # rooftop box
        if rnd.random() < 0.45:
            hh = rnd.uniform(6, 22); extra.append(((x + rnd.uniform(-w / 3, w / 3), y, top + hh / 2), (0.35, 0.35, hh)))  # antenna
        by = y + dp / 2 + 0.03
        cols = int((w - 3) / 3.2); rows = int(min(60, 120) / 4.2)
        for c in range(cols):
            for r in range(rows):
                if rnd.random() < 0.28:
                    wins.append(((x - (cols - 1) * 1.6 + c * 3.2, by, top - 4 - r * 4.2), rnd.choice((0, 0, 0, 1))))
    bld_dark = k.material("RoofBits", (0.03, 0.04, 0.07), 0.9)
    for n, (loc, size) in enumerate(extra):
        k.cube("Bld_x%d" % n, size, loc, bld_dark)
    for kind, color, strength in ((0, (1.0, 0.62, 0.28), 5.0), (1, (0.7, 0.85, 1.0), 4.0)):
        bm = bmesh.new()
        for loc, kd in wins:
            if kd == kind:
                bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.LocRotScale(loc, None, (1.4, 0.2, 2.0)))
        me = bpy.data.meshes.new("WinMesh%d" % kind); bm.to_mesh(me); bm.free()
        wo = bpy.data.objects.new("WinAll%d" % kind, me); bpy.context.scene.collection.objects.link(wo)
        me.materials.append(k.material("WinGlow%d" % kind, (1, 1, 1), 0.5, emit=color, strength=strength))
    k.show_camera()


def stage_light():
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)
    H = k.head_center()
    # dusk sky gradient via world
    w = bpy.context.scene.world; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes["Background"]
    tc = nt.nodes.get("TC") or nt.nodes.new("ShaderNodeTexCoord"); tc.name = "TC"
    sep = nt.nodes.get("SEP") or nt.nodes.new("ShaderNodeSeparateXYZ"); sep.name = "SEP"
    ramp = nt.nodes.get("RAMP") or nt.nodes.new("ShaderNodeValToRGB"); ramp.name = "RAMP"
    mr = nt.nodes.get("MR") or nt.nodes.new("ShaderNodeMapRange"); mr.name = "MR"; mr.inputs["From Min"].default_value = -0.02; mr.inputs["From Max"].default_value = 0.5
    nt.links.new(tc.outputs["Window"] if False else tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], ramp.inputs[0]); nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    e = ramp.color_ramp.elements; e[0].position = 0.0; e[0].color = (1.0, 0.42, 0.18, 1); e[1].position = 1.0; e[1].color = (0.03, 0.08, 0.28, 1)
    bg.inputs["Strength"].default_value = 1.4
    k.area("Sunset", Vector((-5, -14, 1.3)), H, 2500, 4.0, (1.0, 0.55, 0.25), 80)   # hard warm rim from the horizon
    k.area("BlueFill", H + Vector((2.2, 2.6, 0.9)), H, 150, 3.0, (0.45, 0.62, 1.0), 150)
    k.area("FaceKick", H + Vector((1.4, 2.0, 0.1)), H, 18, 1.2, (0.85, 0.9, 1.0), 120)
    k.world((0.02, 0.04, 0.09), 0.2, haze=0.0007)
    k.setup_cycles(64, look="AgX - Punchy", exposure=0.1, dof_fstop=2.8)
    bpy.context.scene.camera.data.dof.focus_distance = (H - bpy.context.scene.camera.location).length
    k.world  # (world already set above)
    k.show_camera()


def cleanup():
    for n in ("Halo", "Backdrop"):
        if n in bpy.data.objects: bpy.data.objects[n].hide_render = True; bpy.data.objects[n].hide_viewport = True
