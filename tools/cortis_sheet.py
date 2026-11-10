"""Contact sheet of catalog items (public thumbnails + names) so outfits can be picked by eye.
usage: cortis_sheet.py "id:type,id:type,..." out_dir"""
import sys, os, json, urllib.request, io
import numpy as np, cv2

pairs = [p.split(":") for p in sys.argv[1].split(",") if p]
out = sys.argv[2]; os.makedirs(out, exist_ok=True)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read()


ids = [i for i, _ in pairs]; thumbs = {}
for k in range(0, len(ids), 40):
    j = json.loads(get("https://thumbnails.roblox.com/v1/assets?assetIds=%s&size=150x150&format=Png" % ",".join(ids[k:k + 40])))
    thumbs.update({str(d["targetId"]): d.get("imageUrl") for d in j["data"]})
info = {}
tiles = []
for i, t in pairs:
    try:
        name = json.loads(get("https://economy.roblox.com/v2/assets/%s/details" % i)).get("Name", "?")
    except Exception:
        name = "?"
    info[i] = dict(type=t, name=name)
    img = np.full((190, 170, 3), 40, np.uint8)
    if thumbs.get(i):
        a = cv2.imdecode(np.frombuffer(get(thumbs[i]), np.uint8), cv2.IMREAD_UNCHANGED)
        if a is not None:
            if a.shape[2] == 4:
                al = a[:, :, 3:] / 255.0; a = (a[:, :, :3] * al + 40 * (1 - al)).astype(np.uint8)
            img[5:155, 10:160] = cv2.resize(a, (150, 150))
    cv2.putText(img, "%s t%s" % (i[-6:], t), (4, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    cv2.putText(img, name[:24], (4, 184), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (200, 220, 255), 1)
    tiles.append(img)
json.dump(info, open(os.path.join(out, "items.json"), "w"), indent=1)
cols = 8
while len(tiles) % cols:
    tiles.append(np.zeros_like(tiles[0]))
rows = [np.hstack(tiles[r:r + cols]) for r in range(0, len(tiles), cols)]
cv2.imwrite(os.path.join(out, "sheet.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
print(len(pairs), "items")
