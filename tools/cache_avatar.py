"""Rig one avatar export with build_exact_gfx and save it alone to gfx_output/avatar_cache/<name>.blend (for appending
several avatars into one scene, since the builder wipes the scene).
  blender -b --factory-startup -P tools/cache_avatar.py -- <avatar folder name>"""
import sys, os
import bpy
from mathutils import Vector
ROOT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender"
name = sys.argv[sys.argv.index("--") + 1]
G = {"__name__": "bx", "AVATAR_DIR": os.path.join(ROOT, "avatars", name), "POSE": "idle"}
exec(open(os.path.join(ROOT, "tools", "build_exact_gfx.py"), encoding="utf-8").read(), G)
for o in list(bpy.data.objects):
    if o.name in ("Backdrop", "Halo") or o.type in ("LIGHT", "CAMERA"):
        bpy.data.objects.remove(o, do_unlink=True)
a = bpy.data.objects["Avatar"]; a.name = "AV_" + name; bpy.context.view_layer.update()
low = min((o.matrix_world @ Vector(c)).z for o in a.children_recursive if o.type == "MESH" for c in o.bound_box)
a.location.z -= low
os.makedirs(os.path.join(ROOT, "gfx_output", "avatar_cache"), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "gfx_output", "avatar_cache", name + ".blend"))
print("cached", name)
