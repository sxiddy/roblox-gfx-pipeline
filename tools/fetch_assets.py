"""Download named Poly Haven (CC0) assets into library/. Usage:
python fetch_assets.py models <category> <res> id1 id2 ...   |   python fetch_assets.py textures <category> <res> id1 ..."""
import json, os, sys, urllib.request

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library")
UA = {"User-Agent": "bio-gfx-library/1.0"}
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=180).read()

def save(url, path):
    if os.path.exists(path): return
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, "wb").write(get(url))

kind, cat, res, ids = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
for aid in ids:
    try:
        f = json.loads(get(f"https://api.polyhaven.com/files/{aid}"))
        if kind == "models":
            g = f["gltf"][res]["gltf"]; base = f"{LIB}/models/{cat}/{aid}"
            save(g["url"], f"{base}/{aid}.gltf")
            for rel, inc in g.get("include", {}).items():
                save(inc["url"], f"{base}/{rel}")
        else:
            for m in ("Diffuse", "nor_gl", "Rough", "Displacement", "AO"):
                if m in f and res in f[m]:
                    fmt = "jpg" if "jpg" in f[m][res] else "png"
                    save(f[m][res][fmt]["url"], f"{LIB}/textures/{cat}/{aid}/{aid}_{m}.{fmt}")
        print("ok", aid, flush=True)
    except Exception as e:
        print("fail", aid, e, flush=True)
