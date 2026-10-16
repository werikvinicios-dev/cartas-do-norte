#!/usr/bin/env python3
"""TRAILER OFICIAL — "O Arquivo Vivo · uma aquarela que respira". 80 s, 24 fps, 16:9 (e 9:16).

Roteiro do prompt mestre, sete sequências (ver docs/trailer/STORYBOARD.md):
  I   0–8    O mar se lembra          preto; superfície escura do mar; a névoa revela a costa.
  II  8–20   O funeral do faroleiro   funeral sob chuva (cap. 1); chuva sobre o caixão; o farol apagado.
  III 20–31  O que ficou para trás    a casa do farol e o baú de cartas (cap. 3); a mesa de mapas (cap. 21);
                                      o azul do mapa vira água.
  IV  31–44  A travessia              a Constância no mar (cap. 22); a câmera sobe e revela a escala.
  V   44–59  O peso do passado        mão e relógio; o testamento (cap. 2) se revela; mar escuro; farol distante;
                                      silhueta à janela (cap. 7); a rota no mapa.
  VI  59–70  O silêncio antes da luz  preto; a primeira luz da manhã sobre a costa (Parte IV).
  VII 70–80  O nome da história       um ponto de luz revela o emblema; subtítulo; chamada.
Regras: só movimento atmosférico (névoa, chuva, água, luz, folha solta em primeiro plano) e câmera mínima;
nenhum rosto, corpo, navio ou arquitetura deformados; sem flashes, glitch ou tremor.
O farol aparece apagado antes do desfecho ("A torre estava apagada havia dezessete anos", cap. 1).

Uso:  TRAILER_W=1920 TRAILER_H=1080 python3 tools/trailer_oficial.py video <saida.mp4>
      TRAILER_W=1080 TRAILER_H=1920 python3 tools/trailer_oficial.py video <saida_vertical.mp4>
      python3 tools/trailer_oficial.py frames <pasta>   (quadros-chave para storyboard)
"""
import math, os, sys, subprocess
from pathlib import Path
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
W = int(os.environ.get('TRAILER_W', 1920)); H = int(os.environ.get('TRAILER_H', 1080))
VERT = H > W; S = min(W, H) / 1080; FPS = 24; DUR = 80.0
rng = np.random.default_rng(3)

