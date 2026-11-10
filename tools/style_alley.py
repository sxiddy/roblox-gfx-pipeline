"""Neon Alley Villain GFX for Bio_IsHere. Stage functions run in Blender via bl.py (exec'd into one namespace)."""
import sys, importlib, math, random
sys.path.insert(0, r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools")
import bpy, bmesh
from mathutils import Vector
import gfx_kit as k; importlib.reload(k)

ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
OUT = ROOT + r"\gfx_output\Bio_IsHere"

def stage_avatar():
    G = {"__name__": "bx", "AVATAR_DIR": ROOT + r"\avatars\Bio_IsHere", "POSE": "idle"}
    exec(open(ROOT + r"\tools\build_exact_gfx.py", encoding="utf-8").read(), G)
    for n in ("Backdrop", "Halo"):
        if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    print("skinned", k.skin_clothes())
    for o in sorted(bpy.data.objects, key=lambda o: o.name):
        if o.type == "MESH":
            m = o.data.materials[0].name if o.data.materials else "-"
            print(o.name, o.parent.name if o.parent else "-", o.parent_bone, tuple(round(d, 2) for d in o.dimensions), m)

# Pose plan: back against the alley wall (wall at -Y), hips slightly forward, torso leaning back.
# Avatar's right arm (P, screen-left) hangs with the hand at the hip pocket; left arm (N, screen-right)
# raised in a palm-up "what?" shrug toward the camera. Head chin-down, turned a little to the lens.
# Camera low (looks up ~15 deg), 35mm, 4:5 portrait, waist-up, head in the upper third, roll 5 deg.
def stage_pose():
    k.reset_pose()
    k.aim("LowerTorso", (0, -0.05, 1)); k.aim("UpperTorso", (0.04, -0.14, 0.99), (0.15, 1, 0))
    k.aim("Head", (-0.05, 0.1, 0.99), (0.2, 1, -0.12))
    # raised arm on the P side (screen-left) so it stays clear of the spear blade at his N hip
    k.aim("UpperArm.N", (-0.18, 0.02, -1)); k.aim("LowerArm.N", (0.1, 0.18, -1)); k.aim("Hand.N", (0.1, 0.2, -1), (-1, 0, 0))
    k.aim("UpperArm.P", (0.6, 0.3, -0.75)); k.aim("LowerArm.P", (0.3, 1, 0.3)); k.aim("Hand.P", (0.35, 1, 0.15), (0, 0, 1))
    k.aim("UpperLeg.P", (0.08, 0.1, -1)); k.aim("UpperLeg.N", (-0.12, 0.05, -1))
    k.upd(); a = k.arm()
    for b in ("Head", "Hand.P", "Hand.N", "Foot.P"):
        print(b, tuple(round(x, 2) for x in a.matrix_world @ a.pose.bones[b].head))

def stage_set():
    a = k.arm(); keep = set(a.children_recursive) | {a, bpy.context.scene.camera}
    for o in [o for o in bpy.context.scene.objects if o not in keep]:
        bpy.data.objects.remove(o, do_unlink=True)  # wipes old-project leftovers and our previous set
    k.upd()
    feet = min((o.matrix_world @ Vector(c)).z for o in a.children if o.name.startswith("Foot") for c in o.bound_box)
    a.location.z -= feet; k.upd()
    back = min((o.matrix_world @ Vector(c)).y for o in a.children if o.name in ("UpperTorso", "LowerTorso") for c in o.bound_box)
    wy = back - 0.02
    # wet asphalt
    g = k.plane("Ground", (12, 12), (0, 2, 0), k.pbr("asphalt_02", 1.2, tint=(0.3, 0.3, 0.34)))
    b = g.data.materials[0].node_tree.nodes["Principled BSDF"]
    rl = b.inputs["Roughness"].links
    if rl: g.data.materials[0].node_tree.links.remove(rl[0])
    b.inputs["Roughness"].default_value = 0.1
    # back wall (behind him) and a side wall going toward the camera on screen-right (world -X)
    wall = k.pbr("concrete_layers_02", 0.9, tint=(0.16, 0.15, 0.17))
    k.cube("Wall", (8, 0.3, 5), (0, wy - 0.15, 2.5), wall)
    k.cube("WallR", (0.3, 8, 5), (-2.2, wy + 4, 2.5), wall)
    # neon SINNERS sign above-right of him, purple; small yellow "OPEN"-style accent
    hz = k.head_center().z
    s = k.neon_text("SINNERS", (-0.62, wy + 0.04, hz + 0.08), color=(0.55, 0.1, 1.0), size=0.2, strength=14, font="monoton")
    k.cube("SignBack", (1.12, 0.03, 0.28), (-0.62, wy + 0.015, hz + 0.13), k.material("SignBack", (0.01, 0.01, 0.012), 0.8))
    # pipes and a dumpster on screen-left (world +X)
    metal = k.material("DarkMetal", (0.04, 0.045, 0.05), 0.35, 0.9)
    for x in (0.9, 1.05):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=5, location=(x, wy + 0.06, 2.5)); o = bpy.context.active_object
        o.name = "Pipe"; o.data.materials.append(metal)
    k.cube("Dumpster", (1.4, 0.8, 1.0), (1.9, wy + 0.45, 0.5), k.pbr("green_metal_rust", 1.5, tint=(0.35, 0.45, 0.4)))
    k.cube("DumpLid", (1.45, 0.85, 0.05), (1.9, wy + 0.45, 1.03), metal)
    k.cardboard_box((-1.4, wy + 0.4, 0.15), rot_z=20)
    # purple LED strip along the wall base and a cold blue window glow high on the side wall
    k.led_strip([(-2.0, wy + 0.03, 0.04), (2.5, wy + 0.03, 0.04)], color=(0.5, 0.1, 1.0), strength=12)
    print("wall_y", round(wy, 3))

