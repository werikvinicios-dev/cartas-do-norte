#!/usr/bin/env python3
"""Som do vídeo promocional (32,6 s): a faixa "Amazing Grace (lofi instrumental)" com efeitos discretos de papel e lacre.

A faixa começa de modo que a entrada da bateria (46,42 s na gravação) caia em 17,6 s no vídeo, no corte para o mosaico.
Efeitos: um brilho leve quando o emblema termina de se montar, sopro de papel em cada cortina dourada, o carimbo
do lacre, o lacre se partindo, a aba e a folha, um toque a cada pino da rota. Uso: python3 tools/promo/promo_som.py <faixa> <saida.wav>
"""
import subprocess, sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
BEAT = .858; BAR = 3 * BEAT; DROP = 15.0 + BAR; DUR = 30.0 + BAR; N = int(SR * DUR)
CUTS = [DROP - 4 * BAR, DROP - 2 * BAR, DROP, DROP + 2 * BAR, DROP + 4 * BAR]
rng = np.random.default_rng(7)

def env(n, a, d):
    e = np.ones(n); A = int(a * SR); D = int(d * SR)
    if A: e[:A] = np.linspace(0, 1, A)
    if D: e[-D:] *= np.exp(-np.linspace(0, 6, D))
    return e

def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, hi], 'bandpass', fs=SR, output='sos'), x)

def whoosh(d=.8):
    n = int(d * SR); x = bp(rng.normal(0, 1, n), 300, 4000); t = np.linspace(0, 1, n)
    return x * np.sin(np.pi * t) ** 2 * .18

def thock():
    n = int(.5 * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 90 * t * (1 - .35 * t)) * np.exp(-t * 18)
    click = bp(rng.normal(0, 1, n), 1500, 6000) * np.exp(-t * 90) * .5
    return (body + click) * .55

def crack():
    n = int(.35 * SR); x = np.zeros(n)
    for k in range(9):
        i = int(rng.uniform(0, .22) * SR); m = int(.012 * SR)
        x[i:i + m] += bp(rng.normal(0, 1, m), 900, 7000) * np.exp(-np.linspace(0, 5, m)) * rng.uniform(.3, 1)
    return x * .45

def rustle(d=.7):
    n = int(d * SR); x = bp(rng.normal(0, 1, n), 1200, 7000)
    mod = np.clip(signal.sosfilt(signal.butter(2, 18, 'lowpass', fs=SR, output='sos'), np.abs(rng.normal(0, 1, n))) * 3, 0, 1)
    return x * mod * env(n, .05, .3) * .22

def shimmer():
    n = int(2.2 * SR); t = np.arange(n) / SR
    tones = sum(np.sin(2 * np.pi * f * t + k) for k, f in enumerate((1396.9, 1760.0, 2093.0)))   # fá, lá, dó: acorde de fá maior, o tom da faixa
    return tones * np.exp(-t * 2.2) * np.clip(t / .08, 0, 1) * .025

def tick():
    n = int(.12 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1800 * t) * .4 + bp(rng.normal(0, 1, n), 2500, 8000)) * np.exp(-t * 60) * .12

def add(buf, t, y, pan=0.):
    i = int(t * SR); j = min(N, i + len(y))
    if j > i:
        buf[i:j, 0] += y[:j - i] * np.sqrt((1 - pan) / 2) * 1.4
        buf[i:j, 1] += y[:j - i] * np.sqrt((1 + pan) / 2) * 1.4

def build(track, out):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{46.424 - DROP:.3f}', '-t', f'{DUR}', '-i', track,
                          '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    music = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)[:N]
    music = np.pad(music, ((0, N - len(music)), (0, 0)))
    t = np.arange(N) / SR
    music *= np.clip(t / .8, 0, 1)[:, None] * np.clip((DUR - t) / 1.6, 0, 1)[:, None]
    fx = np.zeros((N, 2))
    for c in CUTS:
        if c != DROP: add(fx, c - .45, whoosh(), pan=-.3)
    add(fx, 6.25, shimmer())                            # o emblema montado
    add(fx, CUTS[0] + 1.3, thock())                       # o lacre carimba a carta
    add(fx, CUTS[0] + 3.45, crack(), pan=.1)              # o lacre se parte
    add(fx, CUTS[0] + 3.7, rustle(.6), pan=-.2)           # a aba abre
    add(fx, CUTS[0] + 4.1, rustle(.8), pan=.2)            # a folha sobe
    for at in (0, .36, .7, 1):                            # pinos da rota no mapa
        add(fx, CUTS[1] + 1.6 + at * 2.4, tick(), pan=-.4 + at * .8)
    mix = music * .9 + fx
    mix = mix / np.max(np.abs(mix)) * .9
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
