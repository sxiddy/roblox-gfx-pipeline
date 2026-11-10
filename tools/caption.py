"""Calm flat caption for the welcome render: python -I caption.py IN OUT"""
import sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGBA"); W, H = im.size
F = r"C:\Users\Siddharth D\Projects\gfx and animation roblox blender\library\fonts"
def font(n, f, px): return ImageFont.truetype(F + "/" + n + "/" + f, px)
big = font("pacifico", "Pacifico-Regular.ttf", int(H * 0.17))
small = font("montserrat", [x for x in __import__("os").listdir(F + r"\montserrat") if x.lower().endswith(".ttf")][0], int(H * 0.04)); small.set_variation_by_axes([600])
FILL = (206, 84, 124, 255)
def spaced(d, xy, s, f, fill, sp):
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill); x += d.textlength(ch, font=f) + sp
    return x
def heart(d, cx, cy, r, fill):
    pts = [(cx + r * 16 * math.sin(t) ** 3 / 16, cy - r * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16)
           for t in [i * math.pi / 60 for i in range(121)]]
    d.polygon(pts, fill=fill)
lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
x0, y0 = int(W * 0.06), int(H * 0.22)
spaced(d, (x0 + 6, y0), "WELCOME BACK", small, FILL, int(H * 0.012))
d.text((x0, y0 + int(H * 0.055)), "Suhie", font=big, fill=FILL)
heart(d, x0 + int(W * 0.265), y0 + int(H * 0.135), int(H * 0.034), FILL)
sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
sh.paste((110, 40, 70, 90), (6, 8), lay.split()[3]); sh = sh.filter(ImageFilter.GaussianBlur(10))
im = Image.alpha_composite(Image.alpha_composite(im, sh), lay); im.convert("RGB").save(out)
