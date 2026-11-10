"""Mock Discord window for the 'Through Flames' server (public invite data: name, description, 290 members / 50 online,
channel #suhie, icon). Chat lines are invented decoration. Usage: python make_discord_screen.py OUT_DIR"""
import math, random, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1]
W, H = 1920, 1080
BG, SIDE, CHAN, TEXT, DIM, ACC = (49, 51, 56), (30, 31, 34), (43, 45, 49), (219, 222, 225), (148, 155, 164), (255, 120, 50)


def font(n, bold=False):
    for f in (("segoeuib.ttf" if bold else "segoeui.ttf"), "arial.ttf"):
        try: return ImageFont.truetype(f, n)
        except Exception: pass
    return ImageFont.load_default()


def emoji(n):
    try: return ImageFont.truetype("seguiemj.ttf", n)
    except Exception: return None


im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
d.rectangle((0, 0, 140, H), fill=SIDE); d.rectangle((140, 0, 700, H), fill=CHAN)
icon = Image.open(OUT + "/dc_icon.png").convert("RGB").resize((96, 96))
mask = Image.new("L", (96, 96), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, 95, 95), 30, fill=255)
d.rounded_rectangle((8, 40, 12, 120), 3, fill=(255, 255, 255)); im.paste(icon, (22, 36), mask)
for i, c in enumerate(((88, 101, 242), (60, 60, 70), (60, 60, 70), (35, 165, 90))):   # other server bubbles
    d.ellipse((22, 160 + i * 110, 118, 256 + i * 110), fill=c)
d.rectangle((140, 0, 700, 86), fill=(43, 45, 49)); d.line((140, 86, 700, 86), fill=(30, 31, 34), width=3)
d.text((170, 22), "Through ", fill=TEXT, font=font(36, True))
e = emoji(34)
d.text((170 + 150, 22), "\U0001F525", font=e, embedded_color=True) if e else None
d.text((170 + 200, 22), "Flames", fill=TEXT, font=font(36, True))
for i, (name, active) in enumerate((("welcome", 0), ("rules", 0), ("announcements", 0), ("suhie", 1), ("music", 0), ("shows", 0), ("events", 0), ("drama", 0), ("voice lounge", 0))):
    y = 130 + i * 64
    if active: d.rounded_rectangle((156, y - 6, 684, y + 46), 10, fill=(64, 66, 73))
    d.text((176, y), "#", fill=DIM, font=font(34)); d.text((216, y), name, fill=TEXT if active else DIM, font=font(32, active))
d.rectangle((140, H - 120, 700, H), fill=(35, 36, 40)); d.ellipse((165, H - 100, 225, H - 40), fill=(150, 60, 110))
d.text((245, H - 98), "suhaa", fill=TEXT, font=font(30, True)); d.text((245, H - 62), "Online", fill=DIM, font=font(24))
# header of chat
d.rectangle((700, 0, W - 520, 86), fill=BG); d.line((700, 86, W, 86), fill=(30, 31, 34), width=3)
d.text((730, 22), "#  suhie", fill=TEXT, font=font(36, True))
d.text((960, 30), "Music... shows... events... drama... it's fun.", fill=DIM, font=font(26))
msgs = [("Suhie", (255, 150, 200), "welcome back everyone, we're live tonight"), ("Through Flames", ACC, "290 members and counting"),
        ("member", (120, 190, 255), "who's coming to the show?"), ("Suhie", (255, 150, 200), "doors open soon, bring your friends"),
        ("member", (150, 255, 170), "new track just dropped, go listen"), ("Suhie", (255, 150, 200), "thank you for being here, it means a lot")]
y = 130
for who, col, line in msgs:
    d.ellipse((730, y, 794, y + 64), fill=col); d.text((820, y - 4), who, fill=col, font=font(32, True)); d.text((820, y + 38), line, fill=TEXT, font=font(30)); y += 150
d.rounded_rectangle((730, H - 120, W - 550, H - 50), 18, fill=(56, 58, 64)); d.text((770, H - 104), "Message #suhie", fill=DIM, font=font(30))
# member list
d.rectangle((W - 500, 87, W, H), fill=CHAN)
d.text((W - 470, 120), "ONLINE  50", fill=DIM, font=font(26, True))
for i, (nm, col) in enumerate((("Suhie", (255, 150, 200)), ("DJ", ACC), ("member", (120, 190, 255)), ("member", (150, 255, 170)), ("member", (255, 220, 120)), ("member", (200, 160, 255)))):
    yy = 180 + i * 86; d.ellipse((W - 470, yy, W - 410, yy + 60), fill=col); d.ellipse((W - 428, yy + 42, W - 410, yy + 60), fill=(35, 165, 90), outline=CHAN, width=3)
    d.text((W - 390, yy + 10), nm, fill=TEXT, font=font(30))
d.text((W - 470, 740), "OFFLINE  240", fill=DIM, font=font(26, True))
# faint scanlines for a screen feel
for yy in range(0, H, 4): d.line([(0, yy), (W, yy)], fill=(0, 0, 0), width=1)
im = im.filter(ImageFilter.GaussianBlur(0.6)); im.save(OUT + "/gm_screen_discord.png")
# vertical music-visualizer monitor
V = Image.new("RGB", (1080, 1920), (12, 6, 20)); v = ImageDraw.Draw(V); r = random.Random(5)
for i in range(24):
    h = r.randint(180, 1300); x = 40 + i * 42; col = (int(255 - i * 3), int(70 + i * 5), int(60 + i * 6))
    v.rectangle((x, 1750 - h, x + 30, 1750), fill=col)
v.text((90, 120), "NOW PLAYING", fill=(255, 140, 70), font=font(54, True)); v.text((90, 200), "through flames - live set", fill=(235, 235, 245), font=font(44))
V.save(OUT + "/gm_screen_music.png"); print("ok")
