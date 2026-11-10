"""Props shared by the Halloween GFX scenes (style_pumpkin.py, style_lantern.py). Import after gfx_kit."""
import math, random
import bpy, bmesh
from mathutils import Vector

import gfx_kit as k


def emissive(name, color, strength, alpha=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    b.inputs["Emission Color"].default_value = (*color, 1); b.inputs["Emission Strength"].default_value = strength
    if alpha is not None:
        b.inputs["Alpha"].default_value = alpha
    return m


def keep_only_avatar():
    """Delete everything except the avatar (and its camera): the base stage leaves Backdrop/Halo/etc. behind."""
    a = k.arm(); keep = {a} | set(a.children_recursive)
    for o in list(bpy.context.scene.objects):
        if o not in keep and o.type != "CAMERA":
            bpy.data.objects.remove(o, do_unlink=True)


_FACE = {
    "eyes": [[(-0.46, 0.14), (-0.14, 0.14), (-0.30, 0.42)], [(0.14, 0.14), (0.46, 0.14), (0.30, 0.42)]],
    "mouth": [[(-0.55, -0.08), (-0.32, -0.22), (-0.18, -0.06), (0.0, -0.24), (0.18, -0.06), (0.32, -0.22), (0.55, -0.08),
               (0.42, -0.42), (0.2, -0.34), (0.0, -0.5), (-0.2, -0.34), (-0.42, -0.42)]],
}


def pumpkin(name, loc, r, rot_z=0.0, glow=(1.0, 0.32, 0.04), strength=45.0, light=70.0, face=True, skin=(0.5, 0.12, 0.01)):
    """Ribbed pumpkin whose face (+Y local) is emissive; a point light sits in front of the face. rot_z turns it."""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=1.0)
    for v in bm.verts:
        phi = math.atan2(v.co.y, v.co.x)
        f = 1 + 0.045 * math.cos(10 * (phi - math.pi / 2)) * (1 - abs(v.co.z) ** 3)
        v.co.x *= f * r; v.co.y *= f * r; v.co.z *= 0.82 * r
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    for p in me.polygons:
        p.use_smooth = True
    sm = bpy.data.materials.new(name + "_skin"); sm.use_nodes = True; b = sm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*skin, 1); b.inputs["Roughness"].default_value = 0.55
    o.data.materials.append(sm)
    parts = [o]
    stem = bpy.data.objects.new(name + "_stem", None)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.09 * r, radius2=0.05 * r, depth=0.34 * r, location=(0, 0, 0.82 * r + 0.1 * r))
    st = bpy.context.active_object; st.name = name + "_stem"
    st.data.materials.append(k.material(name + "_stemm", (0.12, 0.16, 0.04), 0.8)); parts.append(st)
    if face:
        gm = emissive(name + "_glow", glow, strength)
        for part in ("eyes", "mouth"):
            for poly in _FACE[part]:
                vs = []
                for (u, v) in poly:
                    d = math.sqrt(max(0.06, 1 - u * u - v * v))
                    vs.append((u * r * 0.98, r * d * 1.0 + 0.004, v * r * 0.82 * 1.0))
                fm = bpy.data.meshes.new(name + "_f"); fm.from_pydata(vs, [], [list(range(len(vs)))])
                fo = bpy.data.objects.new(name + "_f", fm); bpy.context.scene.collection.objects.link(fo)
                fo.data.materials.append(gm); fo.visible_shadow = False; parts.append(fo)
        ld = bpy.data.lights.new(name + "_L", "POINT"); ld.energy = light * 0.9 * (r / 0.2) ** 2; ld.color = glow; ld.shadow_soft_size = r * 0.3
        lo = bpy.data.objects.new(name + "_L", ld); bpy.context.scene.collection.objects.link(lo); lo.location = (0, r * 1.5, 0.0)
        parts.append(lo)
    root = bpy.data.objects.new(name + "_root", None); bpy.context.scene.collection.objects.link(root)
    root.location = loc; root.rotation_euler = (0, 0, math.radians(rot_z))
    for p in parts:
        p.parent = root
        if p.type == "MESH" and p.name.endswith("_stem") and p.parent is root:
            pass
    return root


def moon(loc, radius, tint=(0.35, 0.65, 0.8)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=64, ring_count=32)
    m = bpy.context.active_object; m.name = "Moon"; m.visible_shadow = False
    mt = bpy.data.materials.new("MoonM"); mt.use_nodes = True; nt = mt.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL": nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 2.2
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.5; nz.inputs["Detail"].default_value = 8
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (*tint, 1); ramp.color_ramp.elements[1].color = (0.95, 0.98, 1, 1)
    ramp.color_ramp.elements[0].position = 0.38; ramp.color_ramp.elements[1].position = 0.62
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"]); nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    m.data.materials.append(mt); return m


