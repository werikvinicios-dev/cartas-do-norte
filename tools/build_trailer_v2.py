#!/usr/bin/env python3
"""Trailer cinematográfico de Cartas do Norte — 90 s, 1920×1080 com janela 2,39:1, 30 fps.

Roteiro em três atos, usando só aquarelas da edição e frases do próprio romance (prólogo, capítulos 1 e 3,
Carta I, carta náutica) e da paratextualidade da Edição Final. Nenhuma revelação do desfecho.

  0–15 s   A PRIMEIRA LUZ   três pulsações do farol no escuro; a segunda luz (prólogo); impacto.
 15–37 s   O ARQUIVO        funeral sob chuva, a carta escrita à mão, a casa do farol, a rota no mapa.
 37–52 s   A TRAVESSIA      montagem no pulso da trilha: mar de agulhas, salinas, lanternas, baleias, gruta.
 52–68 s   A TEMPESTADE     cortes rápidos, relâmpagos, tremor de câmera; "três pulsações / uma pausa / outras três".
 68–90 s   O EMBLEMA        silêncio, três pulsos, o emblema surge num facho de luz.

Imagem: câmera com subpixel, facho volumétrico, bloom, chuva em duas camadas, relâmpagos, tremor, chicote,
revelação em tinta (máscara de ruído), graduação de cor, vinheta e grão de filme.
Som (sintetizado aqui, sem trilhas de terceiros): drones, impactos graves, risers, chicotes, tambores,
sinos, piano e as ambiências originais da edição (mar, vento, chuva), com reverberação por convolução.

Uso: python3 tools/build_trailer_v2.py   (gera assets/video/trailer.mp4, trailer-poster.webp e trailer.vtt)
"""
import math, subprocess, tempfile, io, os
from pathlib import Path
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/video'
W, H, FPS, DUR = 1920, 1080, 30, 90.0
BAR = 138; AH = H - 2 * BAR          # janela 2,39:1
SR = 48000
rng = np.random.default_rng(7)