def stage_camera():
    sc = bpy.context.scene
    if not sc.camera:
        cd = bpy.data.cameras.new("Cam"); c = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(c); sc.camera = c
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1350
    print(k.frame_head(0.26, head_xy=(0.56, 0.32), view_dir=(-0.25, 1, -0.32), lens=32, roll=-5))
    # slide the sign (and its backing) along the wall until it sits upper-right of the head in frame
    sg = [o for o in sc.objects if o.name.startswith(("Neon", "SignBack"))]
    for _ in range(8):
        x, y, _d = k.project(bpy.data.objects["SignBack"].location)
        for o in sg:
            o.location.x += (x - 0.8) * 1.2; o.location.z += (y - 0.075) * 1.2
        k.upd()
    for n, p in (("handN", k.arm().matrix_world @ k.arm().pose.bones["Hand.P"].tail), ("sign", bpy.data.objects["SignBack"].location)):
        print(n, [round(v, 2) for v in k.project(p)])
    k.show_camera("SOLID")

def stage_light():
    sc = bpy.context.scene; H = k.head_center()
    for o in [o for o in sc.objects if o.type == "LIGHT"]: bpy.data.objects.remove(o, do_unlink=True)
    # warm sodium streetlamp key: screen-left, in front, high
    k.area("Key", H + Vector((1.6, 1.4, 1.6)), H, 170, 0.6, (1.0, 0.72, 0.38), 120)
    # purple neon rim from behind-right and behind-left (wall side)
    k.area("RimR", H + Vector((-0.9, -0.25, 0.5)), H, 45, 0.4, (0.55, 0.15, 1.0))
    k.area("RimL", H + Vector((0.8, -0.2, 0.45)), H, 14, 0.3, (0.45, 0.2, 1.0))
    # teal bounce off the wet ground
    k.area("Fill", H + Vector((-0.4, 1.6, -1.1)), H, 18, 2.0, (0.2, 0.75, 0.8))
    # sign glow spill on the wall
    sb = bpy.data.objects["SignBack"].location
    k.area("SignSpill", sb + Vector((0, 0.35, -0.05)), sb + Vector((0, 0, -0.6)), 6, 1.0, (0.55, 0.15, 1.0))
    k.world((0.006, 0.008, 0.014), 1.0, haze=0.02)

def stage_fx():
    """Rain streaks as one mesh, none near the lens; a puddle sheen stays from the glossy ground."""
    for o in [o for o in bpy.data.objects if o.name.startswith("Rain")]: bpy.data.objects.remove(o, do_unlink=True)
    cam = bpy.context.scene.camera.location; rnd = random.Random(7)
    bm = bmesh.new()
    for _ in range(2200):
        p = Vector((rnd.uniform(-2.5, 2.5), rnd.uniform(-0.3, 2.6), rnd.uniform(0, 3.2)))
        if (p - cam).length < 1.3: continue
        L = rnd.uniform(0.12, 0.25); w = 0.0011
        d = Vector((0.03, 0.0, -L))
        vs = [bm.verts.new(p + Vector((-w, 0, 0))), bm.verts.new(p + Vector((w, 0, 0))),
              bm.verts.new(p + d + Vector((w, 0, 0))), bm.verts.new(p + d + Vector((-w, 0, 0)))]
        bm.faces.new(vs)
    me = bpy.data.meshes.new("Rain"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Rain", me); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(k.material("RainMat", (0.8, 0.85, 1.0), 0.1, emit=(0.6, 0.7, 1.0), strength=0.25, alpha=0.25))

def stage_render(name="cy1", pct=50, samples=48, exposure=0.0):
    k.setup_cycles(samples, "AgX - Punchy", exposure, dof_fstop=2.8)
    sc = bpy.context.scene; sc.cycles.volume_step_rate = 4
    k.render(OUT + "\\" + name + ".png", pct, samples)

def stage_hair(mul=0.3):
    """Keep the black hair black under the purple rim: multiply its texture down, less specular."""
    m = bpy.data.materials["Handle2Mtl"]; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    if "HairDark" not in nt.nodes:
        src = b.inputs["Base Color"].links[0].from_socket
        mix = nt.nodes.new("ShaderNodeMix"); mix.name = "HairDark"; mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1
        nt.links.new(src, mix.inputs[6]); nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    nt.nodes["HairDark"].inputs[7].default_value = (mul, mul, mul, 1)
    b.inputs["Specular IOR Level"].default_value = 0.2
