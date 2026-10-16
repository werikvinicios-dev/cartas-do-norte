#!/usr/bin/env python3
"""Trailer de Cartas do Norte — corte de impacto, trilha e desenho de som sem narração (tools/trailer_sound_v3.py). 62 s, 1920×1080 (janela 2,39:1), 24 fps.

Sem som, o impacto vem do ritmo de corte e da tipografia em movimento:
  0–6     A primeira luz      escuro; três pulsos do farol; frase escrita como tinta.
  6–11    A segunda luz       corte seco; golpes tipográficos "A SEGUNDA LUZ" / "NÃO DEVERIA EXISTIR".
  11–19   As cartas           funeral sob chuva; lacre que se parte; "DOZE CARTAS. DOZE TESTEMUNHAS. UMA MARÉ." (cap. 3)
  19–23   A rota              o mapa surge como tinta; a frase da margem da carta.
  23–35   A travessia         montagem que acelera; "ENTRE CARTAS · FARÓIS · E TRAVESSIAS".
  35–44   A tempestade        cortes de 12 a 6 quadros, relâmpagos, tremor; "UMA PAUSA" congela no preto; "OUTRAS TRÊS".
  44–62   O emblema           três clarões que tomam a tela; emblema num feixe de luz; frase final.
Só aquarelas das Partes I e II e frases do próprio romance.
Uso: python3 tools/build_trailer_v3.py
"""
import math, subprocess, os, sys
from pathlib import Path
from multiprocessing import Pool
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
import build_trailer_v2 as T
from build_trailer_v2 import (W, H, AH, BAR, BLACK, ease, eio, lerp, env, window, to_pil, blur_small, bloom, hblur,
                              VIGNETTE, GRAIN, grade, radial, beam, INK, rain, mist, text_rgba, F_BRAND, F_ITAL, F_CAPS,
                              COVER, PRO, CH1, CH3, MAP, PAPER_A, EMB, LAMP, XX, YY)
ROOT = T.ROOT; OUT = ROOT / 'assets/video'; FPS = 24; DUR = 68.0; D = 4.5   # D: duração do mergulho inserido após a tempestade
A = lambda n: T.img(f'assets/art/{n}.webp')
SEAL_L = Image.open(ROOT / 'assets/experience/wax-seal-l.webp').convert('RGBA')
SEAL_R = Image.open(ROOT / 'assets/experience/wax-seal-r.webp').convert('RGBA')

# ── tipografia em movimento ─────────────────────────────────────────────────
_masks = {}
def mask(text, font, size, y=.5, tracking=.08, color=(244, 237, 222)):
    k = (text, font, size, y, tracking)
    if k not in _masks:
        m, col = text_rgba([text], font, size, tracking, y, color)
        ys, xs = np.where(m > .02)
        _masks[k] = (m, col, (xs.min(), xs.max(), ys.min(), ys.max()) if len(xs) else (0, W, 0, AH))
    else:
        m, col, bb = _masks[k]; _masks[k] = (m, np.array(color, np.float32) / 255, bb)
    return _masks[k]

def comp(a, m, col, alpha, glow=0.0):
    m = m * alpha
    if glow: a = a + blur_small(np.repeat(m[..., None], 3, 2), 2, 10) * col * glow
    return a * (1 - m[..., None] * .95) + m[..., None] * col

def slam(a, text, dt, size=150, y=.5, color=(232, 203, 150), font=F_BRAND, hold=99, tracking=.12):
    """Golpe: a palavra cai de 1,7× com desfoque e assenta em 5 quadros; depois respira devagar."""
    if dt < 0 or dt > hold: return a
    m, col, (x0, x1, y0, y1) = mask(text, font, size, y, tracking, color)
    s = 1 + .7 * math.exp(-dt / .07) + .03 * dt
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    im = to_pil(np.repeat(m[..., None], 3, 2)).convert('L')
    w, h = W / s, AH / s
    im = im.transform((W, AH), Image.EXTENT, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), Image.BILINEAR)
    mm = np.asarray(im, np.float32) / 255
    if dt < .12: mm = hblur(np.repeat(mm[..., None], 3, 2), 14 * (1 - dt / .12))[..., 0]
    alpha = min(1, dt / .05) * (1 - ease((dt - hold + .25) / .25) if hold < 99 else 1)
    return comp(a, mm, col, alpha, glow=.9 + 1.5 * math.exp(-dt / .1))

