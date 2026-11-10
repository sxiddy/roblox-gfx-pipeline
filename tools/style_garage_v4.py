"""Garage selfie, round 4: built on style_garage_selfie.py plus gfx_kit, tuned to measurements of
gfx_references/sttvr_l1ght_garage.png (warm daylight from the top, real concrete, head ~0.5 of frame width,
steep high angle with a strong roll, near sleeve filling the bottom-left).

Exec in Blender, then call stage_set(), stage_camera(...), stage_light(...) one at a time so the owner can watch.
"""
import glob
import importlib
import os
import sys

import bpy
from mathutils import Vector

TOOLS = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools"
sys.path.insert(0, TOOLS)
import gfx_kit as k  # noqa: E402
importlib.reload(k)
TEX = os.path.join(TOOLS, "..", "library", "textures")


def _img(nt, path, colour=True, scale=0.6):
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    if not colour:
        t.image.colorspace_settings.name = "Non-Color"
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs[0], t.inputs["Vector"])
    return t


def _tex(folder, kind):
    return glob.glob(os.path.join(TEX, "*", folder, f"*_{kind}.jpg"))[0]


def stage_set():
    """Garage set from the round-3 script, then real concrete under the procedural grime and yellow lines."""
    k.label("1/4 set: garage + real concrete texture")
    exec(open(os.path.join(TOOLS, "style_garage_selfie.py"), encoding="utf-8").read(), {"__name__": "garage"})
    k.clean_stray()
    floor = bpy.data.objects["Floor"]; m = floor.data.materials[0]; nt = m.node_tree
    mixc = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeMix" and n.data_type == "RGBA"
                and abs(n.inputs[7].default_value[0] - 0.55) < 0.01 and abs(n.inputs[7].default_value[1] - 0.38) < 0.01)
    crete = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeValToRGB")
    crete.color_ramp.elements[0].color = (0.35, 0.33, 0.3, 1); crete.color_ramp.elements[1].color = (1, 0.98, 0.95, 1)
    diff = _img(nt, _tex("concrete_floor_worn_001", "Diffuse"))
    mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs["Factor"].default_value = 1
    nt.links.new(diff.outputs["Color"], mul.inputs[6]); nt.links.new(crete.outputs["Color"], mul.inputs[7])
    nt.links.new(mul.outputs[2], mixc.inputs[6])
    mixc.inputs[7].default_value = (0.75, 0.52, 0.04, 1)
    b = nt.nodes["Principled BSDF"]
    nt.links.new(_img(nt, _tex("concrete_floor_worn_001", "Rough"), False).outputs["Color"], b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.8
    nt.links.new(_img(nt, _tex("concrete_floor_worn_001", "nor_gl"), False).outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    wall = bpy.data.objects["Wall"]; wall.data.materials.clear()
    wall.data.materials.append(k.pbr("concrete_layers_02", 0.5))
    k.show_camera()


def stage_camera(roll=-24, head_frac=0.6, head_xy=(0.4, 0.42), torso_xy=(0.2, 0.8), lean=(0.15, 0.6, 0.8),
                 head_tilt=(0.3, 0.15, 0.95), lens=14, head_angle=18):
    """Measured from the reference: no arm reaches to the lens. The body leans toward a high camera so the
    shoulder and jacket fill the bottom-left, the head is rolled. Search view directions with frame_head
    (exact head size and position), and score where the torso lands."""
    import math
    k.label("2/4 pose + camera: lean toward a high camera, head sized and placed from reference")
    k.apply_pose("idle")
    k.aim("LowerTorso", (lean[0] * 0.4, lean[1] * 0.4, 1), (0.2, 1, 0)); k.aim("UpperTorso", lean, (0.25, 1, 0))
    k.aim("UpperArm.P", (0.25, 0.35, -0.9)); k.aim("LowerArm.P", (0.1, 0.5, -0.85))
    k.aim("UpperArm.N", (-0.3, 0.2, -0.93)); k.aim("LowerArm.N", (-0.1, 0.4, -0.9))
    k.aim("UpperLeg.P", (0.08, 0.05, -1)); k.aim("UpperLeg.N", (-0.1, -0.05, -1))
    a = k.arm(); pb = a.pose.bones
    torso = lambda: a.matrix_world @ ((pb["UpperTorso"].head + pb["UpperTorso"].tail) / 2)
    best = None
    def head_aim(d, ht):  # face looks up toward the high camera; ht rolls the head top sideways
        k.aim("Head", (ht - 0.45 * d[0], -0.45 * d[1], 1), Vector(d))

    def axis_angle():  # on-screen angle of the head's up axis, degrees right of vertical
        c = k.project(a.matrix_world @ pb["Head"].head); t = k.project(a.matrix_world @ pb["Head"].tail)
        rx, ry = bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y
        return math.degrees(math.atan2((t[0] - c[0]) * rx, -(t[1] - c[1]) * ry))

    for az in range(0, 51, 10):  # the face must stay visible: no top-down or side-on views
      for el in (10, 20, 30, 40):
        for rl in (-30, -15, 0, 15, 30):
         for ht in (-0.6, -0.3, 0.0, 0.3, 0.6):
            d = (math.sin(math.radians(az)) * math.cos(math.radians(el)), math.cos(math.radians(az)) * math.cos(math.radians(el)),
                 math.sin(math.radians(el)))
            head_aim(d, ht)
            r = k.frame_head(head_frac, head_xy, d, lens, rl, iters=4)
            t = k.project(torso())
            sc = 2 * (abs(t[0] - torso_xy[0]) + abs(t[1] - torso_xy[1])) + 2 * abs(r["head_frac"] - head_frac)
            hx, hy = r["head_xy"]
            sc += 0 if ((t[0] - hx) ** 2 + (t[1] - hy) ** 2) ** 0.5 > 0.3 else 1  # torso must show beside the head
            sc += abs(axis_angle() - head_angle) / 60
            if best is None or sc < best[0]:
                best = (sc, az, el, d, rl, ht)
    _, az, el, d, roll, ht = best
    head_aim(d, ht); r = k.frame_head(head_frac, head_xy, d, lens, roll)
    k.show_camera()
    return {"score": round(best[0], 2), "az": az, "el": el, "roll": roll, "head_roll": ht, "head_angle": round(axis_angle()), **r, "torso": tuple(round(v, 2) for v in k.project(torso()))}


def stage_selfie(head_frac=0.75, head_xy=(0.36, 0.45), shoulder_xy=(0.1, 0.75), head_angle=18, lens=12,
                 lean=(0.12, 0.45, 0.88)):
    """Real selfie: a straight arm holds the phone; the lens sits just beside the fingertips so the hand is outside
    the wide field of view while the near shoulder shows in the bottom-left. Searches arm direction, lens offset
    from the hand, aim height, roll and head roll, and scores everything measured from the reference."""
    import math
    k.label("2/4 pose + camera: real selfie search (arm, phone position, roll)")
    k.apply_pose("idle")
    k.aim("LowerTorso", (lean[0] * 0.4, lean[1] * 0.4, 1), (0.2, 1, 0)); k.aim("UpperTorso", lean, (0.25, 1, 0))
    k.aim("UpperArm.N", (-0.3, 0.2, -0.93)); k.aim("LowerArm.N", (-0.1, 0.4, -0.9))
    a = k.arm(); pb = a.pose.bones; W = a.matrix_world
    P = lambda b, end="head": W @ getattr(pb[b], end)
    cam = bpy.context.scene.camera; cam.data.shift_x = cam.data.shift_y = 0; cam.data.lens = lens
    rx, ry = bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y
    inside = lambda p, m=0.0: p[2] > 0 and -m <= p[0] <= 1 + m and -m <= p[1] <= 1 + m

    def angle():
        c = k.project(P("Head")); t = k.project(P("Head", "tail"))
        return math.degrees(math.atan2((t[0] - c[0]) * rx, -(t[1] - c[1]) * ry))

    def setup(aa, ae, off, aim_dz, rl, ht):
        d = Vector((math.sin(math.radians(aa)) * math.cos(math.radians(ae)), math.cos(math.radians(aa)) * math.cos(math.radians(ae)),
                    math.sin(math.radians(ae))))
        for b in ("UpperArm.P", "LowerArm.P", "Hand.P"):
            k.aim(b, d, (0, 0, 1))
        c = P("Hand.P", "tail") + Vector(off)
        H = k.head_center(); v = (c - H).normalized()
        k.aim("Head", (ht - 0.4 * v.x, -0.4 * v.y, 1), v)
        k.place_camera(c, k.head_center() + Vector((0, 0, aim_dz)), lens, rl)
        return c

    best = None
    offs = [(x, y, z) for x in (-0.12, 0.0, 0.12) for y in (-0.06, 0.06) for z in (-0.12, 0.0, 0.12)]
    for aa in range(10, 81, 14):
        for ae in (10, 25, 40, 55):
            for off in offs:
                for aim_dz in (-0.25, -0.1):
                    for rl in (-20, 0, 20):
                        for ht in (-0.3, 0.0, 0.3):
                            c = setup(aa, ae, off, aim_dz, rl, ht)
                            if c.z < k.head_center().z + 0.05 or inside(k.project(P("Hand.P")), 0.02) or inside(k.project(P("Hand.P", "tail")), 0.02):
                                continue
                            m = k.measure(); sh = k.project(P("UpperArm.P"))
                            sc = 3 * abs(m["head_frac"] - head_frac) + 2 * (abs(m["head_xy"][0] - head_xy[0]) + abs(m["head_xy"][1] - head_xy[1]))
                            sc += abs(sh[0] - shoulder_xy[0]) + abs(sh[1] - shoulder_xy[1]) + abs(angle() - head_angle) / 45
                            if best is None or sc < best[0]:
                                best = (sc, aa, ae, off, aim_dz, rl, ht)
    if not best:
        return "no selfie found"
    setup(*best[1:])
    cam.data.dof.focus_distance = (cam.location - k.head_center()).length
    k.show_camera()
    return {"score": round(best[0], 2), "arm": best[1:3], "off": best[3], "roll": best[5], "head_roll": best[6], **k.measure(),
            "shoulder": tuple(round(v, 2) for v in k.project(P("UpperArm.P"))), "angle": round(angle())}


def stage_light(key=60, sky=0.6, exposure=0.3):
    """Warm daylight from the open side above, soft bounce from the floor, warm-tinted sky."""
    k.label("3/4 light: warm daylight from above, floor bounce")
    for o in [o for o in bpy.context.scene.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)
    H = k.head_center()
    k.area("Daylight", H + Vector((1.2, 0.6, 2.4)), H, key * 7, 4.0, (1.0, 0.86, 0.68))
    k.area("Bounce", H + Vector((0, 0.8, -1.0)), H, key * 0.6, 3.0, (1.0, 0.8, 0.55))
    k.area("Rim", H + Vector((-1.0, -1.2, 1.0)), H, key * 1.5, 1.0, (1.0, 0.9, 0.8))
    k.world((0.9, 0.75, 0.55), sky, haze=0.003)
    bpy.context.scene.view_settings.exposure = exposure
    k.show_camera()


def stage_render(path, percent=40, samples=48):
    k.label("4/4 rendering preview")
    k.render(path, percent, samples)
    k.label(None)


def stage_final(out_dir, head_x=0.4, samples=160):
    """Nudge the head to the measured x with lens shift (keeping the hand out of frame), full render + mask."""
    k.label("4/4 final render + avatar mask")
    cam = bpy.context.scene.camera; a = k.arm(); pb = a.pose.bones
    for _ in range(6):
        x = k.measure()["head_xy"][0]; cam.data.shift_x += (x - head_x) * 0.5625; k.upd()
    hand = [k.project(a.matrix_world @ v) for v in (pb["Hand.P"].head, pb["Hand.P"].tail)]
    os.makedirs(out_dir, exist_ok=True)
    k.render(os.path.join(out_dir, "v4_raw.png"), 100, samples)
    k.render_mask(os.path.join(out_dir, "v4_mask.png"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "sttvr_l1ght_garage_v4.blend"), copy=True)
    k.label(None)
    return {**k.measure(), "hand": [tuple(round(v, 2) for v in h) for h in hand]}
