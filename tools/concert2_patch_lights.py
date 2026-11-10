"""Patch the built anim_concert2 scene's lights in place (no rebuild): softer strobe flash, wider front key."""
import bpy, math
st = bpy.data.lights["Strobe"]
for fc in (st.animation_data.action.fcurves if st.animation_data and hasattr(st.animation_data.action, "fcurves") else []):
    for kp in fc.keyframe_points:
        kp.co[1] = min(kp.co[1], 6000); kp.interpolation = "CONSTANT"
try:
    for layer in st.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for kp in fc.keyframe_points:
                        kp.co[1] = min(kp.co[1], 6000); kp.interpolation = "CONSTANT"
except AttributeError:
    pass
k = bpy.data.objects["StageKey"].data; k.spot_size = math.radians(70)
for src in [k] :
    ad = src.animation_data
    if ad and ad.action:
        for layer in getattr(ad.action, "layers", []):
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        if fc.data_path == "energy":
                            for kp in fc.keyframe_points:
                                kp.co[1] *= 1.45
bpy.ops.wm.save_mainfile(); print("patched")