def ink(a, text, t0, t1, size=64, y=.8, color=(244, 237, 222), font=F_ITAL, fade_out=.5, tracking=0.0, now=0):
    """Frase que se escreve da esquerda para a direita, como tinta."""
    if not (t0 <= now < t1 + fade_out): return a
    m, col, (x0, x1, y0, y1) = mask(text, font, size, y, tracking, color)
    k = ease((now - t0) / max(.4, len(text) * .045))
    edge = x0 + k * (x1 - x0 + 60)
    mm = m * np.clip((edge - XX) / 60, 0, 1)
    alpha = 1 - ease((now - t1) / fade_out)
    band = np.exp(-((YY[:, :1] - (y0 + y1) / 2) / ((y1 - y0) / 2 + 70)) ** 4)[..., None] * alpha
    if color[0] > 128: a = a * (1 - .5 * band)          # faixa escura sob texto claro
    else: a = a * (1 - .7 * band) + band * .7 * np.array([.94, .89, .78], np.float32)   # faixa de papel sob tinta
    return comp(a, mm, col, alpha, glow=.35 if color[0] > 128 else 0)

# ── câmera e cortes ─────────────────────────────────────────────────────────
def shot(im, c0, c1, w0, w1, t, t0, t1):
    k = eio((t - t0) / (t1 - t0))
    a = window(im, lerp(c0[0], c1[0], k), lerp(c0[1], c1[1], k), lerp(w0, w1, k))
    p = 1 + .09 * math.exp(-(t - t0) / .12)   # empurrão no corte
    if p > 1.002:
        im2 = to_pil(a); w, h = W / p, AH / p
        a = np.asarray(im2.transform((W, AH), Image.EXTENT, ((W - w) / 2, (AH - h) / 2, (W + w) / 2, (AH + h) / 2), Image.BILINEAR), np.float32) / 255
    return a

def aberration(a, px):
    if px < .5: return a
    o = a.copy(); s = int(round(px)); o[..., 0] = np.roll(a[..., 0], s, 1); o[..., 2] = np.roll(a[..., 2], -s, 1); return o

# Montagem (Partes I e II): imagem, centro inicial/final, largura inicial/final, extra
MONT = ['tres-pulsacoes', 'ch5', 'salinas-ao-entardecer', 'ch9', 'lanternas-de-papel', 'ch16', 'vozes-das-baleias', 'ch20',
        'primeiros-sinos', 'ch29', 'a-galeria-do-farol', 'ch31', 'oficina-de-pranchas', 'ch45', 'ch22', 'ch41', 'ch50', 'ch53']
STORMS = ['a-cidade-na-tempestade', 'ch14', 'ch37', 'ch26', 'manivela-da-lente', 'ch34', 'ch47', 'COVER', 'ch46', 'ch14']
WIDE = {n for n in MONT + STORMS if n != 'COVER' and Image.open(ROOT / f'assets/art/{n}.webp').width > Image.open(ROOT / f'assets/art/{n}.webp').height}
IM = {n: (COVER if n == 'COVER' else A(n)) for n in set(MONT + STORMS)}
def schedule(t0, t1, names, d0, d1):
    out, t, i = [], t0, 0
    while t < t1 - .05:
        k = (t - t0) / (t1 - t0); d = lerp(d0, d1, k)
        out.append((t, min(t1, t + d), names[i % len(names)])); t += d; i += 1
    return out
