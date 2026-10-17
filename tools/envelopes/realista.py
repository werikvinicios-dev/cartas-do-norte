#!/usr/bin/env python3
"""Envelope realista: papel com fibras e relevo iluminados, dobras com espessura e sombra, aba em perspectiva,
lacre de cera com volume e brilho, carimbado com o emblema de Cartas do Norte em relevo, sobre uma mesa de madeira.

Uso:  python3 tools/envelopes/realista.py video saida.mp4
      python3 tools/envelopes/realista.py still saida.png [t]
      python3 tools/envelopes/realista.py som efeitos.wav
      python3 tools/envelopes/realista.py export assets/experience
"""
import sys, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
S = 1080; FPS = 30; DUR = 8.0
EW, EH = 720, 470; FH = int(EH * .58)          # envelope e altura da aba
GW, GH = 900, 900                              # tela do grupo (envelope + aba aberta + carta)
OX, OY = (GW - EW) // 2, 330                   # envelope dentro do grupo
LIGHT = np.array([-.45, -.6, .66]); LIGHT = LIGHT / np.linalg.norm(LIGHT)

def fbm(h, w, seed, scales=(4, 8, 16, 32, 64)):
    rng = np.random.default_rng(seed); out = np.zeros((h, w)); tot = 0
    for i, s in enumerate(scales):
        g = rng.random((max(2, h // s + 2), max(2, w // s + 2)))
        up = ndimage.zoom(g, (h / (g.shape[0] - 1), w / (g.shape[1] - 1)), order=3)[:h, :w]
        wt = 1 / (i + 1) ** .9; out += up * wt; tot += wt
    out /= tot; return (out - out.min()) / (out.max() - out.min() + 1e-9)

def poly_mask(h, w, pts, ss=3):
    im = Image.new('L', (w * ss, h * ss), 0); ImageDraw.Draw(im).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    return np.asarray(im.resize((w, h), Image.LANCZOS)) / 255

def shade_height(hgt, strength=1.0):
    gy, gx = np.gradient(hgt * strength)
    n = np.dstack([-gx, -gy, np.ones_like(hgt)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    return np.clip(n @ LIGHT, 0, 1), n

PAPER = np.array([238, 228, 204]) / 255
def paper_sheet(h, w, seed, tint=(1, 1, 1), age=.5):
    """Papel: fibras (relevo iluminado), variação de cor, manchas de chá nas bordas e pontos de foxing."""
    rng = np.random.default_rng(seed)
    fib = fbm(h, w, seed, (1, 2, 3)) * .6 + ndimage.gaussian_filter(rng.random((h, w)), (0.6, 3.5)) * .8
    lum, _ = shade_height(fib, 3.2)
    low = fbm(h, w, seed + 1, (50, 120, 240))
    yy, xx = np.mgrid[0:h, 0:w]; edge = np.minimum.reduce([xx, yy, w - 1 - xx, h - 1 - yy]).astype(float)
    stain = np.exp(-edge / 26) * (.4 + .6 * fbm(h, w, seed + 2, (20, 45))) * age
    col = PAPER * np.array(tint) * (.95 + .07 * low[..., None])
    col = col * (1 - stain[..., None] * np.array([.12, .2, .32]))
    for _ in range(int(14 * age)):
        cy, cx = rng.integers(0, h), rng.integers(0, w); r = rng.uniform(1.5, 6)
        spot = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)) * rng.uniform(.08, .25)
        col = col * (1 - spot[..., None] * np.array([.15, .3, .45]))
    col = col * (.86 + .2 * lum[..., None])
    return np.clip(col, 0, 1)

def edges_lit(alpha, rgb, width=2.2, hi=.22, lo=.28):
    """Espessura do papel: a borda voltada para a luz clareia, a oposta escurece."""
    gy, gx = np.gradient(ndimage.gaussian_filter(alpha, 1.0))
    mag = np.hypot(gx, gy) + 1e-9; facing = -(gx * LIGHT[0] + gy * LIGHT[1]) / mag
    band = np.clip(mag * width * 2, 0, 1)
    out = rgb * (1 + band[..., None] * np.where(facing > 0, hi * facing, lo * facing)[..., None])
    return np.clip(out, 0, 1)

def drop_shadow(alpha, dx=6, dy=9, blur=7, k=.35):
    sh = ndimage.shift(ndimage.gaussian_filter(alpha, blur), (dy, dx), order=1)
    return np.clip(sh * k, 0, 1)

def over(dst, src_rgb, src_a, x=0, y=0):
    h, w = src_a.shape; H, W = dst.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    a = src_a[y0 - y:y1 - y, x0 - x:x1 - x, None]
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + src_rgb[y0 - y:y1 - y, x0 - x:x1 - x] * a

def darken(dst, sh, x=0, y=0):
    h, w = sh.shape; dst[y:y + h, x:x + w] *= (1 - sh[..., None])

def TTF(name):
    out = Path('/tmp') / f'{name}.ttf'
    if not out.exists():
        from fontTools.ttLib import TTFont
        f = TTFont(ROOT / 'assets/fonts' / {'pinyon': 'pinyon-script.woff2', 'corm': 'cormorant-400-italic.woff2'}[name]); f.flavor = None; f.save(out)
    return out

# ── peças ───────────────────────────────────────────────────────
def build():
    L = {}
    L['back'] = paper_sheet(EH, EW, 1, (.96, .95, .93), .8)                     # costas internas (mais sombra)
    pts_side_l = [(0, 0), (EW * .5, EH * .56), (0, EH)]; pts_side_r = [(EW, 0), (EW * .5, EH * .56), (EW, EH)]
    pts_bottom = [(0, EH), (EW * .5, EH * .44), (EW, EH)]
    L['side_a'] = np.maximum(poly_mask(EH, EW, pts_side_l), poly_mask(EH, EW, pts_side_r))
    L['side'] = edges_lit(L['side_a'], paper_sheet(EH, EW, 2, (.985, .98, .97), .6) * .97)
    L['bot_a'] = poly_mask(EH, EW, pts_bottom)
    L['bot'] = edges_lit(L['bot_a'], paper_sheet(EH, EW, 3, (1, 1, 1), .6))
    L['flap_a'] = poly_mask(FH, EW, [(0, 0), (EW, 0), (EW * .5, FH)])
    fl = paper_sheet(FH, EW, 4, (1, .995, .99), .55)
    # o nome no envelope, a tinta sépia
    im = Image.fromarray((fl * 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
    L['flap'] = edges_lit(L['flap_a'], np.asarray(im) / 255)
    L['flap_in'] = paper_sheet(FH, EW, 5, (.93, .92, .9), .4)
    L['body_a'] = np.ones((EH, EW))
    # carta
    lw, lh = int(EW * .9), int(EH * .92)
    lt = paper_sheet(lh, lw, 6, (1.03, 1.03, 1.03), .25)
    im = Image.fromarray((np.clip(lt, 0, 1) * 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
    for k in range(6): dr.line([(40, 128 + k * 46), (lw - 40, 128 + k * 46)], fill=(170, 176, 182), width=1)
    ink = (58, 40, 26)
    dr.text((46, 34), 'Miqueias,', font=ImageFont.truetype(str(TTF('pinyon')), 64), fill=ink)
    f2 = ImageFont.truetype(str(TTF('pinyon')), 32)
    dr.text((56, 100), 'Se você está lendo isto, voltou.', font=f2, fill=ink)
    dr.text((56, 146), 'Não vou pedir que confie em mim.', font=f2, fill=ink)
    im = im.filter(ImageFilter.GaussianBlur(.45))
    L['letter'] = np.asarray(im) / 255; L['letter_a'] = np.ones((lh, lw))
    L['seal'], L['seal_a'], L['seal_h'] = seal_parts()
    L['desk'] = desk()
    return L

def desk():
    """Mesa de nogueira: veios longos na horizontal, faixas de cor, poros finos e luz suave do alto à esquerda."""
    rng = np.random.default_rng(11); yy, xx = np.mgrid[0:S, 0:S]
    sway = fbm(S, S, 9, (120, 260)) * 18                                  # o veio ondula de leve
    grain = ndimage.gaussian_filter(rng.random((S, S)), (1.0, 90))
    bands = ndimage.gaussian_filter(rng.random((S, S)), (14, 300))
    grain = ndimage.map_coordinates(grain, [yy + sway, xx], order=1, mode='reflect')
    bands = ndimage.map_coordinates(bands, [yy + sway, xx], order=1, mode='reflect')
    norm = lambda a: (a - a.min()) / (a.max() - a.min() + 1e-9)
    g, b = norm(grain), norm(bands)
    pores = ndimage.gaussian_filter(rng.random((S, S)), (.4, 3)) ; pores = norm(pores)
    v = .55 + .3 * g ** 1.5 + .28 * b - .08 * (pores > .8)
    dark = np.array([46, 28, 17]) / 255; light = np.array([104, 66, 40]) / 255
    col = dark + (light - dark) * np.clip(v - .35, 0, 1)[..., None]
    lum, _ = shade_height(g * .5 + pores * .2, 3)
    col *= (.85 + .25 * lum[..., None])
    spot = np.exp(-(((xx - S * .42) / (S * .6)) ** 2 + ((yy - S * .42) / (S * .55)) ** 2))
    return np.clip(col * (.5 + .7 * spot[..., None]), 0, 1)

def seal_parts(R=78):
    k = R / 78
    """Lacre: altura (gota com bordas irregulares, centro achatado pelo sinete, emblema em relevo), luz de Phong."""
    n = 2 * R + 60; c = n / 2; yy, xx = np.mgrid[0:n, 0:n]; ang = np.arctan2(yy - c, xx - c); r = np.hypot(xx - c, yy - c)
    rng = np.random.default_rng(31)
    bumps = (sum(rng.uniform(1.5, 4.5) * np.cos(f * ang + rng.uniform(0, 6)) for f in (2, 3, 5, 7)) + 7 * np.clip(np.cos(ang - 2.2), 0, 1) ** 18 + 5 * np.clip(np.cos(ang + .6), 0, 1) ** 24) * k   # bordas moles e duas escorridas
    edge = R + bumps - r; m = np.clip(edge / (1.5 * k) + .5, 0, 1)
    dome = np.sqrt(np.clip(1 - (r / (R + bumps)) ** 2, 0, 1))
    hgt = dome * 14 * k
    face = R * .72
    pressed = np.clip((face - r) / 3, 0, 1)
    hgt = hgt * (1 - pressed) + pressed * 9.5 * k + np.exp(-((r - face - 3 * k) / (3.5 * k)) ** 2) * 3.0 * k        # rebordo empurrado pelo sinete
    emb = Image.open(ROOT / 'assets/branding/emblem-gold.webp').split()[-1]
    es = int(face * 1.72); emb = emb.resize((int(es * 831 / 898), es), Image.LANCZOS)
    E = np.zeros((n, n)); ex, ey = int(c - emb.size[0] / 2), int(c - emb.size[1] / 2)
    E[ey:ey + emb.size[1], ex:ex + emb.size[0]] = np.asarray(emb) / 255
    E = ndimage.gaussian_filter(E, .9 * k) * pressed
    hgt += E * 2.2 * k
    return None, m, hgt

def light_seal(hgt, m, gloss=1.0, light=LIGHT, base=(118, 14, 22)):
    gy, gx = np.gradient(hgt); nrm = np.dstack([-gx, -gy, np.ones_like(hgt) * 1.6]); nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    dif = np.clip(nrm @ light, 0, 1); Hh = light + np.array([0, 0, 1.]); Hh /= np.linalg.norm(Hh)
    spec = np.clip(nrm @ Hh, 0, 1) ** 60 * .9 * gloss + np.clip(nrm @ Hh, 0, 1) ** 12 * .12 * gloss
    b = np.array(base) / 255
    col = b * (.28 + .95 * dif[..., None]) + spec[..., None] * np.array([1, .9, .85])
    col += np.array([.18, .02, .03]) * np.clip(1 - hgt / 10, 0, 1)[..., None] * .5          # translucidez na borda fina
    return np.clip(col, 0, 1)

# ── geometria da aba em perspectiva ─────────────────────────────
def homography(src, dst):
    A = []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
    b = [c for p in src for c in p]
    return np.linalg.solve(np.array(A, float), np.array(b, float))

def flap_image(L, theta):
    """A aba gira em torno da dobra superior; projeção com perspectiva leve. Devolve rgb, alfa e o deslocamento y."""
    f = 2400.0; cy = FH / 2
    def proj(x, y):
        yy_ = y * np.cos(theta); z = y * np.sin(theta); k = f / (f - z)
        return ((x - EW / 2) * k + EW / 2, yy_ * k)
    corners = [(0, 0), (EW, 0), (EW, FH), (0, FH)]
    dstp = [proj(x, y) for x, y in corners]
    ys = [p[1] for p in dstp]; top = min(0, min(ys)); bot = max(ys)
    H = int(np.ceil(bot - top)) + 2
    dsh = [(x, y - top) for x, y in dstp]
    coeffs = homography(corners, dsh)
    front = np.cos(theta) > 0
    rgb = L['flap'] if front else L['flap_in']
    rgba = np.dstack([rgb, L['flap_a']])
    im = Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA').transform((EW, max(1, H)), Image.PERSPECTIVE, tuple(coeffs), Image.BICUBIC)
    a = np.asarray(im) / 255
    nz = np.cos(theta); lit = .78 + .3 * abs(nz) if front else .62 + .3 * abs(nz)
    return a[..., :3] * lit, a[..., 3], int(round(top))

# ── quadro ──────────────────────────────────────────────────────
def clamp(x, a=0., b=1.): return min(b, max(a, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def eo(x): return 1 - (1 - x) ** 3
def eio(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2

def group(L, t):
    rgb = np.zeros((GH, GW, 3)); a = np.zeros((GH, GW))
    def put(src, sa, x, y, shadow=None):
        if shadow is not None: darken(rgb, shadow, x, y)
        over(rgb, src, sa, x, y)
        h, w = sa.shape; a[max(0, y):y + h, max(0, x):x + w] = np.maximum(a[max(0, y):y + h, max(0, x):x + w], sa[max(0, -y):, max(0, -x):][:min(h, GH - y), :min(w, GW - x)])
    theta = np.pi * .96 * eio(seg(t, 4.35, 5.4))
    lift = eo(seg(t, 5.35, 6.7))
    # costas internas
    put(L['back'], L['body_a'], OX, OY)
    # aba aberta fica atrás da carta
    if np.cos(theta) <= 0:
        fr, fa, top = flap_image(L, theta); put(fr, fa, OX, OY + top)
    # carta
    lh, lw = L['letter_a'].shape; ly = OY + int(EH * .05) - int(lift * EH * .66)
    sh = drop_shadow(L['letter_a'], 0, 6, 8, .25 * (1 if lift > 0 else 0))
    put(L['letter'], L['letter_a'], OX + (EW - lw) // 2, ly, sh if lift > .02 else None)
    # dobras da frente (sobre a carta)
    put(L['side'], L['side_a'], OX, OY, drop_shadow(L['side_a'], 4, 6, 6, .22))
    put(L['bot'], L['bot_a'], OX, OY, drop_shadow(L['bot_a'], 3, -5, 6, .25))
    if np.cos(theta) > 0:
        fr, fa, top = flap_image(L, theta)
        put(fr, fa, OX, OY + top, drop_shadow(fa, 5, 9 + int(12 * np.sin(theta)), 7 + 10 * np.sin(theta), .3))
    # lacre
    t_drop, t_press, t_brk = 1.45, 2.2, 3.95
    if t >= t_drop and t < t_brk + .6:
        m, hgt = L['seal_a'], L['seal_h']; n = m.shape[0]
        grow = eo(seg(t, t_drop, t_drop + .45)); press = seg(t, t_press, t_press + .14)
        R = 78; c = n / 2; yy, xx = np.mgrid[0:n, 0:n]; r = np.hypot(xx - c, yy - c)
        molten = np.sqrt(np.clip(1 - (r / (R * .95)) ** 2, 0, 1)) * 16
        h = molten * (1 - press) + hgt * press
        sw = .35 + .65 * grow
        ang = .3 * np.sin(t * .9)                            # a luz passeia devagar sobre a cera
        lt = np.array([LIGHT[0] * np.cos(ang) - LIGHT[1] * np.sin(ang), LIGHT[0] * np.sin(ang) + LIGHT[1] * np.cos(ang), LIGHT[2]])
        col = light_seal(h, m, 1.4 - .4 * press, lt / np.linalg.norm(lt))
        rgba = np.dstack([col, m])
        im = Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA'); k = max(1, int(n * sw)); im = im.resize((k, k), Image.LANCZOS)
        cx, cy = OX + EW // 2, OY + FH - 4
        if t < t_brk:
            sa = np.asarray(im) / 255; put(sa[..., :3], sa[..., 3], cx - k // 2, cy - k // 2, drop_shadow(sa[..., 3], 3, 5, 4, .45))
        else:
            e = eo(seg(t, t_brk, t_brk + .5)); fade = 1 - seg(t, t_brk + .3, t_brk + .6)
            sa = np.asarray(im) / 255; half = k // 2; jag = (np.sin(np.arange(k) / 5) * 5 + np.sin(np.arange(k) / 2.3) * 2).astype(int)
            for side, sgn in ((0, -1), (1, 1)):
                part = sa.copy()
                for y in range(k):
                    if side == 0: part[y, half + jag[y]:, 3] = 0
                    else: part[y, :half + jag[y], 3] = 0
                pim = Image.fromarray((part * 255).astype(np.uint8), 'RGBA').rotate(-sgn * e * 22, Image.BICUBIC, expand=True)
                pa = np.asarray(pim) / 255; pa[..., 3] *= fade
                put(pa[..., :3], pa[..., 3], cx - pa.shape[1] // 2 + int(sgn * e * 40), cy - pa.shape[0] // 2 + int(e * 30), drop_shadow(pa[..., 3], 3, 5, 4, .4 * fade))
    return rgb, a

def frame(L, t):
    img = L['desk'].copy()
    rgb, a = group(L, t)
    # entrada: desliza sobre a mesa e assenta
    p = eo(seg(t, 0, 1.3)); ang = -9 * (1 - p) - 2.2; dx = int(-260 * (1 - p)); dy = int(140 * (1 - p))
    rgba = np.dstack([rgb, a])
    im = Image.fromarray((np.clip(rgba, 0, 1) * 255).astype(np.uint8), 'RGBA').rotate(ang, Image.BICUBIC, center=(GW / 2, OY + EH / 2))
    g = np.asarray(im) / 255
    zoom = 1 + .035 * seg(t, 5.5, 8)
    if zoom != 1:
        gim = Image.fromarray((g * 255).astype(np.uint8), 'RGBA'); k = int(GW * zoom); gim = gim.resize((k, k), Image.LANCZOS); g = np.asarray(gim) / 255
    x, y = (S - g.shape[1]) // 2 + dx, (S - g.shape[0]) // 2 + 40 + dy
    sh = ndimage.gaussian_filter(g[..., 3], 14 - 6 * p) * (.55 + .1 * (1 - p))
    darken(img, ndimage.shift(sh, (16 + 20 * (1 - p), 12 + 16 * (1 - p)), order=1)[:min(S - y, sh.shape[0]) if y >= 0 else None], max(0, x), max(0, y)) if False else None
    shadow_full = np.zeros((S, S)); hh, ww = sh.shape
    y0, x0 = y + 18 + int(18 * (1 - p)), x + 12 + int(14 * (1 - p))
    ys, xs = max(0, y0), max(0, x0); ye, xe = min(S, y0 + hh), min(S, x0 + ww)
    shadow_full[ys:ye, xs:xe] = sh[ys - y0:ye - y0, xs - x0:xe - x0]
    img *= (1 - shadow_full[..., None])
    over(img, g[..., :3], g[..., 3], x, y)
    vig = np.hypot(*np.mgrid[0:S, 0:S] - S / 2) / (S * .75); img *= (1 - .35 * vig ** 2)[..., None]
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)

def render(out):
    L = build()
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{S}x{S}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)): ff.stdin.write(frame(L, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('ok', out)

def sound(out):
    """Papel deslizando na mesa, a cera caindo, o sinete, o lacre partindo, a aba e a carta."""
    sys.path.insert(0, str(ROOT / 'tools/promo')); import promo_som as PS
    from scipy.io import wavfile
    SR = PS.SR; N = int(DUR * SR); fx = np.zeros((N, 2)); rng = np.random.default_rng(3)
    def add(t, y, pan=0.):
        i = int(t * SR); j = min(N, i + len(y)); fx[i:j, 0] += y[:j - i] * np.sqrt((1 - pan) / 2); fx[i:j, 1] += y[:j - i] * np.sqrt((1 + pan) / 2)
    n = int(1.2 * SR); tt = np.arange(n) / SR
    slide = PS.bp(rng.normal(0, 1, n), 300, 3000) * np.sin(np.pi * tt / 1.2) ** 1.5 * .08
    m = int(.5 * SR); tm = np.arange(m) / SR
    drip = (np.sin(2 * np.pi * 180 * tm * (1 + 2 * tm)) * np.exp(-tm * 14) * .25 + PS.bp(rng.normal(0, 1, m), 200, 1200) * np.exp(-tm * 10) * .2)
    add(0, slide, -.3); add(1.45, drip); add(2.2, PS.thock()); add(3.95, PS.crack(), .1); add(4.35, PS.rustle(.8), -.2); add(5.35, PS.rustle(1.1), .2)
    fx = fx / max(1e-9, np.max(np.abs(fx))) * .7
    wavfile.write(out, SR, (fx * 32767).astype(np.int16))

def export(dst):
    """Camadas para o site e para o vídeo promocional (assets/experience): costas, frente com as dobras, aba (frente e
    verso), folha, papel para os cartões e o lacre inteiro e em duas metades (mesma tela, para se encaixarem)."""
    dst = Path(dst); L = build()
    def save(rgb, a, name, q=90):
        Image.fromarray((np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)]) * 255).astype(np.uint8), 'RGBA').save(dst / name, quality=q, method=6)
    save(L['back'], L['body_a'], 'env-back.webp')
    # frente: dobras laterais e de baixo com as sombras que projetam
    rgb = np.zeros((EH, EW, 3)); a = np.zeros((EH, EW))
    for part, pa, sh in (('side', 'side_a', drop_shadow(L['side_a'], 4, 6, 6, .22)), ('bot', 'bot_a', drop_shadow(L['bot_a'], 3, -5, 6, .25))):
        a_new = a + sh * (1 - a); rgb = (rgb * a[..., None]) / np.maximum(a_new, 1e-6)[..., None]; a = a_new
        m = L[pa]; rgb = rgb * (1 - m[..., None]) + L[part] * m[..., None]; a = a * (1 - m) + m
    save(rgb, a, 'env-front.webp')
    fr, fa, _ = flap_image(L, 0.0); save(fr, fa, 'env-flap.webp')
    save(L['flap_in'] * .9, L['flap_a'], 'env-flap-in.webp')
    lt = paper_sheet(*L['letter_a'].shape, 6, (1.03, 1.03, 1.03), .25); save(lt, L['letter_a'], 'env-letter.webp')
    save(paper_sheet(800, 600, 7, (1, .99, .97), .7), np.ones((800, 600)), 'env-paper.webp')
    # lacre em alta: inteiro e metades
    R = 128; m, hgt = seal_parts(R)[1:]; col = light_seal(hgt, m); n = m.shape[0]; pad = (360 - n) // 2 if n < 360 else 0
    canvas = lambda x: np.pad(x, ((pad, 360 - n - pad), (pad, 360 - n - pad)) + ((0, 0),) * (x.ndim - 2)) if n < 360 else x
    C, M = canvas(col), canvas(m)
    save(C, M, 'wax-seal.webp', 92)
    k = M.shape[0]; jag = (k / 2 + np.sin(np.arange(k) / 9) * 8 + np.sin(np.arange(k) / 3.7) * 3).astype(int)
    left = M.copy(); right = M.copy()
    for y in range(k): left[y, jag[y]:] = 0; right[y, :jag[y]] = 0
    save(C, left, 'wax-seal-l.webp', 92); save(C, right, 'wax-seal-r.webp', 92)
    print('ok', dst)

if __name__ == '__main__':
    mode, out = sys.argv[1:3]
    if mode == 'still':
        Image.fromarray(frame(build(), float(sys.argv[3]) if len(sys.argv) > 3 else 3.2)).save(out)
    elif mode == 'export':
        export(out)
    elif mode == 'som':
        sound(out)
    else:
        render(out)
