#!/usr/bin/env python3
"""Trilha e desenho de som do trailer v3 (sem narração). 68 s, 48 kHz, estéreo.

Sincronizado com tools/build_trailer_v3.py:
  1–6.5   escuro, mar e vento; três pulsos graves; harmônicos de cordas; subida.
  6.5     impacto + braam; golpes "A SEGUNDA LUZ / NÃO DEVERIA EXISTIR".
  11–15   funeral: chuva, piano grave, cordas em ré menor.
  15–19   lacre que estala; três impactos crescentes (DOZE CARTAS / TESTEMUNHAS / UMA MARÉ).
  19–23   o mapa: papel, relógio que acelera, subida.
  23–35   a travessia: ostinato de cordas e tambores a 120 bpm, braams nos títulos, chicotes nos cortes.
  35–40   a tempestade: tutti, taiko, trovões, gritos de socorro ao longe.
  40–44.5 o mergulho: tudo abafado sob a água — bolhas, borbulhar, coração, gritos submersos que se apagam.
  44.5–46 a pausa: silêncio absoluto.
  46.1    "OUTRAS TRÊS": a tempestade volta de uma vez.
  47.7–49 três clarões: três impactos enormes.
  50.9    o emblema: braam, ré maior, coro e piano; decaimento.
Gritos: vozes neurais (Kokoro pf_dora, pm_alex, pm_santa) gritando "Socorro!", tratadas como gritos distantes
(esforço, saturação, distância, chuva por cima) e, no mergulho, filtradas como ouvidas debaixo d'água.
"""
import math, sys
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).parent))
import trailer_audio as TA
from trailer_audio import (SR, Bus, at, lp, hp, bp, nm, mtof, saw, piano, cello, ostinato, strings_chord, choir_note,
                           boom, taiko, braam, riser, whoosh, hit, thunder, bell, reverb, ogg, CH, adsr, VOICES)
DUR = 68.0; N = int(DUR * SR); T = np.arange(TA.N) / SR
rng = np.random.default_rng(23)
D = 4.5; DROWN = (40.0, 44.5); PAUSE = (44.5, 46.1)

def curve(points): xs, ys = zip(*points); return np.interp(T, xs, ys)

# ── gritos ──────────────────────────────────────────────────────────────────
def screams():
    from kokoro_onnx import Kokoro
    k = Kokoro(str(VOICES / 'kokoro-v1.0.onnx'), str(VOICES / 'voices-v1.0.bin'))
    takes = []
    for voice, text, speed in [('pf_dora', 'Socorro!', 1.15), ('pm_alex', 'Socorro! Socorro!', 1.2), ('pm_santa', 'Me ajudem!', 1.15),
                               ('pf_dora', 'Aqui! Socorro!', 1.2), ('pm_alex', 'Não!', 1.0), ('pm_santa', 'Socorro!', 1.25)]:
        a, sr = k.create(text, voice=voice, speed=speed, lang='pt-br')
        a = a.astype(np.float64)
        nz = np.where(np.abs(a) > .01)[0]; a = a[nz[0]:nz[-1] + 1]
        # esforço: +5 semitons com leve oscilação de altura, saturação e banda de grito
        ratio = 2 ** (5 / 12)
        n_out = int(len(a) / ratio * SR / sr)
        tt = np.arange(n_out) / SR
        src = np.cumsum(ratio * sr / SR * (1 + .035 * np.sin(2 * np.pi * 6.5 * tt)))
        src = np.clip(src, 0, len(a) - 2)
        y = np.interp(src, np.arange(len(a)), a)
        y = np.tanh(y / (np.max(np.abs(y)) + 1e-9) * 3.2)
        y = bp(y, 450, 3800, 2) * np.minimum(1, tt / .02)
        takes.append(y / (np.max(np.abs(y)) + 1e-9))
    return takes

