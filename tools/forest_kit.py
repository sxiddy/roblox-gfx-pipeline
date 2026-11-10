"""Real-asset forest dressing: Poly Haven glTF models instanced (linked copies) at real heights, plus avatar material
polish. Used by style_spirits.py."""
import math
import bpy
from mathutils import Vector
import gfx_kit as k

_cache = {}


def _bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    return Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))), \
        Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))


def _source(category, name):
    """Import once, park the hierarchy hidden at the origin; returns (root, native height)."""
    if name not in _cache:
        roots = k.import_model(category, name); bpy.context.view_layer.update()
        if len(roots) > 1:
            e = bpy.data.objects.new(name + "_src", None); bpy.context.scene.collection.objects.link(e)
            for r in roots:
                r.parent = e
            root = e
        else:
            root = roots[0]
        bpy.context.view_layer.update()
        objs = [root] + list(root.children_recursive); lo, hi = _bbox(objs)
        root.location -= Vector((0, 0, lo.z))
        _cache[name] = (root, hi.z - lo.z)
        for o in objs:
            o.hide_render = True; o.hide_viewport = True
    return _cache[name]


def place(category, name, loc, height=None, scale=None, rot_z=0.0, tilt=(0, 0)):
    """Linked copy of a library model standing on loc (z = ground), scaled to `height` metres (or by `scale`)."""
    src, h = _source(category, name)
    s = (height / h) if height else (scale or 1.0)
    def dup(o, parent):
        c = o.copy(); bpy.context.scene.collection.objects.link(c); c.hide_render = c.hide_viewport = False
        c.parent = parent
        for ch in o.children:
            dup(ch, c)
        return c
    r = dup(src, None)
    r.location = Vector((loc[0], loc[1], loc[2] + src.location.z * s))  # src.location.z lifts the base to z=0
    r.scale = Vector(src.scale) * s
    r.rotation_euler = (math.radians(tilt[0]), math.radians(tilt[1]), math.radians(rot_z))
    return r


def tint_model(root, mul, rough=None):
    """Multiply every material colour under root (shared materials: call once per model)."""
    seen = set()
    for o in [root] + list(root.children_recursive):
        for sl in getattr(o, "material_slots", []):
            m = sl.material
            if not m or m.name in seen or not m.use_nodes:
                continue
            seen.add(m.name); b = m.node_tree.nodes.get("Principled BSDF")
            if not b:
                continue
            src = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].links else None
            mix = m.node_tree.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1; mix.inputs[7].default_value = (*mul, 1)
            if src:
                m.node_tree.links.new(src, mix.inputs[6])
            else:
                mix.inputs[6].default_value = b.inputs["Base Color"].default_value
            m.node_tree.links.new(mix.outputs[2], b.inputs["Base Color"])
            if rough is not None and not b.inputs["Roughness"].links:
                b.inputs["Roughness"].default_value = rough


def avatar_polish(hair_value=0.72):
    """Character pass: neutral cloth sheen, hair darkened a touch so the white doesn't clip, soft hair coat,
    linear-filtered textures (the 2x upscaled maps)."""
    a = k.arm(); head = k.head_obj(); done = set()
    for o in a.children_recursive:
        if o.type != "MESH":
            continue
        hair = o.parent_bone == "Head" and o != head
        for sl in o.material_slots:
            m = sl.material
            if not m or m.name in done or not m.use_nodes:
                continue
            done.add(m.name); nt = m.node_tree; b = nt.nodes.get("Principled BSDF")
            if not b:
                continue
            for n in nt.nodes:
                if n.type == "TEX_IMAGE":
                    n.interpolation = "Cubic"
            if "Sheen Tint" in b.inputs:
                b.inputs["Sheen Tint"].default_value = (0.8, 0.85, 0.9, 1)
            if hair and b.inputs["Base Color"].links:
                hsv = nt.nodes.new("ShaderNodeHueSaturation"); hsv.inputs["Value"].default_value = hair_value
                src = b.inputs["Base Color"].links[0].from_socket
                nt.links.new(src, hsv.inputs["Color"]); nt.links.new(hsv.outputs["Color"], b.inputs["Base Color"])
                b.inputs["Roughness"].default_value = 0.42; b.inputs["Coat Weight"].default_value = 0.25
                b.inputs["Specular IOR Level"].default_value = 0.3
