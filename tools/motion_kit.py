"""Follow-through for things that hang off a bone (hair, hats with tails, bags, coat pieces).

    import motion_kit as mk
    mk.spring(["Handle1"], 1, 240)                       # hair lags and overshoots when the head moves or stops
    mk.spring(["Handle4"], 1, 240, length=0.5, stiffness=60, damping=6, rest=(0, -0.3, -1))   # heavier, slower

Each object must be bone-parented to the Avatar and not animated itself. A point `length` metres along `rest`
(given in the parent bone's space; default straight down in world at the first frame) is simulated as a damped
spring that chases where the bone carries it. The lag between the two becomes a small rotation of the object
about the bone's head, keyed on every frame (location + rotation_quaternion on the object).
Run it after the body animation is final; run clear(names) first to redo it.
"""
import math

import bpy
from mathutils import Matrix, Quaternion, Vector


def arm():
    return bpy.data.objects["Avatar"]


def clear(names):
    for n in names:
        o = bpy.data.objects[n]
        if "_spring_basis" in o:
            o.animation_data_clear(); o.matrix_basis = Matrix([o["_spring_basis"][i * 4:i * 4 + 4] for i in range(4)])


def spring(names, start, end, length=0.3, stiffness=120.0, damping=9.0, max_deg=25.0, rest=None, substeps=4):
    """Bake follow-through for bone-parented objects over frames start..end. Returns the peak lag in degrees."""
    s = bpy.context.scene; a = arm(); fps = s.render.fps / s.render.fps_base; dt = 1.0 / fps / substeps
    objs = [bpy.data.objects[n] for n in names]
    for o in objs:
        if o.parent != a or o.parent_type != "BONE":
            raise RuntimeError(f"motion_kit: {o.name} is not bone-parented to Avatar")
        if o.animation_data and o.animation_data.action:
            raise RuntimeError(f"motion_kit: {o.name} is already animated; run clear() first")
        o["_spring_basis"] = [v for row in o.matrix_basis for v in row]
    rec = {o.name: [] for o in objs}
    for f in range(start, end + 1):                     # pass 1: where the body carries each object
        s.frame_set(f)
        for o in objs:
            bm = a.matrix_world @ a.pose.bones[o.parent_bone].matrix
            rec[o.name].append((bm.translation.copy(), bm.to_quaternion(), o.matrix_world.copy()))
    peak = {}
    for o in objs:
        r = rec[o.name]; q0 = r[0][1]
        rest_b = Vector(rest).normalized() if rest else (q0.inverted() @ Vector((0, 0, -1)))
        x = r[0][0] + (q0 @ rest_b) * length; v = Vector(); basis = o.matrix_basis.copy()
        o.rotation_mode = "QUATERNION"; prev = None; peak[o.name] = 0.0
        for k, (piv, q, M) in enumerate(r):
            target = piv + (q @ rest_b) * length
            if k:
                p0 = r[k - 1][0] + (r[k - 1][1] @ rest_b) * length
                for i in range(1, substeps + 1):
                    tg = p0.lerp(target, i / substeps)
                    v += ((tg - x) * stiffness - v * damping) * dt; x += v * dt
            d0 = (target - piv).normalized(); d1 = (x - piv).normalized()
            lag = d0.rotation_difference(d1); ang = lag.angle
            if ang > math.radians(max_deg):
                lag = Quaternion(lag.axis, math.radians(max_deg))
                x = piv + (lag @ d0) * length; v *= 0.5
            peak[o.name] = max(peak[o.name], math.degrees(min(ang, math.radians(max_deg))))
            T = Matrix.Translation(piv)
            M2 = T @ lag.to_matrix().to_4x4() @ T.inverted() @ M
            nb = (M @ basis.inverted()).inverted() @ M2
            loc, rot, _sc = nb.decompose()
            if prev and rot.dot(prev) < 0:
                rot.negate()
            prev = rot.copy()
            o.location = loc; o.rotation_quaternion = rot
            o.keyframe_insert("location", frame=start + k); o.keyframe_insert("rotation_quaternion", frame=start + k)
    s.frame_set(start)
    return {k: round(v, 1) for k, v in peak.items()}