MONTAGE = schedule(23.0, 35.0, MONT, 1.25, .45)
STORM1 = schedule(35.0, 40.0, STORMS, .55, .26)
STORM2 = schedule(41.6 + D, 43.0 + D, STORMS[3:], .3, .25)
SLAMS = [(7.0, 'A SEGUNDA LUZ', 168, .43, (240, 214, 160)), (8.3, 'NÃO DEVERIA EXISTIR', 104, .62, (226, 96, 70)),
         (15.75, 'DOZE CARTAS', 150, .5, (240, 214, 160)), (16.85, 'DOZE TESTEMUNHAS', 132, .5, (240, 214, 160)), (17.95, 'UMA MARÉ', 176, .5, (240, 214, 160)),
         (25.0, 'ENTRE CARTAS', 150, .5, (244, 237, 222)), (28.0, 'FARÓIS', 190, .5, (244, 237, 222)), (30.8, 'E TRAVESSIAS', 150, .5, (244, 237, 222)),
         (37.5, 'TRÊS PULSAÇÕES', 150, .5, (240, 214, 160)), (40.0 + D, 'UMA PAUSA', 170, .5, (244, 237, 222)), (41.6 + D, 'OUTRAS TRÊS', 170, .5, (240, 214, 160))]
IMPACTS = [6.5, 11.0, 15.0, 16.8, 17.9, 19.0, 23.0] + [s[0] for s in SLAMS] + [m[0] for m in MONTAGE[::2]] + [s[0] for s in STORM1 + STORM2] + [40.0, 43.2 + D, 43.75 + D, 44.3 + D, 46.4 + D]
LIGHTNING = [35.3, 36.4, 37.2, 38.6, 39.3, 42.0 + D, 42.6 + D]
PULSES_END = [43.2 + D, 43.75 + D, 44.3 + D]
DROWN = (40.0, 40.0 + D)
BUBBLES = np.random.default_rng(9).random((140, 4))

