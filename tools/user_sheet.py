"""Numbered contact sheet of Roblox users' avatar thumbnails (public API) for picking avatars by eye.
usage: user_sheet.py "id,id,..." out.jpg   (writes out.json with the id list in sheet order)"""
import sys, json, urllib.request
import numpy as np, cv2

ids = [i for i in sys.argv[1].split(",") if i]
out = sys.argv[2]
UA = {"User-Agent": "Mozilla/5.0"}
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read()
urls = {}
for k in range(0, len(ids), 50):
    j = json.loads(get("https://thumbnails.roblox.com/v1/users/avatar?userIds=%s&size=420x420&format=Png" % ",".join(ids[k:k + 50])))
    urls.update({str(d["targetId"]): d.get("imageUrl") for d in j["data"]})
tiles = []
for n, i in enumerate(ids):
    im = np.full((420, 420, 3), 60, np.uint8)
    if urls.get(i):
        try:
            a = cv2.imdecode(np.frombuffer(get(urls[i]), np.uint8), cv2.IMREAD_UNCHANGED)
            al = a[:, :, 3:] / 255.0; im = (a[:, :, :3] * al + 60 * (1 - al)).astype(np.uint8)
        except Exception:
            pass
    im = cv2.copyMakeBorder(im, 0, 18, 0, 0, cv2.BORDER_CONSTANT, value=(30, 30, 30))
    cv2.putText(im, str(n), (6, 432), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1); tiles.append(im)
COLS = int(sys.argv[3]) if len(sys.argv) > 3 else 12
while len(tiles) % COLS:
    tiles.append(np.zeros_like(tiles[0]))
img = np.vstack([np.hstack(tiles[r:r + COLS]) for r in range(0, len(tiles), COLS)])
cv2.imwrite(out, cv2.resize(img, (img.shape[1] * 2 // 3, img.shape[0] * 2 // 3)))
json.dump(ids, open(out.rsplit(".", 1)[0] + ".json", "w"))
