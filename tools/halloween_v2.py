"""v2 set pieces from docs/GFX_MASTER_PIPELINE.md section 4/5: carved hollow pumpkins, beveled tombstones,
gnarled skin-modifier trees, maple leaf cards, displaced ground, wisps, avatar materials, lint gate."""
import math, os, random
import bpy, bmesh
from mathutils import Vector

import gfx_kit as k
from halloween_kit import emissive, moon, _FACE

LEAF_PNG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library", "textures", "leaf_cards", "maple.png")


def _inside(pt, poly):
    x, y = pt; c = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1:
            c = not c
    return c


JACK_FACE = [  # classic jack-o'-lantern: triangle eyes, triangle nose, toothy grin (x, z on the unit front hemisphere)
    [(-0.52, 0.10), (-0.14, 0.10), (-0.36, 0.46)], [(0.14, 0.10), (0.52, 0.10), (0.36, 0.46)],
    [(-0.1, -0.06), (0.1, -0.06), (0.0, 0.1)],
    [(-0.64, -0.08), (-0.44, -0.18), (-0.32, -0.18), (-0.32, -0.29), (-0.18, -0.29), (-0.18, -0.21), (0.18, -0.21),
     (0.18, -0.29), (0.32, -0.29), (0.32, -0.18), (0.44, -0.18), (0.64, -0.08), (0.5, -0.38), (0.13, -0.5), (0.13, -0.37),
     (-0.05, -0.37), (-0.05, -0.51), (-0.5, -0.4)],
]


def carved_pumpkin(name, loc, r, rot_z=0.0, light=12.0, glow=(1.0, 0.42, 0.05), face="classic", rib=0.05, res=96, squash=0.82):
    """Hollow ribbed shell; face holes are deleted faces (no boolean), Solidify gives a real wall, flesh inside glows,
    a point light at the centre so light only leaves through the holes. Face points to local +Y. face='jack' = nose+teeth."""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=res, v_segments=res // 2, radius=1.0)
    for v in bm.verts:
        phi = math.atan2(v.co.y, v.co.x)
        rr = 0.5 + 0.5 * math.cos(10 * (phi - math.pi / 2)); f = 1 - rib + rib * 2 * rr ** 0.4 * (1 - abs(v.co.z) ** 3) if face == "jack" else \
            1 + rib * math.cos(10 * (phi - math.pi / 2)) * (1 - abs(v.co.z) ** 3)
        v.co.x *= f; v.co.y *= f; v.co.z *= squash
        if face == "jack" and v.co.z > 0.6 * squash:  # dimple at the stem
            v.co.z -= 0.12 * (v.co.z / squash - 0.6) / 0.4 * squash
    holes = [[(x * 1.18, z * 1.12) for x, z in pl] for pl in JACK_FACE] if face == "jack" else (_FACE["eyes"] + _FACE["mouth"]) if face else []
    dead = [fc for fc in bm.faces if fc.calc_center_median().y > 0.3
            and any(_inside((fc.calc_center_median().x, fc.calc_center_median().z / squash), p) for p in holes)]
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    if face == "jack":  # snap hole-boundary verts onto the outline so carved edges are straight, not stair-stepped
        segs = [(p[i], p[(i + 1) % len(p)]) for p in holes for i in range(len(p))]
        for v in bm.verts:
            if v.is_boundary and v.co.y > 0.3:
                px, pz = v.co.x, v.co.z / squash; best = None
                for (ax, az), (bx, bz) in segs:
                    dx, dz = bx - ax, bz - az; t = max(0, min(1, ((px - ax) * dx + (pz - az) * dz) / (dx * dx + dz * dz + 1e-9)))
                    qx, qz = ax + dx * t, az + dz * t; d = (qx - px) ** 2 + (qz - pz) ** 2
                    if best is None or d < best[0]:
                        best = (d, qx, qz)
                if best[0] < 0.004:
                    v.co.x, v.co.z = best[1], best[2] * squash
    for v in bm.verts:
        v.co *= r
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    for p in me.polygons:
        p.use_smooth = True
    skin = bpy.data.materials.new(name + "_skin"); skin.use_nodes = True; b = skin.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.6, 0.3, 0.035, 1) if face == "jack" else (0.5, 0.12, 0.01, 1); b.inputs["Roughness"].default_value = 0.5
    b.inputs["Subsurface Weight"].default_value = 0.12 if face == "jack" else 0.3; b.inputs["Subsurface Radius"].default_value = (1, 0.3, 0.1)
    b.inputs["Subsurface Scale"].default_value = 0.02 * r
    if face == "jack":  # blotchy skin + fine bump so it is not plastic
        snt = skin.node_tree; nz = snt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60; nz.inputs["Detail"].default_value = 10
        bp = snt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15; snt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
        snt.links.new(bp.outputs["Normal"], b.inputs["Normal"]); b.inputs["Roughness"].default_value = 0.7
        b.inputs["Base Color"].default_value = (0.72, 0.26, 0.012, 1); b.inputs["Subsurface Weight"].default_value = 0.05
        b.inputs["Specular IOR Level"].default_value = 0.3; bp.inputs["Strength"].default_value = 0.35
        tc = snt.nodes.new("ShaderNodeTexCoord"); vo = snt.nodes.new("ShaderNodeTexNoise"); vo.inputs["Scale"].default_value = 4
        snt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
        mx = snt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs[6].default_value = (0.72, 0.26, 0.012, 1)
        mx.inputs[7].default_value = (0.45, 0.13, 0.008, 1); snt.links.new(vo.outputs["Fac"], mx.inputs["Factor"])
        snt.links.new(mx.outputs[2], b.inputs["Base Color"])
        glow = (1.0, 0.33, 0.02)
    flesh = bpy.data.materials.new(name + "_flesh"); flesh.use_nodes = True; fb = flesh.node_tree.nodes["Principled BSDF"]
    fb.inputs["Base Color"].default_value = (1.0, 0.45, 0.08, 1); fb.inputs["Emission Color"].default_value = (*glow, 1)
    fb.inputs["Emission Strength"].default_value = 1.4 if face == "jack" else 3.0
    o.data.materials.append(skin); o.data.materials.append(flesh)
    so = o.modifiers.new("wall", "SOLIDIFY"); so.thickness = 0.07 * r; so.offset = -1; so.use_even_offset = True
    so.use_rim = True; so.material_offset = 1; so.material_offset_rim = 1
    if face == "jack":
        bv = o.modifiers.new("rim", "BEVEL"); bv.width = 0.012 * r; bv.segments = 2; bv.limit_method = "ANGLE"
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.1 * r, radius2=0.06 * r, depth=0.38 * r, location=(0.02 * r, 0, 0.96 * r))
    st = bpy.context.active_object; st.name = name + "_stem"; st.rotation_euler = (0.25, 0.1, 0)
    st.data.materials.append(k.material(name + "_stemm", (0.1, 0.12, 0.04), 0.8))
    ld = bpy.data.lights.new(name + "_L", "POINT"); ld.energy = light; ld.color = glow; ld.shadow_soft_size = 0.2 * r
    lo = bpy.data.objects.new(name + "_L", ld); bpy.context.scene.collection.objects.link(lo)
    root = bpy.data.objects.new(name + "_root", None); bpy.context.scene.collection.objects.link(root)
    for p in (o, st, lo):
        p.parent = root
    root.location = loc; root.rotation_euler = (0, 0, math.radians(rot_z))
    return root