def frame(i):
    t = i / FPS; g = {}
    a = BLACK.copy()
    # 1. a primeira luz
    if 1.0 <= t < 6.5:
        k = ease((t - 1.0) / 5.5); cx, cy, wf = lerp(.83, .87, k), lerp(.40, .37, k), lerp(.5, .36, k)
        lit = window(COVER, cx, cy, wf); p = sum(env(t - s, .03, .32) for s in (2.2, 2.8, 3.4))
        a = lit * (.04 + .62 * p + .55 * ease((t - 3.8) / 2.5))
        a = a + radial(W * .72, AH * .3, 60 + 150 * p, (1, .9, .62), .9 * p + .3 * ease((t - 3.8) / 2))
        if t > 3.6: a = a + beam(W * .72, AH * .3, math.pi + .7 - (t - 3.6) * .5, k=.5 * ease((t - 3.6) / 1.2))
        a = a + mist(t, .2); g = dict(bloom=.8 + p)
        a = ink(a, 'A primeira luz era a que todos esperavam.', 3.9, 6.2, now=t)
    # 2. a segunda luz
    if 6.5 <= t < 10.6:
        a = shot(PRO, (.45, .55), (.33, .25), .9, .5, t, 6.5, 10.6)
        a = a + radial(W * .45, AH * .3, 160, (1, .2, .08), .5 * (.8 + .2 * math.sin(t * 21))) + rain(t, .5)
        a = a * (.55 if t > 6.95 else 1)
        a = slam(a, SLAMS[0][1], t - SLAMS[0][0], SLAMS[0][2], .5, SLAMS[0][4], hold=1.3)
        a = slam(a, SLAMS[1][1], t - SLAMS[1][0], SLAMS[1][2], .5, SLAMS[1][4])
        g = dict(cool=.7, sat=.8)
    # 3. funeral, lacre, doze cartas
    if 11.0 <= t < 15.0:
        a = shot(CH1, (.5, .2), (.5, .6), 1.0, .8, t, 11.0, 15.0) + rain(t, .9); g = dict(sat=.5, cool=1.0)
        a = ink(a, 'Choveu no funeral de Jonas Vale.', 11.6, 14.4, now=t)
    if 15.0 <= t < 16.8:
        a = PAPER_A.copy() * .95; g = dict(warm=.8)
        sp = ease((t - 15.35) / .35) if t > 15.35 else 0
        for half, sgn in ((SEAL_L, -1), (SEAL_R, 1)):
            h = int(AH * .62); im = half.resize((h, h), Image.LANCZOS).rotate(-sgn * 35 * sp, Image.BICUBIC, expand=False)
            arr = np.asarray(im, np.float32) / 255; x0 = int(W / 2 - h / 2 + sgn * 260 * sp); y0 = int(AH / 2 - h / 2 + 120 * sp ** 2)
            xs, ys = slice(max(0, x0), min(W, x0 + h)), slice(max(0, y0), min(AH, y0 + h))
            sub = arr[ys.start - y0: ys.stop - y0, xs.start - x0: xs.stop - x0]
            al = sub[..., 3:4] * (1 - ease((t - 15.6) / .5))
            a[ys, xs] = a[ys, xs] * (1 - al) + sub[..., :3] * al
        if t > 15.75: a = a * .35
        a = slam(a, *SLAMS[2][1:3], y=SLAMS[2][3], color=SLAMS[2][4]) if False else slam(a, SLAMS[2][1], t - SLAMS[2][0], SLAMS[2][2], SLAMS[2][3], SLAMS[2][4])
    if 16.8 <= t < 17.9:
        a = shot(CH3, (.5, .45), (.55, .4), .95, .8, t, 16.8, 17.9) * .45; g = dict(warm=.3)
        a = slam(a, SLAMS[3][1], t - SLAMS[3][0], SLAMS[3][2], SLAMS[3][3], SLAMS[3][4])
    if 17.9 <= t < 19.0:
        a = shot(COVER, (.55, .75), (.6, .7), .6, .45, t, 17.9, 19.0) * .45; g = dict(cool=.9)
        a = slam(a, SLAMS[4][1], t - SLAMS[4][0], SLAMS[4][2], SLAMS[4][3], SLAMS[4][4])
    # 4. a rota
    if 19.0 <= t < 23.0:
        k = (t - 19.0) / 4.0
        m = window(MAP, .45, lerp(.6, .55, k), lerp(.95, .72, eio(k)))
        rev = np.clip((ease((t - 19.0) / 1.6) * 1.25 - INK) * 6, 0, 1)[..., None]
        a = PAPER_A * (1 - rev) + m * rev; g = dict(warm=.6)
        a = a * (1 - .35 * ease((t - 19.8) / .6))
        a = ink(a, 'Uma rota não é segura porque alguém', 20.0, 22.5, 80, .44, (30, 20, 10), now=t)
        a = ink(a, 'a desenhou com régua.', 20.9, 22.5, 80, .6, (30, 20, 10), now=t)
    if 22.8 <= t < 23.0: a = hblur(np.roll(a, int(260 * (t - 22.8) / .2), 1), 80 * (t - 22.8) / .2)
    # 5. a travessia
    for t0, t1, n in MONTAGE:
        if t0 <= t < t1:
            a = shot(IM[n], (.3, .5), (.7, .45), 1.0, .82, t, t0, t1) if n in WIDE else shot(IM[n], (.5, .3), (.5, .62), 1.0, .9, t, t0, t1)
            g = dict(warm=.5, sat=1.05)
            if t - t0 < .12: a = hblur(np.roll(a, int(-200 * (1 - (t - t0) / .12)), 1), 50 * (1 - (t - t0) / .12))
    for s in SLAMS[5:8]:
        if s[0] <= t < s[0] + 1.5: a = slam(a * .55, s[1], t - s[0], s[2], s[3], s[4])
    # 6. a tempestade
    for t0, t1, n in STORM1 + STORM2:
        if t0 <= t < t1:
            a = shot(IM[n], (.5, .4), (.5, .6), .95, .75, t, t0, t1) * .7 + rain(t, 1.1); g = dict(cool=1.4, sat=.75)
    if 37.5 <= t < 39.0: a = slam(a * .5, SLAMS[8][1], t - 37.5, SLAMS[8][2], SLAMS[8][3], SLAMS[8][4])
    if 40.0 + D <= t < 41.6 + D:
        a = BLACK.copy()
        a = slam(a, SLAMS[9][1], t - (40.0 + D), SLAMS[9][2], SLAMS[9][3], SLAMS[9][4], hold=.9)
    if 41.6 + D <= t < 43.0 + D: a = slam(a * .5, SLAMS[10][1], t - (41.6 + D), SLAMS[10][2], SLAMS[10][3], SLAMS[10][4])
    if (35.0 <= t < 40.0) or (41.6 + D <= t < 43.0 + D):
        amp = 6 + 10 * ease((t - 35) / 8); dx, dy = amp * math.sin(t * 47), amp * math.sin(t * 59 + 1)
        a = np.roll(np.roll(a, int(dx), 1), int(dy), 0)
    lt = sum(env(t - s, .015, .1) for s in LIGHTNING)
    if lt: a = a * (1 + .7 * min(lt, 1.2)) + np.array([.5, .56, .72], np.float32) * min(lt, 1.2) * .22
    # 7. clarões e emblema
    if 43.0 + D <= t < 46.4 + D:
        a = BLACK.copy()
        for s in PULSES_END:
            e = env(t - s, .02, .3); a = a + radial(W / 2, AH / 2, 100 + 1200 * (t - s) * (t >= s), (1, .9, .7), 1.4 * e)
        g = dict(bloom=1.2)
    # 6b. o mergulho: a câmera afunda, a água ondula, bolhas sobem
    if DROWN[0] <= t < DROWN[1]:
        k = (t - DROWN[0]) / D
        base = window(T.img('assets/art/ch14.webp'), .5, lerp(.55, .8, eio(k)), lerp(.9, .6, k))
        wob = (8 + 10 * k) * np.sin(YY / 38 + t * 5.5)[..., None]
        base = np.take_along_axis(base, np.clip((XX[..., None] + wob).astype(int), 0, W - 1).repeat(3, 2), 1)
        lum = base @ np.array([.3, .5, .2], np.float32)
        a = lum[..., None] * np.array([.18, .42, .55], np.float32) * (1 - .55 * k) + np.array([.0, .03, .06], np.float32)
        rays = np.clip(np.sin((XX - YY * .35) / 70 + t * .8) * np.sin((XX + YY * .2) / 130 - t * .5), 0, 1) ** 3
        a = a + (rays * np.exp(-YY / (AH * .7)))[..., None] * np.array([.25, .45, .5], np.float32) * (1 - k)
        for bx, by, br, bs in BUBBLES:
            y = AH * (1.1 - ((t - DROWN[0]) * (.25 + bs * .5) + by) % 1.2); x = W * bx + 12 * math.sin(t * 3 + by * 9)
            a = a + radial(x, y, 3 + 9 * br, (.6, .85, .95), .35)
        a = blur_small(a, 2, 1.5) * .6 + a * .4
        a = ink(a, 'Havia gente trancada onde os registros', DROWN[0] + .5, DROWN[1] - .3, 62, .45, now=t, fade_out=.3)
        a = ink(a, 'diziam que só existiam caixas.', DROWN[0] + 1.6, DROWN[1] - .3, 62, .58, now=t, fade_out=.3)
        a = a * (1 - ease((t - (DROWN[1] - .5)) / .5)); g = dict(cool=1.2, sat=.8)
    if t >= 46.4 + D:
        k = ease((t - (46.4 + D)) / 1.6); sc = lerp(1.08, 1.0, eio((t - (46.4 + D)) / 5))
        h = int(AH * .82 * sc); e = EMB.resize((int(EMB.width * h / EMB.height), h), Image.LANCZOS)
        ea = np.asarray(e, np.float32) / 255; x0, y0 = (W - e.width) // 2, int(AH * .44 - h / 2)
        lay = np.zeros((AH, W, 4), np.float32); ys0, xs0 = max(0, y0), max(0, x0)
        lay[ys0:y0 + h, xs0:x0 + e.width] = ea[ys0 - y0:AH - y0, xs0 - x0:]
        pos = (t - (46.8 + D)) * 1300 - 400; band = np.exp(-(((XX - x0) + (YY - y0) * .6 - pos) / 80) ** 2)[..., None]
        al = lay[..., 3:4] * k
        a = BLACK * (1 - al) + lay[..., :3] * al * (1 + 1.8 * band) + radial(W / 2, AH * .44, 700, (1, .85, .55), .12 * k)
        if t > 49.5 + D: a = slam(a, 'O ARQUIVO VIVO', t - (49.5 + D), 52, .93, (226, 197, 140), F_CAPS, tracking=.6)
        if t > 53.0 + D:
            f = ease((t - (53.0 + D)) / .8); a = a * (1 - .75 * f)
            a = ink(a, 'Há histórias que não terminam na última página.', 53.6 + D, 59.5 + D, 66, .5, now=t, fade_out=1.0)
        g = dict(bloom=1.0, warm=.4)
    # pós: clarão, tremor, aberração, cor, grão
    imp = sum(env(t - s, .01, .09) for s in IMPACTS if t >= s)
    if imp: a = a + min(imp, 1) * .28
    a = aberration(a, 9 * min(1, sum(env(t - s, .01, .12) for s in IMPACTS if t >= s)))
    a = grade(a, g.get('warm', 0), g.get('cool', 0), g.get('sat', 1), g.get('gamma', 1))
    a = bloom(a, .35 * g.get('bloom', 1))
    a = a * VIGNETTE + GRAIN[i % 6] * .012
    if t > DUR - 2.0: a = a * (1 - ease((t - (DUR - 2.0)) / 2.0))
    out = np.zeros((H, W, 3), np.uint8); out[BAR:BAR + AH] = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    return out.tobytes()

