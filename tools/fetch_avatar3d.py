"""Download a Roblox avatar-3d export (OBJ + MTL + textures) from its metadata JSON.
Get the JSON (needs a logged-in roblox.com session) from
  https://thumbnails.roblox.com/v1/users/avatar-3d?userId=<id>  -> imageUrl -> that JSON.
Files keep their CDN hash names, which is what the OBJ/MTL reference.
Usage: python fetch_avatar3d.py meta.json out_dir"""
import gzip, json, os, sys, urllib.request

def cdn(h):
    i = 31
    for c in h:
        i ^= ord(c)
    return f"https://t{i % 8}.rbxcdn.com/{h}"

meta = json.load(open(sys.argv[1]))
out = sys.argv[2]; os.makedirs(out, exist_ok=True)
for h in [meta["obj"], meta["mtl"], *meta["textures"]]:
    data = urllib.request.urlopen(cdn(h)).read()
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    open(os.path.join(out, h), "wb").write(data)
    print(h, len(data))
json.dump(meta, open(os.path.join(out, "meta.json"), "w"), indent=1)