def img(p): return Image.open(ROOT / p).convert('RGB')
def ease(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
def eio(x): x = min(1.0, max(0.0, x)); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def lerp(a, b, k): return a + (b - a) * k
def arr(p): return np.asarray(p, np.float32) / 255
def pil(a): return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def window(im, cx, cy, wf, out=(None, None)):
    """Recorte na proporção da tela: largura wf (fração da imagem) centrada em (cx, cy); nunca sai da pintura."""
    ow, oh = out[0] or W, out[1] or H; iw, ih = im.size
    w = min(wf * iw, iw, ih * ow / oh); h = w * oh / ow
    x = min(max(cx * iw, w / 2), iw - w / 2); y = min(max(cy * ih, h / 2), ih - h / 2)
    return arr(im.transform((ow, oh), Image.EXTENT, (x - w / 2, y - h / 2, x + w / 2, y + h / 2), Image.BICUBIC))

YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
VIGN = (1 - .42 * (((XX - W / 2) / (W * .7)) ** 2 + ((YY - H / 2) / (H * .8)) ** 2)).clip(.35, 1)[..., None]
GRAIN = [rng.normal(0, 1, (H, W)).astype(np.float32)[..., None] for _ in range(4)]
def smooth_noise(seed, scale):
    r = np.random.default_rng(seed).random((H // scale + 2, W // scale + 2)).astype(np.float32)
    im = Image.fromarray((r * 255).astype(np.uint8)).resize((W + 2 * scale, H + 2 * scale), Image.BICUBIC)
    return np.asarray(im, np.float32)[scale:scale + H, scale:scale + W] / 255
PIGMENT = smooth_noise(4, int(110 * S)) * .55 + smooth_noise(5, int(28 * S)) * .3 + smooth_noise(6, int(7 * S) or 1) * .15

def blur(a, r):
    s = 4; small = pil(a).resize((W // s, H // s), Image.BILINEAR).filter(ImageFilter.GaussianBlur(r / s))
    return arr(small.resize((W, H), Image.BILINEAR))
def radial(cx, cy, r, col, k):
    return (np.exp(-((XX - cx) ** 2 + (YY - cy) ** 2) / (r * r))[..., None] * np.array(col, np.float32)) * k

def grade(a, temp=0.0, sat=1.0, lift=0.0, contrast=1.06):
    """temp < 0 frio (azul/cinza), > 0 quente (dourado/marfim). Preserva a textura: contraste moderado."""
    lum = (a @ np.array([.299, .587, .114], np.float32))[..., None]
    a = lum + (a - lum) * sat
    if temp < 0: a = a + (np.array([-.03, -.005, .035], np.float32) * (1 - lum) + np.array([-.02, 0, .015], np.float32) * lum) * -temp
    else: a = a + (np.array([.035, .015, -.03], np.float32) * lum + np.array([.02, .01, -.01], np.float32)) * temp
    return np.clip(.5 + (a - .5) * contrast + lift, 0, 1)

# ── atmosfera (animada à parte da pintura) ──────────────────────────────────
MIST = arr(Image.open(ROOT / 'assets/experience/mist.webp').convert('RGBA').resize((int(2048 * S) or 1, H)))[..., 3]
def mist(t, k, speed=14, y0=0.0, y1=1.0, scale=1.0):
    o = int(t * speed * S) % MIST.shape[1]; m = np.concatenate([MIST, MIST], 1)[:, o:o + W]
    if m.shape[1] < W: m = np.pad(m, ((0, 0), (0, W - m.shape[1])), mode='wrap')
    band = np.clip((YY[:, :1] / H - y0) / .15, 0, 1) * np.clip((y1 - YY[:, :1] / H) / .15, 0, 1)
    return (m * band)[..., None] * np.array([.78, .82, .86], np.float32) * k
def rain_sheet(seed, n, length, slant):
    r = np.random.default_rng(seed); sh = Image.new('L', (W, H * 2), 0); d = ImageDraw.Draw(sh)
    for _ in range(int(n * W * H / 2e6)):
        x, y = r.uniform(-200, W), r.uniform(0, H * 2); l = r.uniform(.6, 1.2) * length * S
        d.line([(x, y), (x + slant * l, y + l)], fill=int(r.uniform(.35, 1) * 255), width=1)
    return arr(sh.filter(ImageFilter.GaussianBlur(.5)))
RAIN = [rain_sheet(11, 2200, 34, .12), rain_sheet(12, 700, 80, .15)]
def rain(t, k):
    out = 0
    for sheet, sp, g in zip(RAIN, (1700, 2300), (.3, .5)):
        off = int(t * sp * S) % H; out = out + sheet[H - off: 2 * H - off] * g
    return (out[..., None] * np.array([.8, .86, .92], np.float32)) * k
def ripple(a, t, horizon, amp=1.6, wl=9.0, speed=1.4):
    """Ondulação mínima só abaixo da linha d'água."""
    m = np.clip((YY - horizon * H) / (H * .08), 0, 1)
    dx = amp * S * m * np.sin(YY / (wl * S) + t * speed + np.sin(XX / (90 * S)) * 1.5)
    idx = np.clip((XX + dx).astype(np.int32), 0, W - 1)
    return np.take_along_axis(a, np.repeat(idx[..., None], 3, 2), 1)
def glint(cx, cy, r, t, t0, dur=1.2):
    k = (t - t0) / dur
    if not 0 <= k <= 1: return 0
    band = np.exp(-(((XX - cx) - (YY - cy) * .8 - (k * 2 - 1) * r * 1.4) / (r * .18)) ** 2)
    return (band * np.exp(-((XX - cx) ** 2 + (YY - cy) ** 2) / (r * r)))[..., None] * np.array([1, .9, .7], np.float32) * .55 * math.sin(math.pi * k)
def splashes(t, x0, x1, y0, y1, n=40, seed=7):
    r = np.random.default_rng(seed); out = 0
    for _ in range(n):
        px, py, ph = r.uniform(x0, x1) * W, r.uniform(y0, y1) * H, r.uniform(0, 1)
        life = (t * 1.6 + ph) % 1
        if life < .35: out = out + radial(px, py, (2 + 10 * life) * S, (.85, .9, .95), .5 * (1 - life / .35))
    return out

# ── tipografia ──────────────────────────────────────────────────────────────
TMP = Path('/tmp/claude-0/trailer_fonts'); TMP.mkdir(parents=True, exist_ok=True)
def ttf(woff, name):
    p = TMP / name
    if not p.exists(): f = TTFont(ROOT / 'assets/fonts' / woff); f.flavor = None; f.save(p)
    return str(p)
F_LINE = ttf('cormorant-400-italic.woff2', 'ital.ttf'); F_CAPS = ttf('cormorant-500.woff2', 'caps.ttf'); F_CAPS6 = ttf('cormorant-600.woff2', 'caps6.ttf')
_tc = {}
def text_layer(text, font, size, color, tracking=0.0, maxw=None):
    key = (text, font, size, color, tracking, maxw)
    if key in _tc: return _tc[key]
    f = ImageFont.truetype(font, size); words = text.split(' '); lines, cur = [], ''
    maxw = maxw or W * (.86 if VERT else .78)
    width = lambda s: sum(f.getlength(c) for c in s) + tracking * size * max(0, len(s) - 1)
    for w_ in words:
        cand = (cur + ' ' + w_).strip()
        if width(cand) > maxw and cur: lines.append(cur); cur = w_
        else: cur = cand
    lines.append(cur)
    lh = int(size * 1.28); im = Image.new('L', (int(maxw + size), lh * len(lines) + size // 2), 0); d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        x = (im.width - width(ln)) / 2
        for c in ln: d.text((x, i * lh), c, font=f, fill=255); x += f.getlength(c) + tracking * size
    m = arr(im); _tc[key] = (m, np.array(color, np.float32) / 255); return _tc[key]

def title(a, text, t, t0, t1, y=.82, size=70, font=F_LINE, color=(244, 237, 222), tracking=0.0, mask_reveal=True, shade=True):
    """Fade + revelação por máscara + movimento mínimo (sobe 6 px). Faixa de sombra discreta para leitura."""
    if not (t0 <= t < t1): return a
    size = int(size * S * (1.18 if VERT else 1)); m, col = text_layer(text, font, size, color, tracking)
    k_in = ease((t - t0) / .9); k_out = ease((t1 - t) / .7); alpha = min(k_in, k_out)
    h, w = m.shape; x0 = int(W / 2 - w / 2); y0 = int(y * H - h / 2 + (1 - k_in) * 6 * S)
    if mask_reveal:
        edge = (ease((t - t0) / 1.4)) * (w + 80 * S); m = m * np.clip((edge - np.arange(w)[None, :]) / (80 * S), 0, 1)
    ys, xs = slice(max(0, y0), min(H, y0 + h)), slice(max(0, x0), min(W, x0 + w))
    sub = m[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0] * alpha
    if shade:
        band = np.exp(-((YY[:, :1] - (y0 + h / 2)) / (h / 2 + 60 * S)) ** 4)[..., None] * alpha
        a = a * (1 - .42 * band) if col[0] > .5 else a * (1 - .5 * band) + band * .5 * np.array([.94, .9, .8], np.float32)
    glow = pil(np.repeat(sub[..., None], 3, 2)).filter(ImageFilter.GaussianBlur(6 * S)); g = arr(glow)[..., :1]
    reg = a[ys, xs]
    if col[0] > .5: reg = reg + g * col * .25
    a[ys, xs] = reg * (1 - sub[..., None] * .96) + sub[..., None] * col
    return a

# ── materiais ───────────────────────────────────────────────────────────────
A = lambda n: img(f'assets/art/{n}.webp')
SEA0 = img('assets/art/primeiros-sinos.webp'); CH1 = A('ch1'); CH3 = A('ch3'); CH21 = A('ch21'); CH22 = A('ch22'); CH7 = A('ch7')
MAP = img('assets/maps/map_stage_1.webp'); TEST = img('assets/docs/testament.webp'); HAND = A('a-mao-e-a-lente')
DARK = A('vozes-das-baleias'); DAWN = img('assets/branding/part4.webp'); PAPER = Image.open(ROOT / 'assets/experience/letter-paper.webp').convert('RGB')
EMB = Image.open(ROOT / 'assets/branding/emblem-gold.webp').convert('RGBA')
def lighthouse_plate():
    """Composição atmosférica: a aquarela do farol (sem luz) sobre céu e mar da prancha da Parte II."""
    p2 = img('assets/branding/part2.webp'); bw, bh = p2.size
    bg = p2.crop((int(bw * .28), int(bh * .28), int(bw * .96), int(bh * .72))).resize((1536, 1024), Image.BICUBIC)
    bg = Image.fromarray((arr(bg) * np.array([.62, .68, .76]) * 255).astype(np.uint8))
    lh = Image.open(ROOT / 'assets/branding/lighthouse.webp').convert('RGB'); la = arr(lh)
    alpha = np.clip((.94 - la.mean(2)) * 9, 0, 1); alpha = arr(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)))
    rgba = Image.fromarray(np.dstack([la, alpha]).__mul__(255).astype(np.uint8), 'RGBA')
    hh = 760; rgba = rgba.resize((int(rgba.width * hh / rgba.height), hh), Image.LANCZOS)
    bg = bg.convert('RGBA'); bg.alpha_composite(rgba, (int(1536 * .55), 1024 - hh + 40)); return bg.convert('RGB')
LIGHT = lighthouse_plate()
BLACK = np.zeros((H, W, 3), np.float32)

def pigment_mix(a, b, k):
    m = np.clip((k * 1.35 - PIGMENT) * 5.5, 0, 1)[..., None]
    return a * (1 - m) + b * m

# ── planos ──────────────────────────────────────────────────────────────────
def frame(i):
    t = i / FPS; g = dict(temp=-.6, sat=.88, lift=0); a = BLACK.copy()
    # I. o mar se lembra
    if 2.0 <= t < 8.0:
        k = (t - 2) / 6
        a = window(SEA0, .28, lerp(.62, .58, eio(k)), lerp(.62, .55, eio(k)))
        a = ripple(a, t, .42) * .62
        a = a * (1 - .78 * mist_cover(t)) + mist(t, .55 * (1 - .6 * ease((t - 4) / 4)), 10, 0, 1) + mist(t * 1.6, .25, 18, .3, 1)
        a = a * ease((t - 2) / 3.2); g = dict(temp=-1, sat=.6, lift=-.01)
    # II. o funeral do faroleiro
    if 8.0 <= t < 11.6:
        k = (t - 8) / 3.6; a = window(CH1, .5, lerp(.36, .32, k), lerp(1.0, .93, k)) + rain(t, .55)
        a = a + mist(t, .12, 8, 0, .5); g = dict(temp=-1, sat=.55)
        a = title(a, 'Toda costa guarda histórias que o mar não conseguiu levar.', t, 8.7, 11.5, .86)
    if 11.6 <= t < 15.4:
        k = (t - 11.6) / 3.8; a = window(CH1, .33, lerp(.8, .82, k), lerp(.5, .45, k)) * .92
        a = a + rain(t, .65) + splashes(t, .1, .8, .55, .85); g = dict(temp=-1.1, sat=.5)
        if t < 11.9: a = a * ease((t - 11.6) / .3) + window(CH1, .5, .32, .93) * (1 - ease((t - 11.6) / .3))
        a = title(a, 'Algumas foram enterradas.', t, 12.4, 15.2, .2)
    if 15.4 <= t < 20.0:
        k = (t - 15.4) / 4.6; a = window(LIGHT, lerp(.66, .68, k), .5, lerp(.86, .82, k))
        a = a + mist(t, .3, 9, .1, .9) + rain(t, .25); g = dict(temp=-1.2, sat=.55, contrast=1.1)
        if t > 19.2: a = a * (1 - .6 * ease((t - 19.2) / .8))
    # III. o que ficou para trás
    if 20.0 <= t < 24.2:
        k = (t - 20) / 4.2; b = window(CH3, lerp(.42, .45, k), .36, lerp(.98, .9, k))
        b = b + radial(W * .22, H * .25, 520 * S, (1, .85, .6), .12 * (1 + .1 * math.sin(t * 2)))
        a = b if t > 20.8 else lerp(window(LIGHT, .68, .5, .82) * .4, b, ease((t - 20) / .8)); g = dict(temp=-.3, sat=.85)
        a = title(a, 'Outras permaneceram esperando…', t, 21.0, 24.1, .85)
    if 24.2 <= t < 27.2:
        k = (t - 24.2) / 3; a = window(CH3, .52, lerp(.78, .8, k), lerp(.55, .48, k))
        a = paper_leaf(a, t); g = dict(temp=-.2, sat=.85)
        a = title(a, '…que alguém tivesse coragem de voltar.', t, 24.6, 27.1, .14)
    if 27.2 <= t < 29.6:
        k = (t - 27.2) / 2.4; a = window(CH21, lerp(.3, .32, k), .78, lerp(.62, .56, k))
        a = a + glint(W * .36, H * .62, 230 * S, t, 27.6, 1.4); g = dict(temp=-.2, sat=.9)
    if 29.6 <= t < 30.9:
        k = (t - 29.6) / 1.4; m = window(MAP, .5, .45, lerp(.42, .2, eio(k)))
        blue = np.array([.1, .2, .3], np.float32) * (.6 + .4 * PIGMENT[..., None])
        a = pigment_mix(m, blue, ease((k - .3) / .7)); g = dict(temp=-.4, sat=.9)
    # IV. a travessia
    if 30.9 <= t < 37.6:
        k = max(0, t - 31) / 6.6; b = window(CH22, lerp(.5, .52, k), lerp(.72, .7, k), lerp(1.0, .94, k))
        b = ripple(b, t, .55, 2.2) + mist(t, .1, 12, .1, .5)
        blue = np.array([.16, .3, .42], np.float32) * (.7 + .3 * PIGMENT[..., None])
        a = pigment_mix(blue, b, ease((t - 30.9) / 1.0)) if t < 31.9 else b
        g = dict(temp=lerp(-.3, -1.0, k), sat=lerp(.95, .8, k))
        a = title(a, 'Mas há viagens que não começam quando partimos.', t, 32.2, 36.6, .14)
    if 37.6 <= t < 44.0:
        k = eio((t - 37.6) / 6.4); a = window(CH22, .5, lerp(.55, .2, k), lerp(1.0, .98, k))
        a = ripple(a, t, .7, 1.8) + mist(t, .14, 10, 0, .6); g = dict(temp=-1.0, sat=.8)
        a = title(a, 'Começam quando já não podemos continuar fugindo.', t, 38.6, 43.6, .86)
    # V. o peso do passado
    shots = [(44.0, 47.0, lambda t, k: window(HAND, lerp(.6, .62, k), lerp(.4, .42, k), lerp(.66, .6, k))),
             (47.0, 50.0, lambda t, k: reveal_doc(t, k)),
             (50.0, 52.4, lambda t, k: ripple(window(DARK, .55, .32, lerp(.52, .46, k)), t, 0, 1.6) * .8 + mist(t, .22, 16, 0, 1)),
             (52.4, 54.4, lambda t, k: window(LIGHT, .66, .5, lerp(1.0, .96, k)) * .8 + mist(t, .38, 8, 0, 1)),
             (54.4, 56.6, lambda t, k: window(CH7, lerp(.6, .62, k), .5, lerp(.74, .68, k))),
             (56.6, 59.0, lambda t, k: window(MAP, lerp(.72, .76, k), .3, lerp(.5, .44, k)))]
    for t0, t1, f in shots:
        if t0 <= t < t1:
            a = f(t, (t - t0) / (t1 - t0)); g = dict(temp=-1.3, sat=.75, contrast=1.12)
            if t - t0 < .35 and t0 > 44.0: pass
    a = title(a, 'Entre a culpa e a verdade…', t, 44.6, 47.2, .86)
    a = title(a, '…entre aquilo que perdemos…', t, 48.2, 51.8, .86)
    a = title(a, '…e aquilo que ainda podemos escolher.', t, 54.9, 58.8, .86)
    # VI. o silêncio antes da luz
    if 59.0 <= t < 60.2: a = BLACK.copy()
    if 60.2 <= t < 70.0:
        k = max(0, (t - 63) / 7)
        a = window(DAWN, lerp(.42, .44, eio(k)), lerp(.79, .77, eio(k)), lerp(.84, .76, eio(k))) if not VERT else window(DAWN, lerp(.34, .38, eio(k)), .84, lerp(.34, .3, eio(k)))
        a = ripple(a, t, .58, 1.4) + mist(t, .2 * (1 - ease((t - 61) / 7)), 8, .2, .8)
        a = a * ease((t - 60.2) / 1.6) + radial(W * .8, H * .3, 620 * S, (1, .86, .6), .1 * ease((t - 61) / 4))
        g = dict(temp=1.0, sat=.95, lift=.01)
        a = title(a, 'Porque nem toda história marcada pela perda…', t, 61.6, 65.8, .14, color=(250, 244, 230))
        a = title(a, '…precisa terminar nela.', t, 66.4, 69.8, .14, color=(250, 244, 230))
        if t > 69.2: a = a * (1 - ease((t - 69.2) / .8))
    # VII. o nome da história
    if t >= 70.0:
        base = np.array([.02, .06, .09], np.float32) * ease((t - 70) / 1.0)
        a = np.broadcast_to(base, (H, W, 3)).copy()
        ey = .42 if not VERT else .4
        a = a + radial(W / 2, H * ey, (8 + 600 * ease((t - 71) / 3.5)) * S, (1, .86, .55), .55 * ease((t - 70.8) / .6) * (1 - .6 * ease((t - 74) / 3)))
        if t >= 71.4:
            hh = int((H * .6) if not VERT else (W * .82)); e = EMB.resize((int(EMB.width * hh / EMB.height), hh), Image.LANCZOS)
            ea = arr(e); x0, y0 = (W - e.width) // 2, int(H * ey - hh / 2)
            rr = np.hypot(XX[y0:y0 + hh, x0:x0 + e.width] - W / 2, YY[y0:y0 + hh, x0:x0 + e.width] - H * ey)
            reveal = np.clip(((ease((t - 71.4) / 3.2) * hh * .8) - rr) / (60 * S), 0, 1)
            al = ea[..., 3:4] * reveal[..., None]
            a[y0:y0 + hh, x0:x0 + e.width] = a[y0:y0 + hh, x0:x0 + e.width] * (1 - al) + ea[..., :3] * al
        a = title(a, 'UMA JORNADA ENTRE A NÉVOA, O MAR E A GRAÇA', t, 74.8, 80.1, .8 if not VERT else .72, 36, F_CAPS, (226, 197, 140), .16, shade=False)
        a = title(a, 'DESCUBRA O ROMANCE. ENTRE NO ARQUIVO VIVO.', t, 76.9, 80.1, .9 if not VERT else .8, 32, F_CAPS6, (244, 237, 222), .14, shade=False)
        if t > 79.0: a = a * (1 - ease((t - 79.0)))
        g = dict(temp=.5, sat=1.0)
    a = grade(a, g.get('temp', 0), g.get('sat', 1), g.get('lift', 0), g.get('contrast', 1.06))
    lum = (a @ np.array([.3, .5, .2], np.float32))[..., None]
    a = a + blur(np.maximum(a - .72, 0), 12) * .35                     # leve bloom só nas luzes
    a = a * VIGN + GRAIN[i % 4] * .010
    return (np.clip(a, 0, 1) * 255).astype(np.uint8).tobytes()

def mist_cover(t):
    """Quanto da névoa ainda cobre a costa no início (0–1)."""
    return 1 - ease((t - 3.0) / 4.5)

LEAF = PAPER.crop((0, 0, PAPER.width, int(PAPER.width * .7)))
def paper_leaf(a, t):
    """Uma folha solta em primeiro plano, fora de foco, que se move com o vento."""
    w = int(W * (.3 if not VERT else .55)); h = int(w * LEAF.height / LEAF.width)
    ang = 3 + 2.2 * math.sin(t * 1.7) + .8 * math.sin(t * 4.3)
    lf = LEAF.resize((w, h), Image.BICUBIC).convert('RGBA').rotate(ang, Image.BICUBIC, expand=True).filter(ImageFilter.GaussianBlur(16 * S))
    la = arr(lf); x0 = int(W - w * .62 + 8 * S * math.sin(t * 1.3)); y0 = int(H - h * .42 + 10 * S * math.sin(t * 1.7))
    ys, xs = slice(max(0, y0), min(H, y0 + la.shape[0])), slice(max(0, x0), min(W, x0 + la.shape[1]))
    sub = la[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]; al = sub[..., 3:4] * .7
    a[ys, xs] = a[ys, xs] * (1 - al) + sub[..., :3] * np.array([.42, .36, .3], np.float32) * al
    return a

def reveal_doc(t, k):
    d = window(TEST, .5, lerp(.34, .38, k), lerp(.8, .72, k))
    paper = window(PAPER, .5, .5, .9)
    return pigment_mix(paper, d, ease(k * 1.4))

TEXT = [(8.7, 11.5, 'Toda costa guarda histórias que o mar não conseguiu levar.'), (12.4, 15.2, 'Algumas foram enterradas.'),
        (21.0, 24.1, 'Outras permaneceram esperando…'), (24.6, 27.1, '…que alguém tivesse coragem de voltar.'),
        (32.2, 36.6, 'Mas há viagens que não começam quando partimos.'), (38.6, 43.6, 'Começam quando já não podemos continuar fugindo.'),
        (44.6, 47.2, 'Entre a culpa e a verdade…'), (48.2, 51.8, '…entre aquilo que perdemos…'), (54.9, 58.8, '…e aquilo que ainda podemos escolher.'),
        (61.6, 65.8, 'Porque nem toda história marcada pela perda…'), (66.4, 69.8, '…precisa terminar nela.'),
        (74.8, 80.0, 'Cartas do Norte — Uma jornada entre a névoa, o mar e a graça'), (76.9, 80.0, 'Descubra o romance. Entre no Arquivo Vivo.')]

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'frames':
        out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
        for t in [float(x) for x in sys.argv[3].split(',')]:
            Image.frombuffer('RGB', (W, H), frame(int(t * FPS))).save(out / f'{t:05.1f}.png')
        sys.exit()
    dst = sys.argv[2]; n = int(DUR * FPS)
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-maxrate', '8M', '-bufsize', '16M', '-pix_fmt', 'yuv420p', '-an', dst], stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(frame, range(n), chunksize=4)):
            enc.stdin.write(buf)
            if k % 240 == 0: print(f'{k}/{n}', flush=True)
    enc.stdin.close(); enc.wait(); print('ok', dst)
