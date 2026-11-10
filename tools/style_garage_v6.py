"""Garage selfie v6 for sttvr_l1ght: v5 set, camera, light and grade, with a pose that suits the chibi avatar.

Pose plan (owner: pose may differ from the reference to suit the avatar):
- camera: v5 high front selfie camera, head big in frame, rail roll
- near arm (P): reaches to the lens and leaves the bottom-left edge (the selfie arm)
- far arm (N): peace sign by the cheek, hand just right of the face, in front of the hair
- head: ~15 deg roll toward the lens, slight dip, face to camera
- body: leaning forward so the shoulders fill the bottom of the frame
Wall: painted plaster in object space with soft dirt patches (v5 streaks read as wood planks).
"""
import math

import bpy
from mathutils import Vector

G = {"__name__": "v5"}
exec(open(r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools\style_garage_v5.py", encoding="utf-8").read(), G)
k = G["k"]


def stage_wall():
    k.label("v6 wall: plaster concrete in object space, soft dirt patches")
    wall = bpy.data.objects["Wall"]
    wall.data.materials.clear(); wm = k.pbr("painted_plaster_wall", 0.8, tint=(0.5, 0.52, 0.53)); wall.data.materials.append(wm)
    nt = wm.node_tree
    tc = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeTexCoord"), None)
    for mp in (n for n in nt.nodes if n.bl_idname == "ShaderNodeMapping"):
        if tc:
            nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    for t in (n for n in nt.nodes if n.bl_idname == "ShaderNodeTexImage"):
        t.projection = "BOX"; t.projection_blend = 0.3
    b = nt.nodes["Principled BSDF"]; src = b.inputs["Base Color"].links[0].from_socket
    tc2 = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.5; nz.inputs["Detail"].default_value = 6
    nt.links.new(tc2.outputs["Object"], nz.inputs["Vector"])
    rp = nt.nodes.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].position = 0.4; rp.color_ramp.elements[1].position = 0.7
    rp.color_ramp.elements[0].color = (0.55, 0.52, 0.48, 1); rp.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(nz.outputs["Fac"], rp.inputs["Fac"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1
    nt.links.new(src, mx.inputs[6]); nt.links.new(rp.outputs["Color"], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs["Base Color"])
    k.show_camera()


def _cheek_target():
    """Screen point just right of the face (avatar's left cheek side), at mouth height."""
    hx, hy, _ = k.project(k.head_center())
    return hx + 0.27, hy + 0.14  # 0.17/0.08 put the sleeve over her eye


def stage_pose(head_deg=15, head_frac=0.9, head_xy=(0.5, 0.46)):
    r = G["stage_camera"](head_frac=head_frac, head_xy=head_xy, torso_xy=(0.35, 0.85), head_deg=head_deg)
    k.label("v6 pose: far hand peace sign by the cheek, leaning in")
    a = k.arm(); pb = a.pose.bones; W = a.matrix_world
    cam = bpy.context.scene.camera
    to_cam = (cam.location - k.head_center()).normalized()
    tx, ty = _cheek_target(); hd = k.project(k.head_center())[2]
    best = None
    for ua in range(-60, 61, 15):           # upper arm: out to the side and forward
        for ue in range(-60, 31, 15):
            u = Vector((-math.cos(math.radians(ue)) * math.cos(math.radians(ua)), math.sin(math.radians(ua)) * math.cos(math.radians(ue)), math.sin(math.radians(ue))))
            k.aim("UpperArm.N", u, (0, 0, 1))
            for fa in range(-90, 91, 15):   # forearm folds up toward the face
                for fe in range(0, 91, 15):
                    f = Vector((math.sin(math.radians(fa)) * math.cos(math.radians(fe)), math.cos(math.radians(fa)) * math.cos(math.radians(fe)), math.sin(math.radians(fe))))
                    k.aim("LowerArm.N", f, (0, 0, 1))
                    k.aim("Hand.N", (f + Vector((0, 0, 0.6))).normalized(), to_cam)
                    p = k.project(W @ pb["Hand.N"].tail)
                    if p[2] <= 0 or p[2] > hd:  # must sit in front of the head
                        continue
                    sc = abs(p[0] - tx) + abs(p[1] - ty)
                    if best is None or sc < best[0]:
                        best = (sc, u, f)
    if best:
        k.aim("UpperArm.N", best[1], (0, 0, 1)); k.aim("LowerArm.N", best[2], (0, 0, 1))
        k.aim("Hand.N", (best[2] + Vector((0, 0, 0.6))).normalized(), to_cam)
    k.show_camera()
    return {**r, "hand_err": round(best[0], 3) if best else None, "handN": tuple(round(v, 2) for v in k.project(W @ pb["Hand.N"].tail))}


def stage_final(out_dir, samples=256):
    sc = bpy.context.scene
    sc.cycles.samples = samples; sc.render.resolution_percentage = 100
    sc.render.filepath = out_dir + r"\v6_raw.png"; bpy.ops.render.render(write_still=True)
    k.render_mask(out_dir + r"\v6_mask.png")
    bpy.ops.wm.save_as_mainfile(filepath=out_dir + r"\sttvr_l1ght_garage_v6.blend", copy=True)