def wail(f0=520, d=1.6, fall=.35):
    """Grito sintético em 'a': altura que sobe e despenca, tremor e ar."""
    n = int(d * SR); t = np.arange(n) / SR
    f = f0 * (1 + .12 * np.sin(np.pi * t / d)) * (1 - fall * (t / d) ** 2) * (1 + .02 * rng.normal(0, 1, n).cumsum() / np.sqrt(n))
    x = 2 * ((np.cumsum(f) / SR) % 1) - 1 + .25 * rng.normal(0, 1, n)
    v = sum(bp(x, fc * .88, fc * 1.12) * g for fc, g in [(850, 1), (1250, .7), (2700, .3)])
    return np.tanh(v * 3) * adsr(n, .06, .2, .9, .4, .9)

# ── debaixo d'água ──────────────────────────────────────────────────────────
def bubbles(d, density=26):
    n = int(d * SR); x = np.zeros(n)
    for _ in range(int(density * d)):
        s = rng.integers(0, n - 4000); L = int(rng.uniform(.015, .06) * SR); t = np.arange(L) / SR
        f = rng.uniform(250, 900) * (1 + 3 * t / t[-1])
        x[s:s + L] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * rng.uniform(40, 90)) * rng.uniform(.3, 1)
    return x
def gurgle(d):
    n = int(d * SR); t = np.arange(n) / SR
    return bp(rng.normal(0, 1, n), 120, 650, 2) * (.5 + .5 * np.sin(2 * np.pi * (9 + 4 * np.sin(t * 1.3)) * t)) * .8
def heartbeat(start, d, bpm0=72, bpm1=140):
    out = []; t = 0.0
    while t < d:
        bpm = bpm0 + (bpm1 - bpm0) * t / d; out.append(start + t); out.append(start + t + .18); t += 60 / bpm
    return out
def thump(): t = np.arange(int(.35 * SR)) / SR; return np.sin(2 * np.pi * (55 + 30 * np.exp(-t * 30)) * t) * np.exp(-t * 14)

def crack():
    t = np.arange(int(.5 * SR)) / SR; x = hp(rng.normal(0, 1, len(t)), 1800) * np.exp(-t * 55)
    x += bp(rng.normal(0, 1, len(t)), 300, 2500) * np.exp(-(t - .12).clip(0) * 8) * (t > .12) * .3
    return x
def tick(): t = np.arange(int(.03 * SR)) / SR; return hp(rng.normal(0, 1, len(t)), 2500) * np.exp(-t * 160) * .6

