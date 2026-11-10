"""Extra Poly Haven (CC0) bedroom assets into library/. Usage: python fetch_extras.py library"""
import json, os, sys, urllib.request
OUT = sys.argv[1]; UA = {"User-Agent": "bio-gfx-library/1.0"}
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read()
js = lambda u: json.loads(get(u))
def save(url, path):
    if os.path.exists(path): return 0
    os.makedirs(os.path.dirname(path), exist_ok=True); d = get(url); open(path, "wb").write(d); return len(d)
MODELS = {"decorative": ["throw_pillows_01", "brass_candleholders", "ornate_mirror_01", "alarm_clock_01", "fancy_picture_frame_02"],
          "electronics": ["television_02", "classic_laptop", "gaming_console"], "furniture": ["vintage_wooden_drawer_01", "side_table_01", "ArmChair_01"],
          "lighting": ["desk_lamp_arm_01"]}
TEX = {"fabric": ["velour_velvet", "wool_boucle", "curly_teddy_natural", "terry_cloth", "floral_jacquard"], "floor": ["wood_floor", "grey_plaster"]}
total = 0
for cat, ids in MODELS.items():
    for a in ids:
        try:
            g = js(f"https://api.polyhaven.com/files/{a}")["gltf"]["1k"]["gltf"]
            total += save(g["url"], f"{OUT}/models/{cat}/{a}/{a}.gltf")
            for rel, inc in g.get("include", {}).items(): total += save(inc["url"], f"{OUT}/models/{cat}/{a}/{rel}")
            print("ok", a, flush=True)
        except Exception as e: print("fail", a, e, flush=True)
for cat, ids in TEX.items():
    for a in ids:
        try:
            f = js(f"https://api.polyhaven.com/files/{a}")
            for m in ("Diffuse", "nor_gl", "Rough", "Displacement", "AO"):
                if m in f and "1k" in f[m]:
                    fmt = "jpg" if "jpg" in f[m]["1k"] else "png"
                    total += save(f[m]["1k"][fmt]["url"], f"{OUT}/textures/{cat}/{a}/{a}_{m}.{fmt}")
            print("ok", a, flush=True)
        except Exception as e: print("fail", a, e, flush=True)
print("MB", round(total / 1e6, 1))