LINES = [(3.9, 6.2, 'A primeira luz era a que todos esperavam.'), (7.0, 10.5, 'A segunda luz não deveria existir.'),
         (11.6, 14.4, 'Choveu no funeral de Jonas Vale.'), (15.75, 19.0, 'Doze cartas. Doze testemunhas. Uma maré.'),
         (20.0, 22.5, 'Uma rota não é segura porque alguém a desenhou com régua.'), (25.0, 32.3, 'Entre cartas, faróis e travessias.'),
         (40.5, 44.2, 'Havia gente trancada onde os registros diziam que só existiam caixas.'), (37.5, 47.5, 'Três pulsações. Uma pausa. Outras três.'), (54.0, 57.5, 'Cartas do Norte — O Arquivo Vivo.'),
         (58.1, 64.5, 'Há histórias que não terminam na última página.')]
def vtt():
    f = lambda s: f'00:{int(s // 60):02d}:{s % 60:06.3f}'
    return 'WEBVTT\n\n' + '\n\n'.join(f'{f(a)} --> {f(b)}\n{t}' for a, b, t in LINES) + '\n'

def cues():
    return dict(slams=[x[0] for x in SLAMS], montage=[m[0] for m in MONTAGE], lightning=LIGHTNING, storm=[x[0] for x in STORM1 + STORM2],
                pulses=PULSES_END, emblem=46.4 + D)

