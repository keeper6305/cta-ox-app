from PIL import Image, ImageDraw, ImageFilter
import math

S = 2048  # work at 4x of 512

def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))

def gradient(size, c1, c2, c3=None):
    # diagonal gradient, built small then upscaled (smooth)
    small = Image.new('RGB', (64, 64))
    px = small.load()
    for y in range(64):
        for x in range(64):
            t = (x + y) / 126.0
            if c3 is None:
                px[x, y] = lerp(c1, c2, t)
            else:
                if t < 0.55:
                    px[x, y] = lerp(c1, c2, t / 0.55)
                else:
                    px[x, y] = lerp(c2, c3, (t - 0.55) / 0.45)
    return small.resize((size, size), Image.BICUBIC)

def rounded_mask(size, radius):
    m = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m

def draw_mark(img, cx, cy, scale, o_color, x_color, ring_w, x_w, gap):
    """O ring + X glyph, centred at (cx, cy), overall width ~= 1.0*scale"""
    d = ImageDraw.Draw(img)
    r = 0.30 * scale
    o_cx = cx - 0.26 * scale
    # ring
    d.ellipse([o_cx - r, cy - r, o_cx + r, cy + r], outline=o_color, width=int(ring_w))
    # X bars
    x_cx = cx + 0.26 * scale
    h = r * 1.02
    d.line([x_cx - h, cy - h, x_cx + h, cy + h], fill=x_color, width=int(x_w))
    d.line([x_cx - h, cy + h, x_cx + h, cy - h], fill=x_color, width=int(x_w))
    # round caps
    for (px, py) in [(x_cx - h, cy - h), (x_cx + h, cy + h), (x_cx - h, cy + h), (x_cx + h, cy - h)]:
        rr = x_w / 2.0
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=x_color)

def spark(img, cx, cy, r, color):
    d = ImageDraw.Draw(img)
    # four-point star
    pts = []
    for i in range(8):
        ang = math.pi / 4 * i - math.pi / 2
        rad = r if i % 2 == 0 else r * 0.34
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=color)

IND1 = (79, 70, 229)     # #4F46E5 indigo
IND2 = (49, 46, 129)     # #312E81 deep indigo
VIO  = (124, 58, 237)    # #7C3AED violet
WHITE = (255, 255, 255, 255)
AMBER = (251, 191, 36, 255)

def base(size, radius_ratio, with_mark=True, scale_ratio=0.62):
    bg = gradient(size, IND1, VIO, IND2).convert('RGBA')
    # soft top-left sheen
    sheen = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sheen)
    ds.ellipse([-size * 0.35, -size * 0.55, size * 0.75, size * 0.45], fill=(255, 255, 255, 26))
    bg = Image.alpha_composite(bg, sheen)
    if with_mark:
        draw_mark(bg, size / 2.0, size / 2.0, size * scale_ratio,
                  WHITE, AMBER, size * 0.068, size * 0.076, 0)
        spark(bg, size * 0.815, size * 0.205, size * 0.045, WHITE)
    mask = rounded_mask(size, int(size * radius_ratio))
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    out.paste(bg, (0, 0), mask)
    return out

def save(img, path, px):
    img.resize((px, px), Image.LANCZOS).save(path, optimize=True)
    print(path, px)

# 512 any (rounded)
any512 = base(S, 0.235)
save(any512, 'site/icon-512.png', 512)
save(any512, 'site/icon-192.png', 192)
# maskable: full bleed, art in 66% safe zone
mask_src = Image.new('RGBA', (S, S))
g = gradient(S, IND1, VIO, IND2).convert('RGBA')
mask_src.paste(g, (0, 0))
sheen = Image.new('RGBA', (S, S), (0, 0, 0, 0))
ds = ImageDraw.Draw(sheen)
ds.ellipse([-S * 0.35, -S * 0.55, S * 0.75, S * 0.45], fill=(255, 255, 255, 26))
mask_src = Image.alpha_composite(mask_src, sheen)
draw_mark(mask_src, S / 2.0, S / 2.0, S * 0.42, WHITE, AMBER, S * 0.050, S * 0.056, 0)
spark(mask_src, S * 0.72, S * 0.30, S * 0.040, WHITE)
save(mask_src, 'site/icon-maskable-512.png', 512)
# apple touch 180 (square, no radius)
apple = base(S, 0.0)
save(apple, 'site/apple-touch-icon.png', 180)
# favicon 32: bold simplified (square bg, thicker strokes)
fav = gradient(S, IND1, VIO, IND2).convert('RGBA')
draw_mark(fav, S / 2.0, S / 2.0, S * 0.80, WHITE, AMBER, S * 0.115, S * 0.125, 0)
save(fav, 'site/favicon-32.png', 32)
save(fav, 'site/favicon-192.png', 192)
