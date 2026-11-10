"""Procedural 'code + hearts' monitor textures for the hacker room v2: app windows with title bars, syntax-coloured code,
a waveform, chat bubbles and a glowing neon heart. Usage: python make_screens.py OUT_DIR"""
import math, random, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PINK, VIOLET, CYAN, SOFT = (255, 80, 170), (170, 110, 255), (80, 220, 255), (255, 205, 232)


def heart_pts(cx, cy, s):
    return [(cx + s * math.sin(t) ** 3, cy - s * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16)
            for t in [i / 120 * 2 * math.pi for i in range(120)]]


def font(n):
    for f in ("consola.ttf", "arial.ttf"):
        try: return ImageFont.truetype(f, n)
        except Exception: pass
    return ImageFont.load_default()


def window(d, box, title, accent, body):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, 14, fill=(20, 10, 40), outline=accent, width=3)
    d.rounded_rectangle((x0, y0, x1, y0 + 44), 14, fill=(34, 16, 62))
    for i, c in enumerate(((255, 95, 120), (255, 200, 90), (110, 230, 150))):
        d.ellipse((x0 + 18 + i * 28, y0 + 14, x0 + 32 + i * 28, y0 + 28), fill=c)
    d.text((x0 + 120, y0 + 8), title, fill=SOFT, font=font(26))
    body(d, (x0 + 20, y0 + 60, x1 - 20, y1 - 16))


def code_body(rng):
    toks = ["def", "love", "<3", "if", "return", "self", "print", "glitch", "0xFF", "while", "heart", "True", "->", "::", "await"]
    cols = [PINK, VIOLET, CYAN, SOFT]
    def body(d, b):
        y = b[1]; n = 0
        while y < b[3] - 30:
            d.text((b[0], y), "%02d" % n, fill=(110, 80, 160), font=font(26)); x = b[0] + 60 + 40 * rng.randint(0, 2)
            for _ in range(rng.randint(2, 6)):
                t = rng.choice(toks); d.text((x, y), t, fill=rng.choice(cols), font=font(26)); x += 17 * len(t) + 18
                if x > b[2] - 100: break
            y += 36; n += 1
    return body


def wave_body(rng, col):
    def body(d, b):
        mid = (b[1] + b[3]) // 2; pts = []
        for x in range(b[0], b[2], 6):
            pts.append((x, mid + math.sin(x / 40) * 90 * math.sin(x / 190) + rng.randint(-14, 14)))
        d.line(pts, fill=col, width=5)
        for gy in range(b[1], b[3], 60): d.line([(b[0], gy), (b[2], gy)], fill=(46, 28, 80), width=1)
    return body


def chat_body(rng):
    def body(d, b):
        y = b[1] + 6
        for i in range(6):
            w = rng.randint(220, 440); left = i % 2 == 0; x0 = b[0] if left else b[2] - w
            d.rounded_rectangle((x0, y, x0 + w, y + 54), 26, fill=(70, 30, 110) if left else (255, 80, 170))
            d.text((x0 + 24, y + 12), "<3 " + "." * rng.randint(3, 14), fill=(255, 235, 245), font=font(28)); y += 74
    return body


def make(path, seed, accent):
    rng = random.Random(seed); W, H = 1920, 1080
    base = Image.new("RGB", (W, H), (12, 6, 26)); d = ImageDraw.Draw(base)
    for y in range(H):  # soft gradient wallpaper
        t = y / H; d.line([(0, y), (W, y)], fill=(int(14 + 30 * t), int(6 + 8 * t), int(30 + 36 * t)))
    glow = Image.new("RGB", (W, H), (0, 0, 0)); g = ImageDraw.Draw(glow)
    for s_, col, w_ in ((330, accent, 14), (250, SOFT, 8)):  # neon heart line art, drawn twice for a hot core
        g.line(heart_pts(W // 2 + (seed - 2) * 120, H // 2 - 20, s_) + [heart_pts(W // 2 + (seed - 2) * 120, H // 2 - 20, s_)[0]], fill=col, width=w_)
    halo = glow.filter(ImageFilter.GaussianBlur(26)); base = Image.blend(base, base, 0)
    base = Image.composite(base, base, Image.new("L", (W, H), 255))
    from PIL import ImageChops
    base = ImageChops.add(base, ImageChops.add(halo, halo)); base = ImageChops.add(base, glow)
    d = ImageDraw.Draw(base)
    window(d, (70, 70, 900, 520), "love.py - glitch", PINK, code_body(rng))
    window(d, (960, 90, 1850, 420), "signal.wav", CYAN, wave_body(rng, CYAN))
    window(d, (1180, 470, 1850, 1010), "messages", VIOLET, chat_body(rng))
    window(d, (110, 600, 760, 1010), "terminal", accent, code_body(rng))
    for y in range(0, H, 4): d.line([(0, y), (W, y)], fill=(0, 0, 0), width=1)
    base.save(path)


if __name__ == "__main__":
    out = sys.argv[1]
    make(out + "/hk_screen1.png", 1, PINK); make(out + "/hk_screen2.png", 2, VIOLET); make(out + "/hk_screen3.png", 3, CYAN)
