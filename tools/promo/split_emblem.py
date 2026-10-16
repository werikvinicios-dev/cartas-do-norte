#!/usr/bin/env python3
"""Separa o emblema (assets/branding/emblem-gold.webp) em camadas para a montagem animada do vídeo promocional.

Cada pixel pertence a exatamente uma camada (prioridade abaixo), então empilhar as camadas reproduz o emblema original.
Saída: tools/promo/emblem/<camada>.webp (mesmo tamanho do original, transparente fora da camada).
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

SRC = Path('assets/branding/emblem-gold.webp'); OUT = Path('tools/promo/emblem')
im = np.asarray(Image.open(SRC).convert('RGBA')); H, W = im.shape[:2]
yy, xx = np.mgrid[0:H, 0:W]
def box(x0, y0, x1, y1): return (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
# regiões (coordenadas do emblema 831×898), na ordem de prioridade
rr = np.hypot(xx - 411, yy - 476)          # distância ao centro do aro (aro duplo entre ~336 e ~358, marcas a partir de ~296)
ring = rr >= 342
R = {}
R['letras'] = box(388, 30, 425, 68) | box(388, 848, 425, 885) | box(0, 462, 34, 500) | box(782, 462, 815, 505)
R['cartas'] = (box(58, 346, 772, 512) | box(58, 512, 300, 536) | box(180, 315, 238, 350)) & ~ring
R['do'] = (box(236, 498, 650, 548) & ~box(236, 498, 300, 512)) & ~ring
R['norte'] = (box(95, 535, 735, 700) | box(560, 650, 740, 742)) & ~ring
R['estrela'] = box(390, 62, 422, 360) | box(300, 148, 512, 262) & ~box(470, 225, 600, 290) | box(390, 745, 422, 848)
R['passaros'] = box(482, 228, 600, 290)
R['montanhas'] = box(185, 222, 680, 362) & (rr < 296) & ~box(180, 315, 238, 350)
R['mar'] = box(220, 680, 600, 795) & (rr < 296)
order = ['letras', 'estrela', 'passaros', 'cartas', 'montanhas', 'do', 'norte', 'mar']
label = np.full((H, W), 'aro', dtype=object); taken = np.zeros((H, W), bool)
for k in order:
    m = R[k] & ~taken; label[m] = k; taken |= m
OUT.mkdir(parents=True, exist_ok=True)
total = np.zeros_like(im, dtype=float)
for k in order + ['aro']:
    layer = im.copy(); layer[label != k] = 0
    Image.fromarray(layer).save(OUT / f'{k}.webp', lossless=True, quality=100)
    total += layer
assert np.array_equal(total.astype(np.uint8), im), 'as camadas não recompõem o emblema'
if len(sys.argv) > 1:   # prévia colorida para conferência
    pal = {'aro': (200, 160, 80), 'letras': (255, 80, 80), 'cartas': (80, 160, 255), 'do': (80, 255, 200), 'norte': (160, 100, 255),
           'estrela': (255, 255, 90), 'passaros': (255, 120, 220), 'montanhas': (90, 220, 90), 'mar': (90, 200, 255)}
    prev = np.zeros((H, W, 3), np.uint8) + np.array([4, 22, 32], np.uint8)
    a = im[..., 3:4] / 255
    for k, c in pal.items():
        m = label == k; prev[m] = (prev[m] * (1 - a[m]) + np.array(c) * a[m]).astype(np.uint8)
    Image.fromarray(prev).save(sys.argv[1])
print('ok', OUT)