def stars(n=250, radius=70, seed=3):
    rnd = random.Random(seed); sm = emissive("StarM", (1, 1, 1), 12)
    for i in range(n):
        az = rnd.uniform(math.radians(200), math.radians(340)); el = rnd.uniform(math.radians(8), math.radians(70))
        p = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * radius
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rnd.uniform(0.05, 0.16), location=p)
        s = bpy.context.active_object; s.name = "Star"; s.data.materials.append(sm); s.visible_shadow = False


def leaves(n, center, spread, seed=5, colors=((1, 0.4, 0.05), (0.9, 0.2, 0.02), (1, 0.6, 0.1)), size=(0.05, 0.12), strength=1.5, ground=None):
    rnd = random.Random(seed); mats = [emissive("LeafM%d" % i, c, strength) for i, c in enumerate(colors)]
    for i in range(n):
        p = Vector(center) + Vector((rnd.uniform(-1, 1) * spread[0], rnd.uniform(-1, 1) * spread[1], rnd.uniform(-1, 1) * spread[2]))
        if ground is not None:
            p.z = ground
        bpy.ops.mesh.primitive_circle_add(vertices=5, radius=rnd.uniform(*size), fill_type="NGON", location=p)
        o = bpy.context.active_object; o.name = "Leaf"; o.scale = (1, rnd.uniform(0.5, 1), 1)
        o.rotation_euler = (rnd.uniform(0, 3.14), rnd.uniform(0, 3.14), rnd.uniform(0, 3.14)); o.data.materials.append(rnd.choice(mats))
        o.visible_shadow = False


def embers(n, center, spread, seed=9, color=(1, 0.5, 0.1), size=(0.006, 0.016), strength=40):
    rnd = random.Random(seed); em = emissive("EmberM", color, strength)
    for i in range(n):
        p = Vector(center) + Vector((rnd.uniform(-1, 1) * spread[0], rnd.uniform(-1, 1) * spread[1], rnd.uniform(-1, 1) * spread[2]))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rnd.uniform(*size), location=p)
        o = bpy.context.active_object; o.name = "Ember"; o.data.materials.append(em); o.visible_shadow = False


def bare_tree(x, y, h, r, mat, rnd):
    def branch(base, d, L, r0):
        bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=r0, radius2=r0 * 0.25, depth=L)
        b = bpy.context.active_object; b.name = "Tree_b"; d = Vector(d).normalized(); b.location = base + d * L / 2
        b.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); b.data.materials.append(mat); return b
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=r, radius2=r * 0.3, depth=h, location=(x, y, h / 2))
    t = bpy.context.active_object; t.name = "Tree"; t.data.materials.append(mat)
    for _ in range(rnd.randint(5, 8)):
        z = rnd.uniform(h * 0.3, h * 0.95); a = rnd.uniform(0, math.tau); tilt = rnd.uniform(0.9, 1.3)
        d = (math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), math.cos(tilt)); L = rnd.uniform(1.0, 2.6) * (1.3 - z / h * 0.6)
        b = branch(Vector((x, y, z)), d, L, r * 0.28)
        if rnd.random() < 0.7:
            branch(b.location + Vector(d) * L / 2, (d[0] + rnd.uniform(-.6, .6), d[1] + rnd.uniform(-.6, .6), d[2] + .4), L * 0.5, r * 0.1)


def fog(name, loc, size, density, color=(0.75, 0.82, 0.95), aniso=0.3, noise=None, fade_height=False):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); f = bpy.context.active_object; f.name = name; f.scale = size
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL": nt.nodes.remove(n)
    pv = nt.nodes.new("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (*color, 1)
    pv.inputs["Density"].default_value = density; pv.inputs["Anisotropy"].default_value = aniso
    if noise:
        tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = noise
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.35; mr.inputs[2].default_value = 0.75
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
        last = mr.outputs[0]
        if fade_height:
            sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sp.inputs[0])
            inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0; nt.links.new(sp.outputs["Z"], inv.inputs[1])
            pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 3.0; nt.links.new(inv.outputs[0], pw.inputs[0])
            m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; nt.links.new(last, m2.inputs[0]); nt.links.new(pw.outputs[0], m2.inputs[1]); last = m2.outputs[0]
        mu = nt.nodes.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; mu.inputs[1].default_value = density
        nt.links.new(last, mu.inputs[0]); nt.links.new(mu.outputs[0], pv.inputs["Density"])
    nt.links.new(pv.outputs[0], nt.nodes["Material Output"].inputs["Volume"]); f.data.materials.append(m); f.visible_shadow = False
    return f


def solid(name, kind, loc, scale, mat, rot=(0, 0, 0), bevel=0.0):
    getattr(bpy.ops.mesh, "primitive_%s_add" % kind)(location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); o.rotation_euler = rot
    if bevel:
        bv = o.modifiers.new("b", "BEVEL"); bv.width = bevel; bv.segments = 2
    o.data.materials.append(mat); return o