# ── utilitários de imagem ────────────────────────────────────────────────────
def img(p): return Image.open(ROOT / p).convert('RGB')
def ease(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
def eio(x): x = min(1.0, max(0.0, x)); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def lerp(a, b, k): return a + (b - a) * k
def env(t, a, d, peak=1.0):
    """Envelope de impacto: ataque a, queda exponencial d."""
    if t < 0: return 0.0
    return peak * (t / a if t < a else math.exp(-(t - a) / d))

def window(im, cx, cy, wf, dx=0.0, dy=0.0):
    """Janela 2,39:1 de largura wf (fração da largura da imagem), centrada em (cx, cy) normalizados."""
    iw, ih = im.size
    w = min(wf * iw, iw, ih * W / AH); h = w * AH / W
    x = min(max(cx * iw + dx, w / 2), iw - w / 2); y = min(max(cy * ih + dy, h / 2), ih - h / 2)
    return np.asarray(im.transform((W, AH), Image.EXTENT, (x - w / 2, y - h / 2, x + w / 2, y + h / 2), Image.BICUBIC), np.float32) / 255

def to_pil(a): return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def blur_small(a, factor=4, radius=10):
    s = to_pil(a).resize((W // factor, AH // factor), Image.BILINEAR).filter(ImageFilter.GaussianBlur(radius))
    return np.asarray(s.resize((W, AH), Image.BILINEAR), np.float32) / 255

def bloom(a, k=0.6, thr=0.62):
    return a + k * blur_small(np.maximum(a - thr, 0) * 2.2, 4, 9)

def hblur(a, r):
    """Desfoque horizontal (chicote de câmera) por soma acumulada."""
    if r < 1: return a
    r = int(r); c = np.cumsum(np.pad(a, ((0, 0), (r + 1, r), (0, 0)), mode='edge'), axis=1)
    return (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)

YY, XX = np.mgrid[0:AH, 0:W].astype(np.float32)
VIGNETTE = (1 - 0.55 * (((XX - W / 2) / (W * .62)) ** 2 + ((YY - AH / 2) / (AH * .78)) ** 2)).clip(0.25, 1)[..., None]
GRAIN = [rng.normal(0, 1, (AH, W)).astype(np.float32)[..., None] for _ in range(6)]

def grade(a, warm=0.0, cool=0.0, sat=1.0, gamma=1.0):
    lum = (a @ np.array([.299, .587, .114], np.float32))[..., None]
    a = lum + (a - lum) * sat
    a = a + (1 - lum) * np.array([-.012, .012, .03], np.float32) * (1 + cool * 2) + lum * np.array([.035, .012, -.03], np.float32) * (1 + warm * 2)
    a = 0.5 + (np.clip(a, 0, 1) ** gamma - 0.5) * 1.08
    return a

def radial(cx, cy, r, color, k=1.0):
    d = ((XX - cx) ** 2 + (YY - cy) ** 2) / (r * r)
    return (np.exp(-d)[..., None] * np.array(color, np.float32)) * k

def beam(px, py, theta, width=0.11, length=1500, k=1.0, color=(1.0, .93, .75)):
    """Facho volumétrico calculado em 1/4 de resolução."""
    s = 4; ys, xs = np.mgrid[0:AH // s, 0:W // s].astype(np.float32); ys *= s; xs *= s
    ang = np.arctan2(ys - py, xs - px); dist = np.hypot(xs - px, ys - py)
    da = np.angle(np.exp(1j * (ang - theta)))
    inten = np.exp(-(da / width) ** 2) * np.exp(-dist / length) * (dist > 6)
    big = np.asarray(Image.fromarray((inten * 255).clip(0, 255).astype(np.uint8)).resize((W, AH), Image.BILINEAR), np.float32) / 255
    return big[..., None] * np.array(color, np.float32) * k

def smooth_noise(seed, scale):
    r = np.random.default_rng(seed).random((AH // scale + 2, W // scale + 2)).astype(np.float32)
    im = Image.fromarray((r * 255).astype(np.uint8)).resize((W + 2 * scale, AH + 2 * scale), Image.BICUBIC)
    return np.asarray(im, np.float32)[scale:scale + AH, scale:scale + W] / 255
INK = (smooth_noise(3, 90) * .6 + smooth_noise(4, 24) * .3 + smooth_noise(5, 6) * .1)

def rain_sheet(seed, n, length, alpha, slant):
    r = np.random.default_rng(seed); sh = Image.new('L', (W, AH * 2), 0); d = ImageDraw.Draw(sh)
    for _ in range(n):
        x, y = r.uniform(-200, W), r.uniform(0, AH * 2); l = r.uniform(.6, 1.2) * length
        d.line([(x, y), (x + slant * l, y + l)], fill=int(r.uniform(.4, 1) * alpha), width=1)
    return np.asarray(sh.filter(ImageFilter.GaussianBlur(.6)), np.float32) / 255
RAIN = [rain_sheet(11, 2600, 38, 255, .18), rain_sheet(12, 900, 90, 200, .22)]
def rain(t, k=1.0, speed=(1900, 2600)):
    out = 0
    for sheet, sp in zip(RAIN, speed):
        off = int(t * sp) % AH
        out = out + sheet[AH - off: 2 * AH - off] * (0.35 if sp == speed[0] else 0.55)
    return (out[..., None] * np.array([.82, .88, .95], np.float32)) * k

MIST = np.asarray(Image.open(ROOT / 'assets/experience/mist.webp').convert('RGBA').resize((2048, AH)), np.float32)[..., 3] / 255
def mist(t, k=.35, speed=22):
    o = int(t * speed) % 2048
    m = np.concatenate([MIST, MIST], axis=1)[:, o:o + W]
    return (m[..., None] * np.array([.75, .8, .85], np.float32)) * k

def shake(t, amp, seed=1):
    return (amp * (math.sin(t * 37 + seed) * .6 + math.sin(t * 61 + 2 * seed) * .4),
            amp * (math.sin(t * 43 + 3 * seed) * .6 + math.sin(t * 71 + seed) * .4))

# ── fontes e texto ──────────────────────────────────────────────────────────
TMP = Path(tempfile.mkdtemp())
def font_file(woff2, name):
    f = TTFont(ROOT / 'assets/fonts' / woff2); f.flavor = None; p = TMP / name; f.save(p); return str(p)
F_BRAND = font_file('cartas-display.woff2', 'brand.ttf')
F_ITAL = font_file('cormorant-400-italic.woff2', 'ital.ttf')
F_CAPS = font_file('cormorant-500.woff2', 'caps.ttf')
_fc = {}
def font(path, size):
    k = (path, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

def text_rgba(lines, path, size, tracking=0.0, y=0.5, color=(244, 237, 222), lead=1.25, x=0.5, align='center'):
    """Camada RGBA (W×AH) com letras espaçadas por 'tracking' (em fração do tamanho)."""
    lay = Image.new('L', (W, AH), 0); d = ImageDraw.Draw(lay); f = font(path, size)
    total = len(lines) * size * lead; y0 = y * AH - total / 2
    for i, line in enumerate(lines):
        widths = [f.getlength(ch) for ch in line]; tw = sum(widths) + tracking * size * (len(line) - 1)
        cx = x * W - (tw / 2 if align == 'center' else 0)
        for ch, w_ in zip(line, widths):
            d.text((cx, y0 + i * size * lead), ch, font=f, fill=255); cx += w_ + tracking * size
    return np.asarray(lay, np.float32) / 255, np.array(color, np.float32) / 255

def put_text(a, mask_color, alpha=1.0, glow=0.0, wipe=None, rise=0.0):
    m, col = mask_color
    if rise: m = np.roll(m, int(rise), axis=0)
    if wipe is not None:   # revelação da esquerda para a direita, borda suave
        edge = wipe * (W + 300) - 150
        m = m * np.clip((edge - XX) / 150, 0, 1)
    m = m * alpha
    if glow:
        g = blur_small(np.repeat(m[..., None], 3, 2), 2, 8) * col * glow
        a = a + g
    return a * (1 - m[..., None] * .92) + m[..., None] * col

def caption(t, t0, t1, lines, path=F_ITAL, size=66, y=.78, tracking=0.0, glow=.6, color=(244, 237, 222)):
    if not (t0 <= t < t1): return None
    k = min(ease((t - t0) / .8), ease((t1 - t) / .6))
    tr = tracking + (1 - ease((t - t0) / 2.5)) * .06 if tracking else 0
    return text_rgba(lines, path, size, tr, y, color), k, (1 - ease((t - t0) / 1.2)) * 14

# ── materiais ───────────────────────────────────────────────────────────────
COVER = img('assets/branding/cover.webp'); PRO = img('assets/art/prologue.webp'); CH1 = img('assets/art/ch1.webp')
CH3 = img('assets/art/ch3.webp'); MAP = img('assets/maps/map_stage_1.webp'); PAPER = img('assets/experience/letter-paper.webp')
SAIL = img('assets/art/ch22.webp'); SALT = img('assets/art/salinas-ao-entardecer.webp'); LANT = img('assets/art/lanternas-de-papel.webp')
WHALE = img('assets/art/vozes-das-baleias.webp'); CAVE = img('assets/art/ch33.webp'); STORM1 = img('assets/art/ch14.webp')
STORM2 = img('assets/art/ch26.webp'); ROCK = img('assets/art/ch34.webp'); BELLS = img('assets/art/primeiros-sinos.webp')
EMB = Image.open(ROOT / 'assets/branding/emblem-gold.webp').convert('RGBA')
PAPER_A = window(PAPER, .5, .45, .75)
LETTER = text_rgba(['Dona Ana,', 'Não lhe escrevo para pedir', 'que me perdoe.'], F_ITAL, 70, 0, .47, (52, 34, 18), 1.35)
BLACK = np.zeros((AH, W, 3), np.float32)
LAMP = (.896, .353)   # lanterna do farol na capa (normalizado)

# ── planos ──────────────────────────────────────────────────────────────────
def pulses(t, times, a=.04, d=.45): return sum(env(t - s, a, d) for s in times)

def s_first(t):
    k = (t - 0) / 8
    cx, cy, wf = lerp(.80, .86, ease(k)), lerp(.42, .38, ease(k)), lerp(.55, .38, ease(k))
    a = window(COVER, cx, cy, wf) * .10
    p = pulses(t, [2.0, 3.0, 4.0])
    lit = window(COVER, cx, cy, wf)
    a = a + lit * (.05 + .75 * p) + (lit * .5 * ease((t - 4.6) / 3))
    iw, ih = COVER.size; w = wf * iw
    lx = (LAMP[0] * iw - (min(max(cx * iw, w / 2), iw - w / 2) - w / 2)) / w * W
    ly = (LAMP[1] * ih - (min(max(cy * ih, w * AH / W / 2), ih - w * AH / W / 2) - w * AH / W / 2)) / (w * AH / W) * AH
    a = a + radial(lx, ly, 70 + 120 * p, (1, .9, .65), .9 * p + .25 * ease((t - 4.6) / 2))
    if t > 4.4: a = a + beam(lx, ly, math.pi + .9 - (t - 4.4) * .55, k=.55 * ease((t - 4.4) / 1.5))
    a = a + mist(t, .22)
    return a, dict(bloom=.6 + .5 * p)

def s_second(t):
    k = (t - 8.4) / 7.1
    a = window(PRO, lerp(.42, .3, eio(k)), lerp(.55, .22, eio(k)), lerp(.95, .55, eio(k)))
    a = a * (.55 + .45 * ease((t - 8.4) / 1.5))
    fl = .75 + .25 * math.sin(t * 23) * math.sin(t * 7.3)
    a = a + radial(W * lerp(.32, .45, eio(k)), AH * lerp(.18, .32, eio(k)), 140, (1, .18, .08), .55 * fl * ease((t - 9) / 2))
    a = a + rain(t, .45) + mist(t, .2)
    return a, dict(bloom=.7, cool=.6, sat=.85)

def s_funeral(t):
    k = (t - 16.6) / 5.9
    a = window(CH1, .5, lerp(.25, .62, eio(k)), lerp(1.0, .82, k))
    a = a + rain(t, .9)
    return a, dict(sat=.55, cool=1.0, gamma=1.05)

def s_letter(t):
    k = (t - 22.3) / 6.2
    a = PAPER_A.copy() * .92
    a = put_text(a, LETTER, wipe=ease((t - 23.0) / 4.0) * 1.0)
    a = a + radial(W * .15, AH * .2, 520, (1, .62, .25), .22 * (.85 + .15 * math.sin(t * 9) * math.sin(t * 4.1)))
    a = to_arr_zoom(a, 1.0 + .05 * k, .45, .45)
    return a, dict(warm=.8, sat=1.0)

def to_arr_zoom(a, z, fx, fy):
    im = to_pil(a); w, h = W / z, AH / z; x = fx * W - w * fx; y = fy * AH - h * fy
    return np.asarray(im.transform((W, AH), Image.EXTENT, (x, y, x + w, y + h), Image.BICUBIC), np.float32) / 255

def s_house(t):
    k = (t - 28.3) / 5.0
    a = window(CH3, lerp(.5, .55, k), lerp(.45, .38, k), lerp(1.0, .78, eio(k)))
    a = a + mist(t, .12)
    return a, dict(warm=.3, sat=.9)

def s_map(t):
    k = (t - 33.1) / 3.9
    m = window(MAP, .45, lerp(.62, .55, k), lerp(.95, .7, eio(k)))
    reveal = np.clip((ease((t - 33.1) / 2.2) * 1.25 - INK) * 6, 0, 1)[..., None]
    a = PAPER_A * (1 - reveal) + m * reveal
    return a, dict(warm=.6, sat=.9)

def mk_pan(im, c0, c1, w0, w1, extra=None, grade_=None):
    def f(t, t0, t1):
        k = eio((t - t0) / (t1 - t0))
        a = window(im, lerp(c0[0], c1[0], k), lerp(c0[1], c1[1], k), lerp(w0, w1, k))
        if extra: a = extra(a, t)
        return a, grade_ or {}
    return f

def glow_lights(a, t, thr=.72, k=1.2):
    b = np.maximum(a - thr, 0) * (1 + .25 * math.sin(t * 11)); return a + blur_small(b, 4, 7) * k * 2
def biolum(a, t):
    blue = np.clip(a[..., 2] - a[..., 0] * .8 - .08, 0, 1)[..., None]
    return a + blur_small(blue * np.array([.2, .7, 1.2], np.float32), 4, 8) * (1.1 + .5 * math.sin(t * 3.1))
def lantern(a, t): return a + radial(W * .36, AH * .45, 260, (1, .7, .3), .35 * (.8 + .2 * math.sin(t * 13) * math.sin(t * 5)))

MONTAGE = [  # (início, fim, função)
    (37.0, 39.4, mk_pan(SAIL, (.35, .35), (.62, .4), .95, .8, None, dict(warm=.8))),
    (40.6, 43.0, mk_pan(SALT, (.5, .5), (.5, .48), 1.0, .82, None, dict(warm=1.0))),
    (44.2, 46.6, mk_pan(LANT, (.4, .6), (.55, .55), .95, .75, glow_lights, dict(warm=.6))),
    (47.8, 50.2, mk_pan(WHALE, (.35, .55), (.5, .52), .95, .75, biolum, dict(cool=1.2, sat=1.1))),
    (50.2, 52.6, mk_pan(CAVE, (.4, .3), (.45, .42), 1.0, .75, lantern, dict(warm=.5))),
]
TITLES = [(39.4, 40.6, 'ENTRE CARTAS'), (43.0, 44.2, 'FARÓIS'), (46.6, 47.8, 'E TRAVESSIAS')]

def storm_extra(a, t): return a * .62 + rain(t, 1.1)
STORM = [
    (52.6, 55.0, mk_pan(STORM1, (.5, .35), (.5, .6), 1.0, .8, storm_extra, dict(cool=1.3, sat=.8))),
    (55.0, 57.0, mk_pan(STORM2, (.4, .4), (.6, .45), .95, .75, storm_extra, dict(cool=1.3, sat=.8))),
    (57.0, 58.6, mk_pan(COVER, (.8, .4), (.86, .38), .55, .4, storm_extra, dict(cool=1.5, sat=.7))),
    (59.8, 61.2, mk_pan(ROCK, (.5, .55), (.55, .35), .95, .7, storm_extra, dict(cool=1.3, sat=.8))),
    (62.0, 63.2, mk_pan(BELLS, (.6, .5), (.7, .5), .8, .6, storm_extra, dict(cool=1.0, sat=.6))),
    (64.2, 66.6, mk_pan(COVER, (.86, .4), LAMP, .45, .16, storm_extra, dict(cool=1.0, sat=.8))),
]
CARDS = [(58.6, 59.8, 'TRÊS PULSAÇÕES SOBRE O MAR'), (61.2, 62.0, 'UMA PAUSA'), (63.2, 64.2, 'OUTRAS TRÊS')]
LIGHTNING = [52.75, 54.3, 56.1, 57.4, 60.4, 62.6]
FINAL_PULSES = [64.6, 65.2, 65.8]

def card(t, t0, t1, word, size=124):
    k = (t - t0) / (t1 - t0)
    size = min(size, int(W * .78 / max(1, len(word) * .62 + len(word) * .26)))
    tm = text_rgba([word], F_BRAND, size, .22 * (1 - eio(min(1, k * 1.6))) + .04, .5, (232, 203, 150))
    a = put_text(BLACK.copy(), tm, alpha=min(ease(k * 5), ease((1 - k) * 6)), glow=1.1)
    return a

def s_emblem(t):
    a = BLACK.copy()
    for s in (68.5, 69.5, 70.5):
        a = a + radial(W / 2, AH / 2, 60 + 260 * env(t - s, .03, .5), (1, .85, .55), env(t - s, .03, .6))
    if t >= 70.9:
        k = ease((t - 70.9) / 2.6); sc = lerp(.9, 1.0, eio((t - 70.9) / 6))
        h = int(AH * .84 * sc); e = EMB.resize((int(EMB.width * h / EMB.height), h), Image.LANCZOS)
        layer = np.zeros((AH, W, 4), np.float32); ea = np.asarray(e, np.float32) / 255
        x0, y0 = (W - e.width) // 2, int(AH * .45 - h / 2)
        layer[y0:y0 + h, x0:x0 + e.width] = ea
        al = layer[..., 3:4] * k
        sweep = math.exp(0)  # posição do brilho que atravessa o emblema
        pos = (t - 71.4) * 900 - 300
        band = np.exp(-(((XX - x0) + (YY - y0) * .6 - pos) / 70) ** 2)[..., None]
        a = a * (1 - al) + layer[..., :3] * al * (1 + 1.6 * band)
        if t > 74.5:
            a = put_text(a, text_rgba(['O ARQUIVO VIVO'], F_CAPS, 40, .55 - .25 * eio((t - 74.5) / 3), .905, (226, 197, 140)), alpha=ease((t - 74.5) / 1.2), glow=.5)
    fade = 1 - ease((t - 86.5) / 3.0)
    return a * fade, dict(bloom=1.0, warm=.4)

# ── quadro ──────────────────────────────────────────────────────────────────
def frame(i):
    t = i / FPS; g = {}; a = None; caps = []
    if t < 8.4: a, g = s_first(t)
    if 8.0 <= t < 15.5:
        b, g2 = s_second(t); k = ease((t - 8.0) / .6) if t < 8.6 else 1
        a = b if a is None or k >= 1 else a * (1 - k) + b * k; g = g2 if k > .5 else g
    if 15.5 <= t < 16.6: a = BLACK.copy()
    if 16.6 <= t < 22.5: a, g = s_funeral(t)
    if 22.3 <= t < 28.5:
        b, g2 = s_letter(t); k = ease((t - 22.3) / .5)
        a = b if a is None or k >= 1 else a * (1 - k) + b * k; g = g2
    if 28.3 <= t < 33.3:
        b, g2 = s_house(t); k = ease((t - 28.3) / .5)
        a = b if a is None or k >= 1 else a * (1 - k) + b * k; g = g2
    if 33.1 <= t < 37.0:
        b, g2 = s_map(t); k = ease((t - 33.1) / .4)
        a = b if a is None or k >= 1 else a * (1 - k) + b * k; g = g2
    for t0, t1, f in MONTAGE + STORM:
        if t0 <= t < t1:
            a, g = f(t, t0, t1)
            whip = max(0, 1 - (t - t0) / .22)
            if whip: a = hblur(np.roll(a, int(-160 * whip), axis=1), 60 * whip)
    for t0, t1, word in TITLES + CARDS:
        if t0 <= t < t1: a, g = card(t, t0, t1, word), dict(bloom=.6)
    if 36.75 <= t < 37.0:   # chicote de saída do mapa
        a = hblur(np.roll(a, int(220 * (t - 36.75) / .25), axis=1), 70 * (t - 36.75) / .25)
    if 66.6 <= t < 68.0: a = BLACK.copy() + .8 * math.exp(-(t - 66.6) / .18)
    if t >= 68.0: a, g = s_emblem(t)
    if a is None: a = BLACK.copy()

    # tremor de câmera na tempestade
    if 52.6 <= t < 66.6:
        dx, dy = shake(t, 7 + 8 * ease((t - 52.6) / 12))
        a = np.roll(np.roll(a, int(dx), 1), int(dy), 0)
    # relâmpagos e pulsos finais
    lt = sum(env(t - s, .02, .12) * (1 + .6 * (math.sin((t - s) * 90) > 0)) for s in LIGHTNING)
    if lt: a = a * (1 + .55 * min(lt, 1.2)) + np.array([.45, .52, .7], np.float32) * min(lt, 1.2) * .16
    fp = pulses(t, FINAL_PULSES, .02, .35)
    if fp: a = a * (1 + .5 * fp) + radial(W * .5, AH * .5, 700, (1, .9, .7), .35 * fp)
    if 15.47 <= t < 15.62: a = a * 0 + 1.0   # clarão do impacto

    # legendas literais
    for c in (caption(t, 4.8, 8.0, ['A primeira luz era a que todos esperavam.']),
              caption(t, 11.0, 15.2, ['A segunda luz não deveria existir.'], size=60),
              caption(t, 17.6, 22.2, ['Choveu no funeral de Jonas Vale…']),
              caption(t, 26.8, 28.4, ['DOZE CARTAS ATRAVESSAM A NARRATIVA'], F_CAPS, 30, .9, .38, .3, (226, 197, 140)),
              caption(t, 29.2, 33.1, ['A casa do farol tinha aprendido', 'a envelhecer sem testemunhas.']),
              caption(t, 34.0, 36.8, ['UMA ROTA NÃO É SEGURA', 'PORQUE ALGUÉM A DESENHOU COM RÉGUA'], F_BRAND, 52, .5, .12, .9, (30, 22, 12))):
        if c:
            mc, k, rise = c; light = mc[1][0] > .5
            ys = np.where(mc[0].max(1) > 0)[0]
            if len(ys):
                cyy = (ys[0] + ys[-1]) / 2; hh = (ys[-1] - ys[0]) / 2 + 60
                band = np.exp(-((YY[:, :1] - cyy) / hh) ** 4)[..., None] * k
                a = a * (1 - .55 * band) if light else a * (1 - .6 * band) + band * .6 * np.array([.95, .9, .8], np.float32)
            a = put_text(a, mc, alpha=k, glow=.5 if light else 0, rise=rise)

    a = grade(a, g.get('warm', 0), g.get('cool', 0), g.get('sat', 1), g.get('gamma', 1))
    a = bloom(a, .35 * g.get('bloom', 1))
    a = a * VIGNETTE + GRAIN[i % 6] * .014
    out = np.zeros((H, W, 3), np.uint8); out[BAR:BAR + AH] = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    return out.tobytes()

# ── som ─────────────────────────────────────────────────────────────────────
from scipy import signal
N = int(DUR * SR); TT = np.arange(N) / SR
def at(s): return int(s * SR)
def place(buf, start, x, gain=1.0):
    i = at(start); j = min(N, i + len(x));
    if j > i: buf[i:j] += x[:j - i] * gain
def lp(x, f, o=4): return signal.sosfilt(signal.butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=4): return signal.sosfilt(signal.butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, a, b): return signal.sosfilt(signal.butter(4, [a, b], 'band', fs=SR, output='sos'), x)
def boom(d=2.2, f0=58, f1=28):
    t = np.arange(int(d * SR)) / SR; f = f1 + (f0 - f1) * np.exp(-t * 6)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.0)
    x += lp(rng.normal(0, 1, len(t)), 180) * np.exp(-t * 18) * .8
    return np.tanh(x * 1.6)
def hit(d=3.0):
    t = np.arange(int(d * SR)) / SR
    return boom(d, 70, 30) + bp(rng.normal(0, 1, len(t)), 200, 4000) * np.exp(-t * 7) * .35
def riser(d):
    t = np.arange(int(d * SR)) / SR; n = rng.normal(0, 1, len(t)); out = np.zeros_like(n); seg = int(.05 * SR)
    for s in range(0, len(t), seg):
        k = s / len(t); out[s:s + seg] = bp(n[s:s + seg + 400], 300 + 4000 * k ** 2, 600 + 8000 * k ** 2)[:len(n[s:s + seg])]
    tone = np.sin(2 * np.pi * np.cumsum(180 + 700 * (t / d) ** 2) / SR) * .25
    return (out * .6 + tone) * (t / d) ** 2.2
def whoosh(d=.45):
    t = np.arange(int(d * SR)) / SR; e = np.sin(np.pi * t / d) ** 2
    return bp(rng.normal(0, 1, len(t)), 500, 5000) * e * .6
def tom(d=.6, f0=95, f1=52):
    t = np.arange(int(d * SR)) / SR; f = f1 + (f0 - f1) * np.exp(-t * 14)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6) + lp(rng.normal(0, 1, len(t)), 900) * np.exp(-t * 40) * .4
def tick(): t = np.arange(int(.05 * SR)) / SR; return hp(rng.normal(0, 1, len(t)), 3000) * np.exp(-t * 90) * .4
def bell(f=196, d=5.0):
    t = np.arange(int(d * SR)) / SR
    return sum(np.sin(2 * np.pi * f * r * t) * np.exp(-t * dd) * g for r, dd, g in [(1, .7, 1), (2.01, 1.1, .5), (2.76, 1.6, .35), (3.9, 2.4, .2), (5.4, 3, .12)]) * .4
def piano(f, d=3.5):
    t = np.arange(int(d * SR)) / SR
    return sum(np.sin(2 * np.pi * f * h * t) * np.exp(-t * (1.2 + h * .7)) / h ** 1.3 for h in range(1, 6)) * np.minimum(1, t * 200) * .35
def saw(f, t): return 2 * ((t * f) % 1) - 1
def drone(t0, t1, freqs, gain, cut=500, attack=3.0):
    t = TT[at(t0):at(t1)] - t0
    x = sum(saw(f * d, t) for f in freqs for d in (1, 1.004, .996)) / (3 * len(freqs))
    x = lp(x, cut) * np.minimum(1, t / attack) * np.minimum(1, (t1 - t0 - t) / 1.5)
    return x * gain
def braam(d=7.0):
    t = np.arange(int(d * SR)) / SR
    x = sum(saw(f, t) for f in (55, 55.3, 54.7, 110.2, 82.4)) / 5
    return lp(np.tanh(x * 3) * np.minimum(1, t / .08) * np.exp(-t * .35), 1100) * .9
def ogg(name):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', str(ROOT / f'assets/audio/{name}.ogg'), '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).astype(np.float64); return np.tile(x, N // len(x) + 1)[:N]
def fade_env(points):
    xs, ys = zip(*points); return np.interp(TT, xs, ys)

def build_audio(path):
    dry = np.zeros(N); send = np.zeros(N)
    sea, wind, rainx = ogg('mar'), ogg('vento'), ogg('chuva')
    dry += sea * fade_env([(0, 0), (1.5, .55), (15, .5), (16.6, .3), (37, .25), (52, .2), (68, .2), (80, .45), (90, 0)])
    dry += wind * fade_env([(0, 0), (8, .15), (15, .25), (37, .1), (52.6, .5), (66.6, .55), (68, 0), (90, 0)])
    dry += rainx * fade_env([(0, 0), (8.4, 0), (9.5, .2), (15.4, .25), (15.5, 0), (16.6, .4), (22.3, .35), (23, 0), (52.6, 0), (53, .7), (66.6, .7), (67, 0), (90, 0)])
    for s in (2.0, 3.0, 4.0): place(dry, s, boom(), .85); place(send, s, boom(), .4)
    place(dry, 10.0, riser(5.45), .55); place(dry, 15.45, hit(), 1.0); place(send, 15.45, hit(), .6)
    dry += np.pad(drone(16.0, 37.0, [55, 82.41], .22, 380, 5), (at(16.0), N - at(37.0)))
    for k, (s, f) in enumerate([(17.0, 440), (18.4, 329.6), (19.8, 392), (21.2, 349.2), (23.4, 440), (24.8, 523.3), (26.2, 493.9), (27.6, 440),
                                (29.4, 329.6), (30.8, 349.2), (32.2, 293.7), (33.6, 329.6), (35.0, 261.6), (35.7, 220)]):
        place(dry, s, piano(f), .5); place(send, s, piano(f), .5)
    place(dry, 34.4, riser(2.6), .4); place(dry, 36.75, whoosh(), .8)
    # pulso da travessia: 100 bpm
    beat = 60 / 100
    dry += np.pad(drone(37.0, 52.6, [55, 65.4, 82.41], .26, 700, 1.0), (at(37.0), N - at(52.6)))
    for b in np.arange(37.0, 52.6, beat):
        place(dry, b, tom(.5, 80, 48), .55); place(dry, b + beat / 2, tick(), .5)
    for t0, _, _ in MONTAGE: place(dry, t0, whoosh(), .5)
    for t0, _, _ in TITLES: place(dry, t0, boom(1.6, 64, 34), .7); place(send, t0, bell(293.7), .3)
    # tempestade: tambores acelerando
    place(dry, 52.6, hit(), 1.0)
    t = 52.6; step = 60 / 120
    while t < 66.6:
        if not (61.2 <= t < 62.0):
            place(dry, t, tom(.55, 105, 55), .85)
            if t > 57: place(dry, t + step / 2, tom(.35, 140, 80), .45)
        t += step * (1 - .45 * ease((t - 52.6) / 14))
    dry += np.pad(drone(52.6, 61.2, [55, 58.27, 82.41], .3, 900, .5), (at(52.6), N - at(61.2)))
    dry += np.pad(drone(62.0, 66.6, [55, 58.27, 82.41, 110], .34, 1200, .3), (at(62.0), N - at(66.6)))
    for s in LIGHTNING: place(dry, s, lp(rng.normal(0, 1, int(2.5 * SR)), 260) * np.exp(-np.arange(int(2.5 * SR)) / SR * 1.6), .9)
    for t0, _, _ in CARDS: place(dry, t0, boom(1.4, 70, 36), .9)
    place(send, 62.0, bell(196, 6), .9); place(dry, 62.0, bell(196, 6), .5)
    for t0, _, _ in STORM: place(dry, t0, whoosh(.3), .6)
    for s in FINAL_PULSES: place(dry, s, hit(2.0), .9); place(send, s, hit(2.0), .5)
    place(send, 66.6, bell(130.8, 7), .6)
    for s in (68.5, 69.5, 70.5): place(dry, s, boom(2.0, 50, 26), .7); place(send, s, boom(2.0, 50, 26), .4)
    place(dry, 70.9, braam(9), .75); place(send, 70.9, braam(9), .5); place(dry, 70.9, hit(4), .8)
    for s, f in [(74.5, 220), (75.9, 261.6), (77.3, 329.6), (78.7, 293.7), (80.6, 220)]:
        place(dry, s, piano(f, 5), .45); place(send, s, piano(f, 5), .6)
    ir_t = np.arange(int(3.2 * SR)) / SR
    irL = rng.normal(0, 1, len(ir_t)) * np.exp(-ir_t * 2.1); irR = rng.normal(0, 1, len(ir_t)) * np.exp(-ir_t * 2.1)
    wetL = signal.fftconvolve(send, irL)[:N] * .025; wetR = signal.fftconvolve(send, irR)[:N] * .025
    L, R = dry + wetL, dry + wetR
    m = np.stack([L, R], 1); m = np.tanh(m / np.max(np.abs(m)) * 1.4); m *= .93 / np.max(np.abs(m))
    m *= np.minimum(1, (DUR - TT) / 2.5)[:, None]
    from scipy.io import wavfile
    wavfile.write(path, SR, (m * 32767).astype(np.int16))

VTT = [(4.8, 8.0, 'A primeira luz era a que todos esperavam.'), (11.0, 15.2, 'A segunda luz não deveria existir.'),
       (17.6, 22.2, 'Choveu no funeral de Jonas Vale…'), (23.0, 28.4, 'Dona Ana, não lhe escrevo para pedir que me perdoe. — Doze cartas atravessam a narrativa.'),
       (29.2, 33.1, 'A casa do farol tinha aprendido a envelhecer sem testemunhas.'), (34.0, 36.8, 'Uma rota não é segura porque alguém a desenhou com régua.'),
       (39.4, 47.8, 'Entre cartas, faróis e travessias.'), (58.6, 64.2, 'Três pulsações sobre o mar, uma pausa, outras três.'),
       (74.5, 86.5, 'Cartas do Norte — O Arquivo Vivo.')]
def vtt():
    f = lambda s: f'00:{int(s // 60):02d}:{s % 60:06.3f}'
    return 'WEBVTT\n\n' + '\n\n'.join(f'{f(a)} --> {f(b)}\n{t}' for a, b, t in VTT) + '\n'

if __name__ == '__main__':
    wav = TMP / 'a.wav'; build_audio(wav); print('áudio ok', flush=True)
    vid = TMP / 'v.mp4'; n = int(DUR * FPS)
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-preset', 'slow', '-crf', '27', '-pix_fmt', 'yuv420p', '-maxrate', '3M', '-bufsize', '6M', str(vid)], stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(frame, range(n), chunksize=4)):
            enc.stdin.write(buf)
            if k % 300 == 0: print(f'{k}/{n}', flush=True)
    enc.stdin.close(); enc.wait()
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(vid), '-i', str(wav), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', str(OUT / 'trailer.mp4')], check=True)
    poster = np.frombuffer(frame(int(73.8 * FPS)), np.uint8).reshape(H, W, 3)
    Image.fromarray(poster).resize((1280, 720), Image.LANCZOS).save(OUT / 'trailer-poster.webp', quality=84)
    (OUT / 'trailer.vtt').write_text(vtt())
    print('ok', OUT / 'trailer.mp4')
