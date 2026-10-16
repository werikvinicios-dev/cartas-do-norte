#!/usr/bin/env python3
"""Envelopes em aquarela, pintados por código, com animação: a tinta se espalha no papel, o lacre carimba, se parte,
a aba abre e a carta sobe.

Variantes: A (sépia, lacre carmim), B (azul do Norte, lacre ocre), C (carta náutica, lacre vinho).
Uso:  python3 tools/envelopes/aquarela.py video A saida.mp4
      python3 tools/envelopes/aquarela.py still A saida.png [t]
      python3 tools/envelopes/aquarela.py som - efeitos.wav
"""
import sys, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
S = 1080; FPS = 30; DUR = 8.0
EW, EH = 760, 500; EX, EY = (S - EW) // 2, 380          # envelope: canto superior esquerdo
FLAP_H = int(EH * .56)

def fbm(h, w, seed, scales=(4, 8, 16, 32, 64), weights=None):
    rng = np.random.default_rng(seed); out = np.zeros((h, w)); tot = 0
    weights = weights or [1 / (i + 1) ** .9 for i in range(len(scales))]
    for s, wt in zip(scales, weights):
        g = rng.random((max(2, h // s + 2), max(2, w // s + 2)))
        up = ndimage.zoom(g, (h / (g.shape[0] - 1), w / (g.shape[1] - 1)), order=3)[:h, :w]
        out += up * wt; tot += wt
    out /= tot; return (out - out.min()) / (out.max() - out.min() + 1e-9)

def poly_mask(h, w, pts, ss=3):
    im = Image.new('L', (w * ss, h * ss), 0); ImageDraw.Draw(im).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    return np.asarray(im.resize((w, h), Image.LANCZOS)) / 255

def wash(mask, pigment, seed, strength=.55, edge=.35, gran=.18, blooms=4, var=.35):
    """Densidade de pigmento numa forma, imitando aquarela: valor irregular, borda molhada dura, granulação,
    "couve-flor" (backruns) com contorno escuro, e a luz vinda do alto à esquerda deixando o papel aparecer."""
    h, w = mask.shape; rng = np.random.default_rng(seed)
    inside = ndimage.distance_transform_edt(mask > .5)
    low = fbm(h, w, seed, (60, 140, 260)); grain = fbm(h, w, seed + 1, (2, 3, 4)); mid = fbm(h, w, seed + 2, (10, 22, 40))
    yy, xx = np.mgrid[0:h, 0:w]
    light = np.clip(1 - .55 * np.exp(-(((xx / w) - .18) ** 2 + ((yy / h) - .15) ** 2) / .09), .35, 1)
    d = strength * (.35 + 1.1 * var * low + (1 - var) * .5) * light
    d += edge * np.exp(-inside / 3.5) + .5 * edge * np.exp(-inside / 14)
    back = fbm(h, w, seed + 3, (40, 80, 150)); bk = back > .8
    rim = bk & ~ndimage.binary_erosion(bk, iterations=2)
    d = np.where(bk, d * .72, d) + rim * .14 * strength
    d *= 1 + gran * 2.2 * (grain - .5)
    d += .07 * (mid - .5)
    ys, xs = np.nonzero(mask > .9)
    for _ in range(blooms if len(xs) else 0):
        k = rng.integers(len(xs)); cx, cy = xs[k], ys[k]; r = rng.uniform(22, 60)
        rr = np.hypot(xx - cx, yy - cy) / (r * (1 + .25 * (fbm(h, w, seed + 9 + _, (8, 16)) - .5)))
        d = d * np.where(rr < 1, .6 + .4 * rr ** 3, 1) + .22 * strength * np.exp(-((rr - 1) / .07) ** 2)
    return np.clip(d, 0, 1) * mask

def ragged(mask, seed, amp=3.0):
    """Borda irregular de aquarela: desloca o contorno com ruído."""
    inside = ndimage.distance_transform_edt(mask > .5) - ndimage.distance_transform_edt(mask <= .5)
    n = fbm(*mask.shape, seed, (6, 14, 30)) - .5
    return np.clip((inside + n * amp * 2 + .5), 0, 1)

def paint(d, pigment, paper, pigment2=None, seed=0):
    """Modelo subtrativo: o papel filtrado pelo pigmento conforme a densidade; um segundo pigmento se mistura em manchas."""
    pig = np.array(pigment, float) / 255; pap = np.array(paper, float) / 255
    if pigment2 is not None:
        mix = fbm(*d.shape, seed + 99, (50, 110, 220))[..., None] ** 1.4
        pig = pig * (1 - mix) + np.array(pigment2, float) / 255 * mix
    return pap * (1 - d[..., None] * (1 - pig))

def ink_lines(h, w, segs, color, seed, width=2.2, alpha=.85):
    """Traço de nanquim feito à mão: duas passadas levemente desalinhadas, espessura variável."""
    rng = np.random.default_rng(seed); ss = 3
    im = Image.new('L', (w * ss, h * ss), 0); dr = ImageDraw.Draw(im)
    for (x0, y0), (x1, y1) in segs:
        for p in range(2):
            n = 24; pts = []
            for i in range(n + 1):
                t = i / n; jx, jy = rng.normal(0, .6, 2)
                pts.append(((x0 + (x1 - x0) * t + jx) * ss, (y0 + (y1 - y0) * t + jy) * ss))
            wd = max(1, int(width * ss * (1 if p == 0 else .55)))
            dr.line(pts, fill=int(255 * (1 if p == 0 else .55)), width=wd, joint='curve')
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(ss * .5)).resize((w, h), Image.LANCZOS)) / 255 * alpha
    return a

VARIANTS = {
 'A': dict(nome='A · Sépia e lacre carmim', paper=(247, 240, 224), body=(178, 120, 64), pocket=(166, 106, 54), flap=(150, 92, 46), mix=(122, 96, 70),
           ink=(84, 52, 26), seal=(150, 28, 32), seal_hi=(214, 92, 84), lining='topo', lining_pig=(150, 110, 70), bg=(240, 232, 214), dens=(.26, .34, .42)),
 'B': dict(nome='B · Azul do Norte e lacre ocre', paper=(245, 240, 229), body=(46, 86, 140), pocket=(36, 70, 122), flap=(28, 56, 104), mix=(70, 110, 120),
           ink=(24, 34, 56), seal=(178, 128, 40), seal_hi=(240, 204, 120), lining='rosa', lining_pig=(60, 94, 140), bg=(236, 231, 220), dens=(.42, .52, .6)),
 'C': dict(nome='C · Carta náutica e lacre vinho', paper=(248, 243, 231), body=(120, 158, 176), pocket=(104, 146, 166), flap=(88, 130, 152), mix=(196, 170, 120),
           ink=(70, 56, 40), seal=(110, 22, 34), seal_hi=(190, 80, 90), lining='rota', lining_pig=(70, 110, 130), bg=(238, 233, 222), dens=(.2, .26, .32)),
}

def rgba(rgb, a):
    return np.dstack([rgb, a])

def build(v):
    V = VARIANTS[v]; P = V['paper']; L = {}
    H_, W_ = EH, EW
    seed = {'A': 11, 'B': 23, 'C': 37}[v]
    # costas internas (forro), visíveis quando a aba abre
    m = ragged(poly_mask(H_, W_, [(0, 0), (W_, 0), (W_, H_), (0, H_)]), seed, 1.5)
    lin = np.zeros((H_, W_)); yy, xx = np.mgrid[0:H_, 0:W_]
    if V['lining'] == 'topo':
        f = fbm(H_, W_, seed + 5, (60, 120, 240)); lin = (np.abs(np.sin(f * 40)) < .12) * .45 + .12
    elif V['lining'] == 'rosa':
        cx, cy = W_ / 2, H_ * .42; ang = np.arctan2(yy - cy, xx - cx); r = np.hypot(xx - cx, yy - cy)
        star = (r < 150 * (.25 + .75 * np.abs(np.cos(2 * ang)) ** 6)) * .5 + (np.abs(r - 160) < 2) * .5 + (np.abs(r - 172) < 1.2) * .35
        lin = ndimage.gaussian_filter(star.astype(float), 1.2) + .1
    else:
        f = fbm(H_, W_, seed + 5, (80, 160)); coast = np.abs(f - .5) < .012
        dots = ((xx // 14 + yy // 14) % 2 == 0) & (np.abs(yy - (H_ * .3 + 90 * np.sin(xx / 120))) < 2.5)
        lin = ndimage.gaussian_filter((coast * .7 + dots * .8).astype(float), .8) + .14
    d = np.clip(wash(m, V['lining_pig'], seed + 6, strength=.12, edge=.15, blooms=2) + lin * .55, 0, 1) * m
    L['back'] = rgba(paint(d, V['lining_pig'], P), m)
    # bolso (dobras laterais e de baixo)
    pk = [(0, H_), (0, H_ * .36), (W_ * .5, H_ * .7), (W_, H_ * .36), (W_, H_)]
    m = ragged(poly_mask(H_, W_, pk), seed + 7, 2.5)
    d = wash(m, V['pocket'], seed + 8, strength=V['dens'][1], edge=.32, blooms=3)
    if v == 'C':   # costa e rota pintadas na frente
        cx, cy = W_ * .16, H_ * .78; ang = np.arctan2(yy - cy, xx - cx); r = np.hypot(xx - cx, yy - cy)   # pequena rosa dos ventos a nanquim
        rose = (r < 54 * (.12 + .88 * np.abs(np.cos(2 * ang)) ** 16)) * .55 + (np.abs(r - 60) < 1.3) * .6 + (np.abs(r - 66) < .9) * .4
        d = np.clip(d + ndimage.gaussian_filter(rose.astype(float), .7) * m, 0, 1)
        route = (np.abs(yy - (H_ * .82 - 70 * np.sin(xx / 150 + .5))) < 2.4) & ((xx // 12) % 2 == 0) & (xx > W_ * .3)
        d = np.clip(d + ndimage.gaussian_filter(route.astype(float), .7) * .7 * m, 0, 1)
    L['pocket'] = rgba(paint(d, V['pocket'], P, V['mix'], seed + 8), m)
    L['pocket_ink'] = ink_lines(H_, W_, [((0, H_ * .36), (W_ * .5, H_ * .7)), ((W_ * .5, H_ * .7), (W_, H_ * .36))], V['ink'], seed + 10)
    # aba (frente e verso)
    fh = FLAP_H
    m = ragged(poly_mask(fh, W_, [(0, 0), (W_, 0), (W_ * .5, fh)]), seed + 11, 2.5)
    d = wash(m, V['flap'], seed + 12, strength=V['dens'][2], edge=.38, blooms=3)
    L['flap'] = rgba(paint(d, V['flap'], P, V['mix'], seed + 12), m)
    L['flap_ink'] = ink_lines(fh, W_, [((2, 2), (W_ * .5, fh - 2)), ((W_ * .5, fh - 2), (W_ - 2, 2))], V['ink'], seed + 13)
    d2 = np.clip(wash(m, V['lining_pig'], seed + 14, strength=.1, edge=.12, blooms=1), 0, 1)
    L['flap_in'] = rgba(paint(d2, V['lining_pig'], P), m)
    # corpo (a frente inteira por baixo das dobras)
    m = ragged(poly_mask(H_, W_, [(0, 0), (W_, 0), (W_, H_), (0, H_)]), seed + 15, 2.0)
    d = wash(m, V['body'], seed + 16, strength=V['dens'][0], edge=.3, blooms=4)
    L['body'] = rgba(paint(d, V['body'], P, V['mix'], seed + 16), m)
    L['body_ink'] = ink_lines(H_, W_, [((1, 1), (W_ - 1, 1)), ((W_ - 1, 1), (W_ - 1, H_ - 1)), ((W_ - 1, H_ - 1), (1, H_ - 1)), ((1, H_ - 1), (1, 1))], V['ink'], seed + 17, 1.8, .6)
    # carta
    lw, lh = int(W_ * .86), int(H_ * .9)
    m = ragged(poly_mask(lh, lw, [(0, 0), (lw, 0), (lw, lh), (0, lh)]), seed + 18, 1.2)
    d = wash(m, (200, 180, 150), seed + 19, strength=.06, edge=.18, blooms=1)
    rgb = paint(d, (200, 180, 150), (252, 248, 238))
    im = Image.fromarray((rgb * 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
    for k in range(5): dr.line([(46, 150 + k * 52), (lw - 46, 150 + k * 52)], fill=(176, 188, 196), width=1)
    font = ImageFont.truetype(str(TTF('pinyon')), 70); dr.text((52, 40), 'Miqueias,', font=font, fill=tuple(V['ink']))
    small = ImageFont.truetype(str(TTF('pinyon')), 34)
    for k, txt in enumerate(['Se você está lendo isto, voltou.', 'Não vou pedir que confie em mim.']): dr.text((60, 112 + 52 * (k + 1) - 26), txt, font=small, fill=tuple(int(c * .9) for c in V['ink']))
    L['letter'] = rgba(np.asarray(im) / 255, m)
    # lacre
    L['seal'] = seal(V, seed + 20)
    # mapas de revelação (a tinta se espalha a partir de um ponto, com ruído)
    for k, (ox, oy) in {'body': (.15, .3), 'pocket': (.85, .9), 'flap': (.5, .1)}.items():
        h, w = L[k].shape[:2]; yy2, xx2 = np.mgrid[0:h, 0:w]
        dist = np.hypot(xx2 - ox * w, yy2 - oy * h) / np.hypot(w, h)
        L[k + '_rev'] = np.clip(dist * 1.25 + (fbm(h, w, seed + 30 + len(k), (20, 50, 100)) - .5) * .5, 0, 1)
    return L

def TTF(name):
    out = Path('/tmp') / f'{name}.ttf'
    if not out.exists():
        from fontTools.ttLib import TTFont
        f = TTFont(ROOT / 'assets/fonts' / {'pinyon': 'pinyon-script.woff2', 'corm': 'cormorant-400-italic.woff2', 'news': 'newsreader.woff2'}[name]); f.flavor = None; f.save(out)
    return out

def seal(V, seed, R=74):
    n = 2 * R + 40; c = n / 2; yy, xx = np.mgrid[0:n, 0:n]; ang = np.arctan2(yy - c, xx - c); r = np.hypot(xx - c, yy - c)
    rng = np.random.default_rng(seed); bumps = sum(rng.uniform(2, 5) * np.cos(k * ang + rng.uniform(0, 6)) for k in (5, 7, 11))
    edge = R + bumps - r; m = np.clip(edge + .5, 0, 1)
    d = .82 + .18 * fbm(n, n, seed, (5, 10, 20)) + .3 * np.exp(-edge / 4)
    well = np.clip(R * .7 - r, 0, None); d -= .12 * np.clip(well / 6, 0, 1)                 # o centro afundado pelo sinete
    ring = np.exp(-((r - R * .7) / 1.8) ** 2); d += .22 * ring
    big = R * .56 * (.16 + .84 * np.abs(np.cos(2 * ang)) ** 14); small = R * .38 * (.2 + .8 * np.abs(np.cos(2 * ang + np.pi / 4)) ** 14)
    star = np.clip(np.maximum(big, small) - r + .5, 0, 1)
    shade = np.clip(np.cos(ang + 2.4), 0, 1) * star                                       # facetas da estrela: um lado na sombra
    d = d + .28 * star * .6 + .2 * shade
    rgb = paint(np.clip(d, 0, 1), V['seal'], V['paper'])
    rgb *= (1 - .25 * np.clip(np.cos(ang + 2.4) * (r / R), 0, 1)[..., None] * m[..., None])     # volume da cera
    hi = np.exp(-(((xx - c + R * .38) / (R * .22)) ** 2 + ((yy - c + R * .42) / (R * .1)) ** 2)) * .6
    rgb = rgb + hi[..., None] * (np.array(V['seal_hi']) / 255 - rgb)
    return rgba(np.clip(rgb, 0, 1), m)

def over(dst, src, x, y, alpha=1.0):
    """Compõe src (RGBA float) sobre dst (RGB float) na posição (x,y), com recorte nas bordas."""
    h, w = src.shape[:2]; H, W = dst.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; a = s[..., 3:4] * alpha
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a

def multiply(dst, src, x, y, alpha=1.0):
    """Aquarela é transparente: as camadas se multiplicam sobre o que está embaixo."""
    h, w = src.shape[:2]; s = src[..., :3]; a = src[..., 3:4] * alpha
    dst[y:y + h, x:x + w] = dst[y:y + h, x:x + w] * (1 - a + a * s)

def clamp(x, a=0., b=1.): return min(b, max(a, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def eo(x): return 1 - (1 - x) ** 3
def eio(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2

def reveal(layer, rev, p):
    """Mostra a camada onde o mapa de revelação já foi alcançado; a frente da tinta fica mais escura (borda molhada)."""
    if p >= 1: return layer
    if p <= 0: return None
    edge = np.clip((p * 1.15 - rev) / .06, 0, 1)
    out = layer.copy(); out[..., 3] *= edge
    wet = np.exp(-((p * 1.15 - rev) / .03) ** 2) * (edge > 0)
    out[..., :3] *= (1 - .18 * wet[..., None])
    return out

def background(V):
    g = fbm(S, S, 3, (3, 6, 12)); low = fbm(S, S, 4, (90, 200))
    bg = np.array(V['bg'], float) / 255 * (.94 + .06 * low[..., None]) * (.97 + .05 * g[..., None])
    yy, xx = np.mgrid[0:S, 0:S]; vig = 1 - .18 * (np.hypot(xx - S / 2, yy - S / 2) / (S * .7)) ** 2
    return bg * vig[..., None]

def frame(L, V, BG, t):
    img = BG.copy()
    # sombra suave sob o envelope
    sh = np.zeros((S, S)); sh[EY + 18:EY + EH + 24, EX + 10:EX + EW + 10] = 1
    sh = ndimage.gaussian_filter(sh, 22) * .22 * eo(seg(t, .2, 1.6))
    img *= (1 - sh[..., None])
    pb, pp, pf = eo(seg(t, .1, 1.7)), eo(seg(t, .5, 2.0)), eo(seg(t, .8, 2.2))
    fo = eio(seg(t, 4.25, 5.0))            # aba: 0 fechada → 1 aberta
    lift = eo(seg(t, 4.95, 6.0))
    # aba aberta fica atrás da carta
    if fo > .5: draw_flap(img, L, V, fo, t)
    if fo > .2:
        over(img, L['back'], EX, EY, alpha=seg(fo, .2, .45))
        over(img, L['letter'], EX + int(EW * .07), EY + int(EH * .06) - int(lift * EH * .62))
    b = reveal(L['body'], L['body_rev'], pb)
    if b is not None and fo <= .2: over(img, b, EX, EY)
    pk = reveal(L['pocket'], L['pocket_rev'], pp)
    if pk is not None: over(img, pk, EX, EY)
    ink = L['pocket_ink'] * seg(t, 1.2, 2.2); img[EY:EY + EH, EX:EX + EW] *= (1 - ink[..., None] * (1 - np.array(V['ink']) / 255))
    bi = L['body_ink'] * seg(t, 1.0, 2.0); img[EY:EY + EH, EX:EX + EW] *= (1 - bi[..., None] * (1 - np.array(V['ink']) / 255))
    if fo <= .5 and pf > 0:
        fs = np.zeros((S, S)); fs[EY:EY + FLAP_H + 8, EX:EX + EW] = poly_mask(FLAP_H + 8, EW, [(0, 0), (EW, 0), (EW * .5, FLAP_H + 8)]) * (1 - seg(fo, 0, .4))
        img *= (1 - ndimage.gaussian_filter(fs, 6)[..., None] * .16 * pf)
        f = reveal(L['flap'], L['flap_rev'], pf)
        if f is not None: draw_flap(img, L, V, fo, t, f)
    # lacre: carimba, depois se parte
    st = 2.25; brk = seg(t, 3.85, 4.35)
    if t >= st and brk < 1:
        sc = 1 + .7 * (1 - eo(seg(t, st, st + .22)))
        sl = L['seal']; n = sl.shape[0]
        cx, cy = EX + EW // 2, EY + FLAP_H - 6
        if brk <= 0:
            s2 = resize(sl, sc); over(img, s2, cx - s2.shape[1] // 2, cy - s2.shape[0] // 2)
            rp = seg(t, st + .1, st + .8)
            if 0 < rp < 1:
                yy, xx = np.mgrid[0:S, 0:S]; ring = np.exp(-((np.hypot(xx - cx, yy - cy) - (80 + rp * 120)) / 6) ** 2) * (1 - rp) * .25
                img *= (1 - ring[..., None] * (1 - np.array(V['seal']) / 255))
        else:
            half = n // 2; e = eo(brk); a = 1 - seg(t, 4.15, 4.4)
            jag = (np.sin(np.arange(n) / 6) * 4).astype(int)
            left = sl.copy(); right = sl.copy()
            for y in range(n): left[y, half + jag[y]:, 3] = 0; right[y, :half + jag[y], 3] = 0
            lr = rot(left, -e * 24); rr = rot(right, e * 20)
            over(img, lr, cx - lr.shape[1] // 2 - int(e * 46), cy - lr.shape[0] // 2 + int(e * 34), a)
            over(img, rr, cx - rr.shape[1] // 2 + int(e * 46), cy - rr.shape[0] // 2 + int(e * 40), a)
    return img

def draw_flap(img, L, V, fo, t, front=None):
    s = np.cos(np.pi * fo)                    # 1 fechada, -1 aberta (projeção da rotação no eixo da dobra)
    face = (front if front is not None else L['flap']) if s > 0 else L['flap_in']
    h = max(1, int(abs(s) * FLAP_H))
    im = face.copy()
    if s > 0:
        ink = L['flap_ink'][..., None] * seg(t, 1.4, 2.3); im[..., :3] *= (1 - ink * (1 - np.array(V['ink']) / 255))
    small = resize_xy(im, EW, h)
    if s < 0: small = small[::-1]
    shade = .75 + .25 * abs(s); small = small.copy(); small[..., :3] *= shade
    y = EY if s > 0 else EY - h
    over(img, small, EX, y)

def resize(rgba_, k):
    h, w = rgba_.shape[:2]; return resize_xy(rgba_, max(1, int(w * k)), max(1, int(h * k)))

def resize_xy(rgba_, w, h):
    im = Image.fromarray((np.clip(rgba_, 0, 1) * 255).astype(np.uint8), 'RGBA').resize((w, h), Image.LANCZOS)
    return np.asarray(im) / 255

def rot(rgba_, deg):
    im = Image.fromarray((np.clip(rgba_, 0, 1) * 255).astype(np.uint8), 'RGBA').rotate(deg, Image.BICUBIC, expand=True)
    return np.asarray(im) / 255

def label(img, V, t):
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
    a = seg(t, .3, 1.0)
    f = ImageFont.truetype(str(TTF('corm')), 40); txt = V['nome']; w = dr.textlength(txt, font=f)
    col = tuple(int(c * a + b * (1 - a)) for c, b in zip((70, 52, 34), V['bg']))
    dr.text(((S - w) / 2, S - 96), txt, font=f, fill=col)
    return np.asarray(im)

def render(v, out):
    V = VARIANTS[v]; L = build(v); BG = background(V)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{S}x{S}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        t = i / FPS; ff.stdin.write(label(frame(L, V, BG, t), V, t).tobytes())
    ff.stdin.close(); ff.wait(); print('ok', out)

def sound(out):
    """Pincel na pintura, carimbo do lacre, lacre partindo, aba e folha (mesmos efeitos do vídeo promocional)."""
    sys.path.insert(0, str(ROOT / 'tools/promo')); import promo_som as PS
    from scipy.io import wavfile
    SR = PS.SR; N = int(DUR * SR); fx = np.zeros((N, 2)); rng = np.random.default_rng(5)
    def add(t, y, pan=0.):
        i = int(t * SR); j = min(N, i + len(y)); fx[i:j, 0] += y[:j - i] * np.sqrt((1 - pan) / 2); fx[i:j, 1] += y[:j - i] * np.sqrt((1 + pan) / 2)
    n = int(2.1 * SR); tt = np.arange(n) / SR
    brush = PS.bp(rng.normal(0, 1, n), 700, 5000) * (.5 + .5 * np.sin(2 * np.pi * 1.6 * tt) ** 2) * np.sin(np.pi * tt / 2.1) * .06
    add(.1, brush, -.2); add(2.25, PS.thock()); add(3.85, PS.crack(), .1); add(4.25, PS.rustle(.7), -.2); add(4.95, PS.rustle(.9), .2)
    fx = fx / max(1e-9, np.max(np.abs(fx))) * .7
    wavfile.write(out, SR, (fx * 32767).astype(np.int16))

if __name__ == '__main__':
    mode, v, out = sys.argv[1:4]
    if mode == 'still':
        t = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0
        V = VARIANTS[v]; L = build(v); Image.fromarray(label(frame(L, V, background(V), t), V, t)).save(out)
    elif mode == 'som':
        sound(out)
    else:
        render(v, out)
