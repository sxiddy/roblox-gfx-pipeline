"""Spray-paint overlay (RGBA) for the skate-spot wall: soft muted spray clouds and a few drips, no text
(owner: no cringe). Laid over a real concrete texture in Blender. python make_graffiti.py OUT.png"""
import sys, random
from PIL import Image, ImageDraw, ImageFilter

W, H = 3072, 1536
rnd = random.Random(24)
PAL = [(105, 35, 165), (130, 25, 45), (35, 100, 120), (95, 40, 150)]
img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
for _ in range(14):
    x, y, r = rnd.randrange(W), rnd.randrange(H // 6, H), rnd.randrange(160, 420); c = rnd.choice(PAL)
    d.ellipse((x - r, y - r // 2, x + r, y + r // 2), fill=(*c, rnd.randrange(110, 190)))
img = img.filter(ImageFilter.GaussianBlur(70))
d = ImageDraw.Draw(img)
# grime: dark water stains running down from the top and a dirty band along the base
grime = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(grime)
for _ in range(60):
    x = rnd.randrange(W); w = rnd.randrange(20, 90); L = rnd.randrange(150, 700)
    gd.rectangle((x, 0, x + w, L), fill=(12, 10, 10, rnd.randrange(40, 110)))
gd.rectangle((0, int(H * 0.82), W, H), fill=(10, 9, 8, 150))
grime = grime.filter(ImageFilter.GaussianBlur(28))
img = Image.alpha_composite(img, grime)
img.save(sys.argv[1])
print("saved", sys.argv[1])