def stone_mat(tint=(0.42, 0.42, 0.5)):
    m = k.pbr("gravel_embedded_concrete", 1.3, tint=tint)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 40; nz.inputs["Detail"].default_value = 8
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def weathered_stone(tint=(0.42, 0.44, 0.5), moss=(0.06, 0.09, 0.03), pits=0.6, moss_amt=0.45):
    """stone_mat + voronoi pits (bump) + a noise moss mask that favours up-facing / low areas."""
    m = stone_mat(tint); nt = m.node_tree; b = nt.nodes["Principled BSDF"]; L = nt.links.new
    base = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].links else None
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 18; L(tc.outputs["Object"], vo.inputs["Vector"])
    pr = nt.nodes.new("ShaderNodeMapRange"); pr.inputs[1].default_value = 0.0; pr.inputs[2].default_value = 0.18
    L(vo.outputs["Distance"], pr.inputs["Value"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6; nz.inputs["Detail"].default_value = 10
    L(tc.outputs["Object"], nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 1 - moss_amt; mr.inputs[2].default_value = 1 - moss_amt + 0.15
    L(nz.outputs["Fac"], mr.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.inputs[7].default_value = (*moss, 1)
    L(mr.outputs[0], mix.inputs["Factor"])
    if base:
        L(base, mix.inputs[6])
    else:
        mix.inputs[6].default_value = (*tint, 1)
    pit = nt.nodes.new("ShaderNodeMix"); pit.data_type = "RGBA"; pit.blend_type = "MULTIPLY"; pit.inputs[7].default_value = (0.25, 0.25, 0.28, 1)
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1; L(pr.outputs[0], inv.inputs[1])
    L(inv.outputs[0], pit.inputs["Factor"]); L(mix.outputs[2], pit.inputs[6]); L(pit.outputs[2], b.inputs["Base Color"])
    bp2 = nt.nodes.new("ShaderNodeBump"); bp2.inputs["Strength"].default_value = pits; bp2.inputs["Distance"].default_value = 0.02
    L(pr.outputs[0], bp2.inputs["Height"])
    old = b.inputs["Normal"].links[0].from_socket if b.inputs["Normal"].links else None
    if old:
        L(old, bp2.inputs["Normal"])
    L(bp2.outputs["Normal"], b.inputs["Normal"])
    return m


def cobble_mat(scale=5.0, tint=(0.2, 0.22, 0.27)):
    """Procedural cobblestones: voronoi cells = stones, distance-to-edge = dark mortar gaps + bump."""
    m = bpy.data.materials.new("Cobble"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]; L = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ed = nt.nodes.new("ShaderNodeTexVoronoi"); ed.feature = "DISTANCE_TO_EDGE"; ed.inputs["Scale"].default_value = scale
    ed.inputs["Randomness"].default_value = 0.85; L(tc.outputs["Object"], ed.inputs["Vector"])
    vc = nt.nodes.new("ShaderNodeTexVoronoi"); vc.inputs["Scale"].default_value = scale; vc.inputs["Randomness"].default_value = 0.85
    L(tc.outputs["Object"], vc.inputs["Vector"])
    gap = nt.nodes.new("ShaderNodeMapRange"); gap.inputs[1].default_value = 0.0; gap.inputs[2].default_value = 0.12
    L(ed.outputs["Distance"], gap.inputs["Value"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30; nz.inputs["Detail"].default_value = 8
    L(tc.outputs["Object"], nz.inputs["Vector"])
    hue = nt.nodes.new("ShaderNodeMix"); hue.data_type = "RGBA"; hue.blend_type = "MULTIPLY"; hue.inputs["Factor"].default_value = 1
    hue.inputs[7].default_value = (*tint, 1); L(vc.outputs["Color"], hue.inputs[6])
    sat = nt.nodes.new("ShaderNodeMix"); sat.data_type = "RGBA"; sat.inputs["Factor"].default_value = 0.65
    sat.inputs[7].default_value = (*tint, 1); L(hue.outputs[2], sat.inputs[6])
    dirt = nt.nodes.new("ShaderNodeMix"); dirt.data_type = "RGBA"; dirt.blend_type = "MULTIPLY"; dirt.inputs[7].default_value = (0.4, 0.4, 0.42, 1)
    L(nz.outputs["Fac"], dirt.inputs["Factor"]); L(sat.outputs[2], dirt.inputs[6])
    gm = nt.nodes.new("ShaderNodeMix"); gm.data_type = "RGBA"; gm.inputs[6].default_value = (0.012, 0.012, 0.016, 1)
    L(gap.outputs[0], gm.inputs["Factor"]); L(dirt.outputs[2], gm.inputs[7]); L(gm.outputs[2], b.inputs["Base Color"])
    hs = nt.nodes.new("ShaderNodeMath"); hs.operation = "MULTIPLY_ADD"; hs.inputs[1].default_value = 0.15
    L(nz.outputs["Fac"], hs.inputs[0]); L(gap.outputs[0], hs.inputs[2])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.8; bp.inputs["Distance"].default_value = 0.03
    L(hs.outputs[0], bp.inputs["Height"]); L(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.8
    return m


def tombstone(name, loc, w=0.5, h=0.9, d=0.14, style="round", tilt=(0, 0), rot_z=0.0, mat=None):
    """Beveled headstone with a rounded (or pointed) top, slight tilt, sunk 0.03 m into the ground. Faces +Y."""
    body_h = h - (w / 2 if style == "round" else w * 0.4)
    bm = bmesh.new(); prof = []
    prof += [(-w / 2, 0), (w / 2, 0), (w / 2, body_h)]
    if style == "round":
        for i in range(1, 16):
            a = i / 16 * math.pi; prof.append((w / 2 * math.cos(a), body_h + w / 2 * math.sin(a)))
    else:
        prof.append((0, h))
    prof.append((-w / 2, body_h))
    front = [bm.verts.new((x, d / 2, z)) for x, z in prof]; back = [bm.verts.new((x, -d / 2, z)) for x, z in prof]
    bm.faces.new(front); bm.faces.new(list(reversed(back)))
    n = len(prof)
    for i in range(n):
        j = (i + 1) % n; bm.faces.new((front[j], front[i], back[i], back[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.location = (loc[0], loc[1], loc[2] - 0.03); o.rotation_euler = (math.radians(tilt[0]), math.radians(tilt[1]), math.radians(rot_z))
    bv = o.modifiers.new("bevel", "BEVEL"); bv.width = 0.015; bv.segments = 3; bv.limit_method = "ANGLE"
    o.modifiers.new("wn", "WEIGHTED_NORMAL")
    o.data.materials.append(mat or stone_mat()); return o


def gnarled_tree(loc, h, seed, mat, depth=3, roots=5):
    """Branch skeleton (verts+edges) -> Skin modifier -> Subsurf 1 -> noise displace. Roots spread into the ground."""
    rnd = random.Random(seed); verts = [Vector((0, 0, 0))]; rad = [h * 0.035]; edges = []

    def grow(i0, d, L, r, lvl):
        idx = i0; cur = verts[i0].copy(); dd = Vector(d).normalized(); seg = 5
        for s in range(seg):
            dd = (dd + Vector((rnd.uniform(-.35, .35), rnd.uniform(-.35, .35), rnd.uniform(-.12, .2)))).normalized()
            cur = cur + dd * (L / seg); verts.append(cur.copy()); rr = max(r * (1 - 0.16 * (s + 1)), 0.005); rad.append(rr)
            edges.append((idx, len(verts) - 1)); idx = len(verts) - 1
            if lvl < depth and s >= 1 and rnd.random() < 0.55:
                a = rnd.uniform(0, math.tau); grow(idx, (math.cos(a), math.sin(a), rnd.uniform(0.2, 0.9)), L * rnd.uniform(0.45, 0.7), rr * 0.6, lvl + 1)
    grow(0, (0, 0, 1), h, h * 0.035, 0)
    for i in range(roots):
        a = i / roots * math.tau + rnd.uniform(-.3, .3)
        verts.append(Vector((math.cos(a) * h * 0.13, math.sin(a) * h * 0.13, -0.05))); rad.append(h * 0.007); edges.append((0, len(verts) - 1))
    me = bpy.data.meshes.new("Tree"); me.from_pydata([tuple(v) for v in verts], edges, [])
    o = bpy.data.objects.new("Tree", me); bpy.context.scene.collection.objects.link(o); o.location = loc
    o.modifiers.new("skin", "SKIN")
    for i, sv in enumerate(me.skin_vertices[0].data):
        sv.radius = (rad[i], rad[i])
    me.skin_vertices[0].data[0].use_root = True
    ss = o.modifiers.new("ss", "SUBSURF"); ss.levels = ss.render_levels = 1
    tx = bpy.data.textures.new("bark_n", "CLOUDS"); tx.noise_scale = 0.15
    dp = o.modifiers.new("disp", "DISPLACE"); dp.texture = tx; dp.strength = 0.02
    o.data.materials.append(mat)
    return o


def bark_mat(tint=(0.2, 0.14, 0.11)):
    return k.pbr("wood_cabinet_worn_long", 2.0, tint=tint)


def leaf_mat(name, color):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(LEAF_PNG, check_existing=True)
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 1
    mix.inputs[7].default_value = (*color, 1)
    nt.links.new(t.outputs["Color"], mix.inputs[6]); nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"]); b.inputs["Roughness"].default_value = 0.8
    return m


LEAF_COLORS = ((0.75, 0.16, 0.02), (0.9, 0.42, 0.03), (0.7, 0.5, 0.05), (0.45, 0.08, 0.02))


def leaf_card(name, loc, size, rot, mat, rnd):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=6, y_subdivisions=6, size=size, location=loc)
    o = bpy.context.active_object; o.name = name; o.rotation_euler = rot
    bd = o.modifiers.new("curl", "SIMPLE_DEFORM"); bd.deform_method = "BEND"; bd.angle = rnd.uniform(0.3, 0.9); bd.deform_axis = "X"
    o.data.materials.append(mat); o.visible_shadow = False; return o


def leaf_cards(n, center, spread, seed=1, size=(0.06, 0.12), ground=None):
    rnd = random.Random(seed); mats = [leaf_mat("Leaf%d" % i, c) for i, c in enumerate(LEAF_COLORS)]
    for i in range(n):
        p = Vector(center) + Vector((rnd.uniform(-1, 1) * spread[0], rnd.uniform(-1, 1) * spread[1], rnd.uniform(-1, 1) * spread[2]))
        rot = (rnd.uniform(0, 3.1), rnd.uniform(0, 3.1), rnd.uniform(0, 6.2))
        if ground is not None:
            p.z = ground + rnd.uniform(0.004, 0.015); rot = (rnd.uniform(-.2, .2), rnd.uniform(-.2, .2), rnd.uniform(0, 6.2))
        leaf_card("LeafCard", p, rnd.uniform(*size), rot, rnd.choice(mats), rnd)


def hero_leaves(cam, n=4, seed=2, dist=(0.3, 0.55)):
    """3-5 leaves just in front of the lens near the frame edges: out of focus, they read as foreground bokeh."""
    rnd = random.Random(seed); mats = [leaf_mat("HeroLeaf%d" % i, c) for i, c in enumerate(LEAF_COLORS)]
    q = cam.matrix_world.to_quaternion(); fwd = q @ Vector((0, 0, -1)); right = q @ Vector((1, 0, 0)); up = q @ Vector((0, 1, 0))
    spots = [(-0.4, 0.36), (0.42, -0.38), (-0.38, -0.4), (0.42, 0.34), (0.0, -0.46)]
    for i in range(n):
        d = rnd.uniform(*dist); sx, sy = spots[i % len(spots)]
        p = cam.location + fwd * d + right * sx * d * 0.85 + up * sy * d * 0.85
        leaf_card("HeroLeaf", p, rnd.uniform(0.05, 0.08), (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 6)), rnd.choice(mats), rnd)


def ground(size=40, tex="brown_mud_leaves_01", tint=(0.4, 0.34, 0.45), disp=0.05):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=200, y_subdivisions=200, size=size)
    g = bpy.context.active_object; g.name = "Ground"
    tx = bpy.data.textures.new("gnd", "CLOUDS"); tx.noise_scale = 0.6
    dp = g.modifiers.new("d", "DISPLACE"); dp.texture = tx; dp.strength = disp; dp.mid_level = 0.7
    g.data.materials.append(k.pbr(tex, 0.5, tint=tint)); return g


def wisps(n, center, spread, color=(0.62, 0.0, 1.0), strength=4.0, seed=8):
    rnd = random.Random(seed); m = emissive("WispM", color, strength)
    for i in range(n):
        p = Vector(center) + Vector((rnd.uniform(-1, 1) * spread[0], rnd.uniform(-1, 1) * spread[1], rnd.uniform(-1, 1) * spread[2]))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=rnd.uniform(0.012, 0.03), location=p, segments=12, ring_count=8)
        o = bpy.context.active_object; o.name = "Wisp"; o.data.materials.append(m); o.visible_shadow = False


def avatar_materials():
    """Section 5: per-role Principled settings (Blender 5.2 names); SSS 0 so the face decal stays crisp."""
    a = k.arm(); head = k.head_obj(); done = set()
    for o in a.children_recursive:
        if o.type != "MESH":
            continue
        role = "skin" if o == head else ("hair" if o.parent_bone == "Head" else "cloth")
        for s in o.material_slots:
            m = s.material
            if not m or m.name in done or not m.use_nodes or not m.node_tree.nodes.get("Principled BSDF"):
                continue
            done.add(m.name); b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Specular IOR Level"].default_value = 0.4; b.inputs["Subsurface Weight"].default_value = 0.0
            if role == "skin":
                b.inputs["Roughness"].default_value = 0.45
            elif role == "hair":
                b.inputs["Roughness"].default_value = 0.35; b.inputs["Coat Weight"].default_value = 0.15; b.inputs["Coat Roughness"].default_value = 0.2
            else:
                b.inputs["Roughness"].default_value = 0.7; b.inputs["Sheen Weight"].default_value = 0.15
                b.inputs["Sheen Roughness"].default_value = 0.5; b.inputs["Sheen Tint"].default_value = (0.75, 0.6, 1.0, 1)


def lint(prefixes=("Pumpkin", "Tomb", "Tree", "Lantern", "HeroLeaf")):
    """Gate helper: stray untextured meshes and props that sit between the lens and the face. Returns problem count."""
    bad = 0; scn = bpy.context.scene; a = k.arm(); keep = set(a.children_recursive) | {a}
    for o in scn.objects:
        if o.type == "MESH" and o not in keep and not o.parent and not any(o.data.materials):
            print("LINT stray mesh:", o.name); bad += 1
    H = k.head_center(); hx, hy, _ = k.project(H); hw = k.measure()["head_frac"] / 2; dh = (H - scn.camera.location).length
    for o in scn.objects:
        if o not in keep and o.name.startswith(prefixes) and o.type in ("MESH", "EMPTY"):
            p = o.matrix_world.translation; x, y, z = k.project(p)
            if z > 0 and abs(x - hx) < hw * 0.8 and abs(y - hy) < hw * 0.8 and (p - scn.camera.location).length < dh:
                print("LINT covers face:", o.name); bad += 1
    print("LINT problems:", bad); return bad