def build_sound(wav):
    import trailer_sound_v3
    trailer_sound_v3.build(str(wav), cues())

def mux(video, wav, out):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(video), '-i', str(wav), '-c:v', 'copy',
                    '-af', 'loudnorm=I=-14:TP=-1.0:LRA=12', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', str(out)], check=True)

if __name__ == '__main__' and '--sound-only' in sys.argv:
    build_sound(OUT / '_trailer.wav'); print('som ok'); sys.exit()

if __name__ == '__main__':
    n = int(DUR * FPS)
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-preset', 'slow', '-crf', '24', '-maxrate', '4M', '-bufsize', '8M', '-pix_fmt', 'yuv420p',
                            '-movflags', '+faststart', '-an', str(OUT / '_trailer_video.mp4')], stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(frame, range(n), chunksize=4)):
            enc.stdin.write(buf)
            if k % 240 == 0: print(f'{k}/{n}', flush=True)
    enc.stdin.close(); enc.wait()
    wav = OUT / '_trailer.wav'; build_sound(wav)
    mux(OUT / '_trailer_video.mp4', wav, OUT / 'trailer.mp4'); (OUT / '_trailer_video.mp4').unlink(); wav.unlink()
    Image.frombuffer('RGB', (W, H), frame(int(50.5 * FPS))).resize((1280, 720), Image.LANCZOS).save(OUT / 'trailer-poster.webp', quality=84)
    (OUT / 'trailer.vtt').write_text(vtt())
    print('ok', OUT / 'trailer.mp4')