# ── composição ──────────────────────────────────────────────────────────────
def build(path, cues):
    mus, sfx, amb, cry, under = Bus(), Bus(), Bus(), Bus(), Bus()
    # 1. a primeira luz
    for s in (2.2, 2.8, 3.4): sfx.add(s, boom(2.6, 52, 24), 1.0); mus.add(s, piano(nm('D1') + 12, 4, 1.0), .6)
    strings_chord(mus, 3.8, 3.0, ['A5', 'D6'], .14, 7000, 2.0)
    sfx.add(4.6, riser(1.9), .7)
    # 2. a segunda luz
    sfx.add(6.5, hit(3.5), 1.1); mus.add(6.5, braam(5, 26), .9)
    mus.add(6.5, np.stack([lp(saw(mtof(26), int(4.1 * SR)), 140)] * 2, 1) * adsr(int(4.1 * SR), .05, .1, 1, 1, 1)[:, None], .3)
    for s in cues['slams'][:2]: sfx.add(s, boom(1.8, 66, 30), .9)
    strings_chord(mus, 8.3, 2.3, ['D4', 'Eb4', 'A4'], .3, 3000, .2)   # dissonância na segunda luz
    # 3. funeral e cartas
    strings_chord(mus, 11.0, 4.1, CH['Dm'], .26, 1800, 1.4); mus.add(11.0, cello(nm('D2'), 4), .5)
    for k, n in enumerate(['D4', 'F4', 'A4', 'G4', 'F4', 'E4']): mus.add(11.5 + k * .62, piano(nm(n), 3.5, .7), .45, .25)
    sfx.add(15.35, crack(), .9)
    for i, s in enumerate(cues['slams'][2:5]):
        sfx.add(s, hit(2.4), .8 + .12 * i); mus.add(s, braam(2.4, 26 + 2 * i), .45 + .15 * i)
    # 4. a rota: relógio que acelera
    t = 19.0
    while t < 23.0: sfx.add(t, tick(), .5); t += .5 * (1 - .65 * (t - 19) / 4)
    strings_chord(mus, 19.0, 4.0, ['D3', 'A3', 'D4'], .22, 2400, 1.0)
    sfx.add(21.0, riser(2.0), .7); sfx.add(22.8, whoosh(.3), .8)
    # 5. a travessia: 120 bpm
    b = .5; prog = ['Dm', 'Bb', 'F', 'C', 'Dm', 'Bb', 'Gm', 'A']; dur = 12.0 / len(prog)
    for i, c in enumerate(prog):
        t0 = 23.0 + i * dur
        strings_chord(mus, t0, dur + .05, CH[c], .3 + .03 * i, 2600 + 300 * i, .15)
        mus.add(t0, choir_note(nm(CH[c][2]), dur), .04 + .02 * i)
        root = nm(CH[c][0]) - (12 if nm(CH[c][0]) > 45 else 0)
        for k in range(int(dur / (b / 2))): mus.add(t0 + k * b / 2, ostinato(root + 12 * (k % 2), b / 2 * .9, .5), .55, -.5 + (k % 2))
    t = 23.0
    while t < 35.0:
        sfx.add(t, taiko(.9, 100, 52, .7), .9, -.1); sfx.add(t + b / 2, taiko(.4, 160, 90, .3), .7, .3); t += b
    for s in cues['montage']: sfx.add(s, whoosh(.35), .45)
    for s in cues['slams'][5:8]: sfx.add(s, hit(2.2), .95); mus.add(s, braam(2.6, 26), .6)
    sfx.add(33.0, riser(2.0), .8)
    # 6. a tempestade
    sfx.add(35.0, hit(3), 1.1)
    for i, c in enumerate(['Dm', 'Bb', 'Gm', 'A']):
        t0 = 35.0 + i * 1.25
        strings_chord(mus, t0, 1.3, CH[c] + [CH[c][2][:-1] + str(int(CH[c][2][-1]) + 1)], .45, 3800, .08)
        mus.add(t0, braam(1.6, nm(CH[c][0]) - 12 if nm(CH[c][0]) > 40 else nm(CH[c][0])), .6)
        mus.add(t0, choir_note(nm(CH[c][1]) + 12, 1.25), .1)
    t = 35.0; step = .25
    while t < 40.0: sfx.add(t, taiko(.8, 110, 50, .9), 1.0); t += step * (1 - .4 * (t - 35) / 5)
    for s in cues['lightning']: sfx.add(s, thunder(), .9)
    for s in cues['storm']: sfx.add(s, whoosh(.25), .4)
    sfx.add(37.5, hit(2.0), 1.0)
    takes = screams()
    for s, k, g, pan in [(36.1, 0, .55, -.6), (36.9, 1, .45, .5), (37.8, 2, .5, -.2), (38.4, 3, .55, .7), (39.0, 5, .5, -.7), (39.4, 4, .6, .1)]:
        cry.add(s, takes[k], g, pan)
    for s, f, pan in [(36.5, 560, .3), (38.0, 480, -.4), (39.2, 620, .6)]: cry.add(s, wail(f), .35, pan)
    # 6b. o mergulho
    d0, d1 = DROWN
    sfx.add(d0, boom(3.0, 40, 20), 1.1)                       # entrada na água
    under.add(d0, np.stack([bubbles(d1 - d0, 34), bubbles(d1 - d0, 34)], 1) * .5, 1.0)
    under.add(d0, gurgle(d1 - d0), .55)
    for s in heartbeat(d0 + .3, d1 - d0 - .6): under.add(s, thump(), .9)
    for s, k, g in [(d0 + .4, 1, .5), (d0 + 1.2, 3, .4), (d0 + 2.0, 0, .3), (d0 + 2.7, 5, .2)]: under.add(s, takes[k], g, rng.uniform(-.6, .6))
    under.add(d0 + 1.6, wail(420, 2.0, .5), .25)
    pres = np.sin(2 * np.pi * 38 * np.arange(int((d1 - d0) * SR)) / SR) * np.linspace(0, 1, int((d1 - d0) * SR)) ** 2
    under.add(d0, pres, .5)
    # 7. outras três, clarões e emblema
    p1 = PAUSE[1]
    sfx.add(p1, hit(3), 1.15); mus.add(p1, braam(2, 26), .9)
    strings_chord(mus, p1, 1.4, CH['Dm'] + ['D5', 'F5'], .5, 4200, .03)
    t = p1
    while t < 47.4: sfx.add(t, taiko(.6, 120, 55, .9), 1.0); t += .17
    cry.add(p1 + .2, takes[2], .4, .6)
    for s in cues['pulses']: sfx.add(s, hit(2.2), 1.1); sfx.add(s, boom(2.4, 45, 22), .8)
    e0 = cues['emblem']
    sfx.add(e0, hit(4.5), 1.0); mus.add(e0, braam(9, 26), .7)
    strings_chord(mus, e0, 15, CH['D'] + ['A5', 'D2'], .55, 3400, .5)
    mus.add(e0, choir_note(nm('A4'), 15), .13); mus.add(e0, choir_note(nm('F#4'), 15), .11)
    for k, n in enumerate(['A4', 'D5', 'F#5', 'E5', 'D5', 'A4', 'D5']): mus.add(e0 + 2.6 + k * .9 * (1.6 if k == 6 else 1), piano(nm(n), 6, .75), .55, .25)
    mus.add(e0 + 7.0, bell(146.8, 9), .3)
    # ambiências
    def ambbus(name, pts): return np.stack([ogg(name) * curve(pts)] * 2, 1)
    amb.x += ambbus('mar', [(0, 0), (1, .45), (6.4, .45), (6.5, .2), (11, .3), (15, .2), (23, .12), (35, .1), (d0, .1), (d0 + .01, 0), (p1, 0), (p1 + .01, .3), (50, .25), (60, .35), (68, 0)])
    amb.x += ambbus('vento', [(0, .1), (6.4, .25), (11, .15), (23, .05), (35, .5), (d0, .55), (d0 + .01, 0), (p1, 0), (p1 + .01, .55), (47.5, .3), (50, .05), (68, 0)])
    amb.x += ambbus('chuva', [(0, 0), (6.5, 0), (7, .25), (10.6, .25), (11, .45), (15, .35), (15.3, 0), (35, 0), (35.2, .7), (d0, .7), (d0 + .01, 0), (p1, 0), (p1 + .01, .7), (47.5, 0), (68, 0)])
    # mixagem
    music = reverb(mus.x, 3.8, 5200, .035, .5)
    effects = reverb(sfx.x, 2.6, 3800, .02, .25)
    cries = reverb(cry.x, 3.4, 4200, .05, .9)                 # distantes
    uw = reverb(under.x, 1.8, 1500, .01, .4)
    dry = music * .85 + effects * .9 + amb.x * .8 + cries * .55
    # debaixo d'água: tudo abafado; depois silêncio absoluto na pausa
    m = np.ones(TA.N); i0, i1 = at(DROWN[0]), at(DROWN[1])
    dry[i0:i1] = lp(dry[i0:i1], 320, 4) * 1.4
    mix = dry + lp(uw, 1400, 2) * 1.1
    mix[at(PAUSE[0]):at(PAUSE[1])] = 0
    mix = mix[:N]
    fade = np.ones(N); fade[at(PAUSE[0]) - 600:at(PAUSE[0])] = np.linspace(1, 0, 600)
    mix *= fade[:, None]
    mix = hp(mix, 22, 2)
    mix = np.tanh(mix / (np.percentile(np.abs(mix), 99.95) + 1e-9) * 1.15)
    mix[at(PAUSE[0]):at(PAUSE[1])] = 0
    tt = np.arange(N) / SR; mix *= np.minimum(1, (DUR - tt) / 2.5)[:, None] * .97
    wavfile.write(path, SR, (mix * 32767).astype(np.int16))
