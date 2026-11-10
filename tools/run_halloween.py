"""blender -b --factory-startup -P run_halloween.py -- pumpkin|lantern [pct samples]"""
import os, sys
T = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools"
G = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\gfx_output\sttvr_l1ght"
a = sys.argv[sys.argv.index("--") + 1:]
which = a[0]; PCT = int(a[1]) if len(a) > 1 else 50; SAMPLES = int(a[2]) if len(a) > 2 else 64
OUT = os.path.join(G, which + ("_final" if PCT >= 100 else ""))
AVATAR_DIR = os.environ.get("GFX_AVATAR") or r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\avatars\sttvr_l1ght_2026-11-02"
POSE = "idle"
exec(compile(open(os.path.join(T, "build_exact_gfx.py"), encoding="utf-8").read(), "build", "exec"))
exec(compile(open(os.path.join(T, "style_%s.py" % which), encoding="utf-8").read(), which, "exec"))
