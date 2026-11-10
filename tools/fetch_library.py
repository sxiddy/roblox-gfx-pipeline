"""Download a curated GFX library: Poly Haven (CC0) HDRIs, models, textures + Google Fonts (OFL).
Picks the most-downloaded assets per category. Usage: python fetch_library.py out_dir"""
import json, os, sys, urllib.request

OUT = sys.argv[1]
UA = {"User-Agent": "bio-gfx-library/1.0"}
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read()
js = lambda u: json.loads(get(u))

def save(url, path):
    if os.path.exists(path): return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = get(url); open(path, "wb").write(data)

def top(kind, cat, n):
    a = js(f"https://api.polyhaven.com/assets?t={kind}&c={cat.replace(' ', '%20')}")
    return sorted(a, key=lambda k: -a[k].get("download_count", 0))[:n]

PLAN = {
    "hdris": [("sunrise-sunset", 6), ("urban", 6), ("indoor", 6), ("night", 5), ("nature", 4), ("studio", 6), ("skies", 3)],
    "models": [("furniture", 14), ("food", 8), ("plants", 10), ("decorative", 10), ("electronics", 6), ("props", 10), ("vehicles", 4), ("lighting", 5), ("rocks", 4)],
    "textures": [("floor", 6), ("wall", 6), ("terrain", 5), ("wood", 4), ("concrete", 4), ("fabric", 4), ("metal", 3)],
}
done = set()
for kind, cats in PLAN.items():
    for cat, n in cats:
        try:
            ids = top(kind, cat, n)
        except Exception as e:
            print("cat fail", kind, cat, e); continue
        for aid in ids:
            if aid in done: continue
            done.add(aid)
            try:
                f = js(f"https://api.polyhaven.com/files/{aid}")
                if kind == "hdris":
                    save(f["hdri"]["2k"]["hdr"]["url"], f"{OUT}/hdri/{cat}/{aid}.hdr")
                elif kind == "models":
                    g = f["gltf"]["1k"]["gltf"]
                    save(g["url"], f"{OUT}/models/{cat}/{aid}/{aid}.gltf")
                    for rel, inc in g.get("include", {}).items():
                        save(inc["url"], f"{OUT}/models/{cat}/{aid}/{rel}")
                else:
                    for m in ("Diffuse", "nor_gl", "Rough", "Displacement", "AO"):
                        if m in f and "1k" in f[m]:
                            fmt = "jpg" if "jpg" in f[m]["1k"] else "png"
                            save(f[m]["1k"][fmt]["url"], f"{OUT}/textures/{cat}/{aid}/{aid}_{m}.{fmt}")
                print("ok", kind, cat, aid, flush=True)
            except Exception as e:
                print("fail", aid, e, flush=True)

FONTS = ["ofl/bebasneue", "ofl/anton", "ofl/montserrat", "ofl/bungee", "ofl/rubikglitch", "ofl/monoton", "ofl/pacifico",
         "ofl/lobster", "apache/permanentmarker", "ofl/creepster", "ofl/orbitron", "ofl/pressstart2p", "ofl/unifrakturmaguntia",
         "ofl/pirataone", "ofl/dancingscript", "ofl/bangers", "ofl/righteous", "ofl/rubikwetpaint", "ofl/metalmania", "ofl/sixcaps"]
for d in FONTS:
    try:
        for it in js(f"https://api.github.com/repos/google/fonts/contents/{d}"):
            if it["name"].endswith(".ttf") or it["name"] in ("OFL.txt", "LICENSE.txt"):
                save(it["download_url"], f"{OUT}/fonts/{d.split('/')[1]}/{it['name']}")
        print("ok font", d, flush=True)
    except Exception as e:
        print("fail font", d, e, flush=True)
print("DONE", len(done), "assets")
