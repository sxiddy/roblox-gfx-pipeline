"""IK for the Avatar rig that build_exact_gfx.py makes: planted feet and hands that reach a target.

    import ik_kit as ik
    ik.add()                                  # targets + poles for both legs and both arms
    ik.add(limbs=("leg",))                    # legs only
    ik.key("IK_Foot.P", 1); ik.key("IK_Foot.P", 30)            # foot stays where it is from frame 1 to 30
    ik.key("IK_Hand.N", 12, loc=(0.3, 0.4, 1.1))               # hand reaches a world point on frame 12
    ik.bake(1, 120)                           # turn the result into plain bone keys and remove the IK

Targets are empties named IK_Foot.P / IK_Foot.N / IK_Hand.P / IK_Hand.N (world space; feet stay put when the
body moves, hands follow the Avatar object unless keyed). Poles IK_Knee.* sit in front of the knees and
IK_Elbow.* behind the elbows; move a pole to turn a knee or elbow. ".P" is the avatar's right.
Animate the body (LowerTorso and above) as usual; the legs solve themselves. Bake before rendering long jobs
or before using motion_kit / the choreography tools, which expect plain bone keys.
"""
import math

import bpy
from mathutils import Vector

LIMBS = {"leg": ("UpperLeg", "LowerLeg", "Foot", "Knee", (0, 1, 0)),
         "arm": ("UpperArm", "LowerArm", "Hand", "Elbow", (0, -1, 0))}


def arm():
    return bpy.data.objects["Avatar"]


def _empty(name, loc, size, parent=None):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    e = bpy.data.objects.new(name, None); e.empty_display_type = "SPHERE"; e.empty_display_size = size
    arm().users_collection[0].objects.link(e)
    if parent:
        e.parent = parent; e.matrix_parent_inverse = parent.matrix_world.inverted()
    e.matrix_world.translation = loc; e.location = (parent.matrix_world.inverted() @ Vector(loc)) if parent else loc
    if parent:
        e.matrix_parent_inverse.identity()
    return e


def _pole_angle(base, end, pole_arm):
    """Standard pole-angle formula, all in armature space."""
    def signed(v1, v2, n):
        ang = v1.angle(v2)
        return -ang if v1.cross(v2).angle(n) < 1 else ang
    normal = (end.tail - base.head).cross(pole_arm - base.head)
    proj = normal.cross(base.tail - base.head)
    return signed(base.x_axis, proj, base.tail - base.head)


def add(limbs=("leg", "arm"), sides="PN", foot_flat=True):
    """Add IK to the chosen limbs at the current pose. Returns the names of the targets made."""
    a = arm(); bpy.context.view_layer.update(); mw = a.matrix_world; inv = mw.inverted(); made = []
    scale = max(mw.to_scale())
    for limb in limbs:
        up, low, end, joint, fwd = LIMBS[limb]
        for s in sides:
            pu, pl, pe = (a.pose.bones[f"{n}.{s}"] for n in (up, low, end))
            for c in [c for c in pl.constraints if c.type == "IK"] + [c for c in pe.constraints if c.name == "IK_flat"]:
                (pl if c.type == "IK" else pe).constraints.remove(c)
            tgt = _empty(f"IK_{end}.{s}", mw @ pl.tail, 0.06 * scale / 0.28, None if limb == "leg" else a)
            reach = (pu.length + pl.length)
            pole_arm = pl.head + Vector(fwd) * reach * 0.8
            pole = _empty(f"IK_{joint}.{s}", mw @ pole_arm, 0.04 * scale / 0.28, a)
            c = pl.constraints.new("IK"); c.target = tgt; c.pole_target = pole; c.chain_count = 2
            c.pole_angle = _pole_angle(pu, pl, pole_arm)
            if limb == "leg" and foot_flat:           # the foot keeps its world rotation while planted
                tgt.rotation_mode = "QUATERNION"; tgt.rotation_quaternion = (mw @ pe.matrix).to_quaternion()
                r = pe.constraints.new("COPY_ROTATION"); r.name = "IK_flat"; r.target = tgt
            made.append(tgt.name)
    bpy.context.view_layer.update()
    return made


def key(target, frame, loc=None):
    """Key an IK target's position (world). Without loc it is keyed where it is now."""
    e = bpy.data.objects[target]
    if loc is not None:
        e.location = (e.parent.matrix_world.inverted() @ Vector(loc)) if e.parent else Vector(loc)
    e.keyframe_insert("location", frame=frame)


def bake(start, end, remove=True):
    """Write the solved pose to plain bone keys on every frame, then remove the IK constraints."""
    s = bpy.context.scene; a = arm(); order = []
    def walk(b):
        order.append(b.name)
        for ch in b.children:
            walk(ch)
    for b in a.data.bones:
        if not b.parent:
            walk(b)
    mats = {}
    for f in range(start, end + 1):
        s.frame_set(f); mats[f] = {n: a.pose.bones[n].matrix.copy() for n in order}
    if remove:
        for pb in a.pose.bones:
            for c in [c for c in pb.constraints if c.type == "IK" or c.name == "IK_flat"]:
                pb.constraints.remove(c)
    for f in range(start, end + 1):
        s.frame_set(f)
        for n in order:
            pb = a.pose.bones[n]; pb.matrix = mats[f][n]; bpy.context.view_layer.update()
            pb.keyframe_insert("location", frame=f)
            pb.keyframe_insert("rotation_quaternion" if pb.rotation_mode == "QUATERNION" else "rotation_euler", frame=f)
    s.frame_set(start)
    return len(order) * (end - start + 1)
