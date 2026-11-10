import os
T = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools"
AVATAR_DIR = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\avatars\sttvr_l1ght"
POSE = "idle"
PCT = 100; SAMPLES = 192; OUT = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\gfx_output\sttvr_l1ght\haunt_final"
exec(compile(open(os.path.join(T, "build_exact_gfx.py"), encoding="utf-8").read(), "build", "exec"))
exec(compile(open(os.path.join(T, "style_haunt.py"), encoding="utf-8").read(), "haunt", "exec"))
