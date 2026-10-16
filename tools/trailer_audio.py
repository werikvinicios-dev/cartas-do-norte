#!/usr/bin/env python3
"""Trilha, narração e efeitos do trailer de Cartas do Norte (90 s, 48 kHz, estéreo).

Composição original em ré menor, quatro movimentos sincronizados com a montagem:
  I    0–15 s   A primeira luz  — pedal grave, harmônicos de cordas, três pulsos; crescendo até o impacto.
  II  16–37 s   O arquivo       — tema de piano sobre cordas (Dm–B♭–F–C–Dm–Gm–B♭–A), violoncelo.
  III 37–52 s   A travessia     — 100 bpm: ostinato de cordas, coro, tambores, metais graves nos títulos.
  IV  52–67 s   A tempestade    — 120 bpm: tutti, braams, taiko; silêncio absoluto na "pausa"; retorno em fortíssimo.
  V   68–90 s   O emblema       — três pulsos, acorde de ré maior (terça de picardia), tema do piano, decaimento.
Narração: voz neural pm_alex (Kokoro, Apache 2.0), tratada como locução de estúdio
(sem alteração de altura). A música é rebaixada automaticamente sob a voz.
Instrumentos sintetizados aqui; ambiências mar/vento/chuva são as originais da edição.
"""
import math, subprocess, functools
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
SR, DUR = 48000, 90.0
N = int(SR * DUR); T = np.arange(N) / SR
rng = np.random.default_rng(11)
VOICES = Path('/tmp/claude-0/-home-user-cartas-do-norte/59f9707a-cf0c-5433-8561-595c954c62d8/scratchpad/voices')

def at(s): return int(round(s * SR))
def sos(kind, f, o=4): return signal.butter(o, f, kind, fs=SR, output='sos')
def lp(x, f, o=4): return signal.sosfilt(sos('low', f, o), x, axis=0)
def hp(x, f, o=4): return signal.sosfilt(sos('high', f, o), x, axis=0)
def bp(x, a, b, o=2): return signal.sosfilt(sos('band', [a, b], o), x, axis=0)
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
NOTE = {n: i for i, n in enumerate(['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'])}
def nm(s):  # 'D3' → midi
    return 12 * (int(s[-1]) + 1) + NOTE[s[:-1]]

class Bus:
    def __init__(self): self.x = np.zeros((N, 2))
    def add(self, start, y, gain=1.0, pan=0.0):
        if y.ndim == 1:
            l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
            y = np.stack([y * l * 1.414, y * r * 1.414], 1)
        i = at(start); j = min(N, i + len(y))
        if i < N and j > i: self.x[i:j] += y[:j - i] * gain

def adsr(n, a, d, s, r, sus_level=.8):
    a, d, r = int(a * SR), int(d * SR), int(r * SR); e = np.full(n, float(sus_level))
    e[:a] = np.linspace(0, 1, a, endpoint=False) if a else e[:a]
    e[a:a + d] = np.linspace(1, sus_level, len(e[a:a + d]))
    if r: e[-r:] *= np.linspace(1, 0, min(r, n))[-len(e[-r:]):]
    return e

def saw(f, n, phase=0.0, vib=0.0, vib_rate=5.2):
    t = np.arange(n) / SR
    inst = f * (1 + vib * np.sin(2 * np.pi * vib_rate * t + phase * 7))
    ph = (np.cumsum(inst) / SR + phase) % 1
    return 2 * ph - 1

# ── instrumentos ────────────────────────────────────────────────────────────
@functools.lru_cache(None)
def strings_note(m, dur, bright=2600, att=.9):
    n = int((dur + 1.6) * SR); f = mtof(m); out = np.zeros((n, 2))
    for k in range(6):
        det = 1 + (k - 2.5) * .0016
        v = saw(f * det, n, phase=rng.random(), vib=.0028, vib_rate=4.6 + .3 * k)
        pan = -.8 + 1.6 * k / 5
        out[:, 0] += v * math.cos((pan + 1) * math.pi / 4); out[:, 1] += v * math.sin((pan + 1) * math.pi / 4)
    out = lp(out, bright, 2); out = hp(out, 70, 2)
    return out * adsr(n, att, .4, 1, 1.6, 1)[:, None] / 6

def strings_chord(bus, start, dur, notes, gain=.5, bright=2600, att=.9):
    for s in notes: bus.add(start, strings_note(nm(s), dur, bright, att), gain)

@functools.lru_cache(None)
def choir_note(m, dur):
    n = int((dur + 2) * SR); f = mtof(m); x = np.zeros(n)
    for k in range(5): x += saw(f * (1 + (k - 2) * .002), n, rng.random(), .004, 5.5)
    v = sum(bp(x, fc * .9, fc * 1.1) * g for fc, g in [(800, 1), (1150, .6), (2900, .18)])
    v = v * adsr(n, 1.4, .5, 1, 2, 1) / 5
    return np.stack([v, np.roll(v, 480)], 1)

def piano(m, dur=4.0, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m); B = .00035; x = np.zeros(n)
    for h in range(1, 10):
        fh = f * h * math.sqrt(1 + B * h * h)
        if fh > 9000: break
        decay = 1.1 + .55 * h; amp = vel / h ** 1.15
        x += amp * (.75 * np.exp(-t * decay) + .25 * np.exp(-t * decay * .22)) * np.sin(2 * np.pi * fh * t + rng.random())
    x += lp(rng.normal(0, 1, n), 2500) * np.exp(-t * 60) * .08 * vel
    x *= np.minimum(1, t * 400)
    return x * .3

@functools.lru_cache(None)
def cello(m, dur):
    n = int((dur + .8) * SR); f = mtof(m)
    x = saw(f, n, rng.random(), .005, 5.0) + .5 * saw(f * 1.003, n, rng.random(), .004, 4.7)
    x = lp(x, 1400, 2) * adsr(n, .25, .3, .85, .8, .85)
    x += bp(rng.normal(0, 1, n), 1500, 5000) * adsr(n, .02, .2, 0, .1, 0) * .05
    return x * .35

def ostinato(m, dur, gain=.4):
    n = int(dur * SR); f = mtof(m); x = saw(f, n, rng.random()) + saw(f * 2.001, n, rng.random()) * .4
    return lp(x, 1800, 2) * adsr(n, .006, .08, .35, .05, .35) * gain

def boom(d=2.2, f0=58, f1=28):
    t = np.arange(int(d * SR)) / SR; f = f1 + (f0 - f1) * np.exp(-t * 6)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.0)
    x += lp(rng.normal(0, 1, len(t)), 180) * np.exp(-t * 18) * .8
    return np.tanh(x * 1.6)
def taiko(d=1.2, f0=110, f1=55, g=1.0):
    t = np.arange(int(d * SR)) / SR; f = f1 + (f0 - f1) * np.exp(-t * 25)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)
    skin = lp(rng.normal(0, 1, len(t)), 1500) * np.exp(-t * 35) * .5
    return np.tanh((body + skin) * 1.4) * g
def braam(d=6.0, root=38):
    t = np.arange(int(d * SR)) / SR; x = np.zeros(len(t))
    for m, g in [(root, 1), (root + 7, .6), (root + 12, .7), (root - 12, .8)]:
        for dt in (-.003, 0, .003): x += saw(mtof(m) * (1 + dt), len(t), rng.random()) * g
    env = np.minimum(1, t / .05) * np.exp(-t * .45)
    cut = 400 + 1400 * np.exp(-t * 1.2)
    out = np.zeros_like(x); seg = SR // 20
    for s in range(0, len(x), seg):  # filtro que fecha ao longo da nota
        out[s:s + seg] = lp(x[max(0, s - 2000):s + seg], float(cut[s]), 2)[-len(x[s:s + seg]):]
    return np.tanh(out * env * .5) * .9
def riser(d):
    t = np.arange(int(d * SR)) / SR; n = rng.normal(0, 1, len(t)); out = np.zeros_like(n); seg = int(.05 * SR)
    for s in range(0, len(t), seg):
        k = s / len(t); out[s:s + seg] = bp(n[s:s + seg + 600], 300 + 3500 * k ** 2, 700 + 7000 * k ** 2)[:len(n[s:s + seg])]
    tone = sum(np.sin(2 * np.pi * np.cumsum(mtof(m) * (1 + .5 * (t / d) ** 2)) / SR) for m in (50, 57, 62)) * .12
    return (out * .5 + tone) * (t / d) ** 2.4
def whoosh(d=.5):
    t = np.arange(int(d * SR)) / SR; return bp(rng.normal(0, 1, len(t)), 400, 5000) * np.sin(np.pi * t / d) ** 2 * .55
def hit(d=3.0): t = np.arange(int(d * SR)) / SR; return boom(d, 70, 30) + bp(rng.normal(0, 1, len(t)), 200, 4000) * np.exp(-t * 7) * .35
def thunder(d=3.5):
    t = np.arange(int(d * SR)) / SR; x = lp(rng.normal(0, 1, len(t)), 220) * (np.exp(-t * 1.3) * (1 + .6 * np.sin(t * 9)))
    return x * 1.6
def bell(f=196, d=6.0):
    t = np.arange(int(d * SR)) / SR
    return sum(np.sin(2 * np.pi * f * r * t) * np.exp(-t * dd) * g for r, dd, g in [(1, .6, 1), (2.01, 1.0, .5), (2.76, 1.5, .35), (3.9, 2.2, .2), (5.4, 3, .12)]) * .35

def reverb(x, seconds=3.6, bright=5000, predelay=.03, wet=.3):
    n = int(seconds * SR); t = np.arange(n) / SR
    irs = []
    for s in (1, 2):
        ir = np.random.default_rng(s).normal(0, 1, n) * np.exp(-t * 6.9 / seconds)
        ir = lp(ir, bright, 2); ir[:int(predelay * SR)] = 0; irs.append(ir / np.sqrt((ir ** 2).sum()))
    mono = x.mean(1)
    w = np.stack([signal.fftconvolve(mono, irs[0])[:N], signal.fftconvolve(mono, irs[1])[:N]], 1)
    return x + w * wet

def ogg(name):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', str(ROOT / f'assets/audio/{name}.ogg'), '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).astype(np.float64); return np.tile(x, N // len(x) + 1)[:N]
def curve(points): xs, ys = zip(*points); return np.interp(T, xs, ys)

# ── narração ────────────────────────────────────────────────────────────────
VO = [  # (início, texto, velocidade)
    (4.7, 'A primeira luz era a que todos esperavam.', .86),
    (10.4, 'Mas a segunda luz… não deveria existir.', .84),
    (17.5, 'Choveu no funeral de Jonas Vale.', .88),
    (23.5, 'Não lhe escrevo para pedir que me perdoe.', .84),
    (28.9, 'A casa do farol tinha aprendido a envelhecer sem testemunhas.', .9),
    (33.6, 'Uma rota não é segura porque alguém a desenhou com régua.', .92),
    (54.6, 'Três pulsações sobre o mar.', .86),
    (58.75, 'Uma pausa.', .8),
    (61.05, 'Outras três.', .82),
    (72.2, 'Cartas do Norte.', .78),
    (76.0, 'Há histórias que não terminam na última página.', .84),
]
def synth_vo():
    from kokoro_onnx import Kokoro
    k = Kokoro(str(VOICES / 'kokoro-v1.0.onnx'), str(VOICES / 'voices-v1.0.bin'))
    out = []
    for start, text, speed in VO:
        a, sr = k.create(text, voice='pm_alex', speed=speed, lang='pt-br')
        a = signal.resample_poly(a.astype(np.float64), SR, sr)
        nz = np.where(np.abs(a) > .01)[0]; a = a[max(0, nz[0] - 600): nz[-1] + 2400]
        out.append((start, a))
    return out
def treat_voice(a):
    a = hp(a, 75, 2)
    lo = lp(a, 180, 2); a = a + lo * .35                       # corpo
    pres = bp(a, 2800, 5000); a = a + pres * .35               # presença
    env = np.sqrt(signal.lfilter([.002], [1, -.998], a ** 2) + 1e-9)   # compressão RMS suave
    g = np.minimum(1, (.08 / env) ** .45); a = a * g
    ess = bp(a, 6000, 9500); a = a - ess * .4                  # de-esser simples
    return a / (np.max(np.abs(a)) + 1e-9) * .9

# ── composição ──────────────────────────────────────────────────────────────
CH = {'Dm': ['D3', 'A3', 'D4', 'F4'], 'Bb': ['Bb2', 'F3', 'D4', 'F4'], 'F': ['F2', 'C4', 'F4', 'A4'], 'C': ['C3', 'G3', 'E4', 'G4'],
      'Gm': ['G2', 'D4', 'G4', 'Bb4'], 'A': ['A2', 'E4', 'A4', 'C#5'], 'D': ['D3', 'A3', 'F#4', 'D5'], 'Dsus': ['D3', 'A3', 'G4', 'D5']}
MOTIF = ['A4', 'D5', 'F5', 'E5', 'D5', 'C5', 'A4', 'Bb4', 'A4', 'G4', 'F4', 'E4', 'D4']

def compose(cues):
    mus, sfx, amb = Bus(), Bus(), Bus()
    L = cues
    # I — a primeira luz
    mus.add(0, np.stack([lp(saw(mtof(26), N, .1), 120)] * 2, 1)[:at(15.4)] * adsr(at(15.4), 3, .1, 1, 1.5, 1)[:, None], .22)
    for s in L['pulses1']: sfx.add(s, boom(), .8); mus.add(s, piano(nm('D2'), 5, .9), .5)
    strings_chord(mus, 5.2, 10.2, ['D5', 'A5'], .16, 6000, 3.5)
    sfx.add(10.0, riser(5.45), .55)
    sfx.add(15.45, hit(), 1.0)
    # II — o arquivo (72 bpm, compasso 4/4 ≈ 3,33 s)
    bar = 60 / 72 * 4; t0 = 16.2
    for i, c in enumerate(['Dm', 'Bb', 'F', 'C', 'Dm', 'Gm']):
        strings_chord(mus, t0 + i * bar, bar + .2, CH[c], .38, 2200 + 200 * i, 1.0)
        mus.add(t0 + i * bar, cello(nm(CH[c][0]) - 12 if nm(CH[c][0]) > 45 else nm(CH[c][0]), bar), .55, -.2)
    beat = bar / 4
    for k, n in enumerate(MOTIF):
        tt = t0 + bar * .5 + k * beat * (1.5 if k in (2, 6, 12) else 1.0) + (beat * .5 * sum(1 for j in (2, 6) if k > j))
        mus.add(tt, piano(nm(n), 4.5, .8), .6, .25)
    for k, n in enumerate(['D5', 'F5', 'A5', 'G5', 'F5', 'E5']):
        mus.add(t0 + 4 * bar + k * beat, piano(nm(n), 4, .65), .45, .3)
    sfx.add(34.6, riser(2.4), .38); sfx.add(36.75, whoosh(), .7)
    # III — a travessia (100 bpm)
    b3 = 60 / 100; prog = ['Dm', 'Bb', 'F', 'C'] * 2
    t = 37.0
    for i, c in enumerate(prog):
        dur = b3 * 4 * (15.6 / (b3 * 4 * len(prog)))
        strings_chord(mus, t, dur + .1, CH[c], .3 + .03 * i, 2600 + 250 * i, .3)
        mus.add(t, choir_note(nm(CH[c][2]), dur), .05 + .02 * i)
        root = nm(CH[c][0]) - (12 if nm(CH[c][0]) > 45 else 0)
        sub = dur / 8
        for k in range(8): mus.add(t + k * sub, ostinato(root + (12 if k % 2 else 0), sub * .9), .5, -.4 + .8 * (k % 2))
        t += dur
    for bt in np.arange(37.0, 52.6, b3):
        sfx.add(bt, taiko(.9, 95, 52, .55), .9, -.15)
        if (bt - 37.0) / b3 % 4 in (2.0,): sfx.add(bt + b3 / 2, taiko(.5, 160, 90, .3), .8, .3)
    for s in L['montage']: sfx.add(s, whoosh(.4), .45)
    for s in L['titles']: sfx.add(s, boom(1.8, 62, 32), .75); mus.add(s, braam(3.0, 38), .35)
    # IV — a tempestade (120 bpm), silêncio na pausa
    b4 = .5; pause0, pause1 = L['pause']
    for sec, chords in [((52.6, pause0), ['Dm', 'Bb', 'Gm', 'A']), ((pause1, 66.6), ['Dm', 'Bb', 'Gm', 'A'])]:
        a, b = sec; dur = (b - a) / len(chords)
        for i, c in enumerate(chords):
            strings_chord(mus, a + i * dur, dur, CH[c] + [CH[c][2][:-1] + str(int(CH[c][2][-1]) + 1)], .42, 3600, .15)
            mus.add(a + i * dur, choir_note(nm(CH[c][1]) + 12, dur), .09)
            mus.add(a + i * dur, braam(min(4, dur + 1), nm(CH[c][0]) - 12 if nm(CH[c][0]) > 40 else nm(CH[c][0])), .55)
            root = nm(CH[c][0]) - (12 if nm(CH[c][0]) > 45 else 0)
            for k in range(int(dur / (b4 / 2))): mus.add(a + i * dur + k * b4 / 2, ostinato(root + 12 * (k % 2), b4 / 2 * .9, .5), .55, -.5 + (k % 2))
        bt = a
        while bt < b - .05:
            sfx.add(bt, taiko(1.0, 105, 50, .9), 1.0)
            sfx.add(bt + b4 / 2, taiko(.4, 170, 95, .35), .8, .4)
            bt += b4 * (1 - .3 * min(1, (bt - 52.6) / 14))
    sfx.add(52.6, hit(), 1.0); sfx.add(pause1, hit(), 1.0); sfx.add(pause1, braam(4, 26), .9)
    for s in L['lightning']: sfx.add(s, thunder(), .8)
    for s in L['storm']: sfx.add(s, whoosh(.3), .5)
    sfx.add(pause0 + .1, bell(196, 5), .5)
    for s in L['pulses2']: sfx.add(s, hit(2.0), .9)
    # V — o emblema: ré maior
    for s in L['pulses3']: sfx.add(s, boom(2.2, 50, 26), .7); mus.add(s, piano(nm('D2'), 4, .9), .45)
    e0 = L['emblem']
    sfx.add(e0, hit(4), .9); mus.add(e0, braam(8, 26), .55)
    strings_chord(mus, e0, 14, CH['D'] + ['A5', 'D2'], .5, 3200, .4)
    mus.add(e0, choir_note(nm('A4'), 14), .12); mus.add(e0, choir_note(nm('F#4'), 14), .1)
    for k, n in enumerate(['A4', 'D5', 'F#5', 'E5', 'D5', 'A4', 'D5']):
        mus.add(e0 + 2.4 + k * .83 * (1.6 if k == 6 else 1), piano(nm(n), 6, .75), .55, .25)
    mus.add(e0 + 9.5, bell(146.8, 8), .25)
    # ambiências da edição
    amb.x += np.stack([ogg('mar') * curve([(0, 0), (1.5, .5), (15.3, .45), (15.5, .1), (16.6, .3), (37, .18), (52, .12), (pause0, .1), (pause0 + .2, .35), (pause1, .3), (66.6, .1), (68, .25), (80, .3), (90, 0)])] * 2, 1)
    amb.x += np.stack([ogg('vento') * curve([(0, 0), (8, .12), (15, .2), (37, .06), (52.6, .45), (pause0, .5), (pause0 + .1, .7), (pause1, .5), (66.6, .5), (68, .1), (90, 0)])] * 2, 1)
    amb.x += np.stack([ogg('chuva') * curve([(0, 0), (8.4, 0), (9.5, .18), (15.4, .22), (15.5, 0), (16.6, .38), (22.3, .3), (23, 0), (52.6, 0), (53, .6), (66.6, .6), (67, 0), (90, 0)])] * 2, 1)
    return mus, sfx, amb

def build_audio(path, cues):
    mus, sfx, amb = compose(cues)
    music = reverb(mus.x, 3.8, 5200, .035, .55)
    effects = reverb(sfx.x, 2.4, 3500, .02, .22)
    vo_bus = np.zeros(N)
    for start, a in synth_vo():
        a = treat_voice(a); i = at(start); vo_bus[i:i + len(a)] += a[:N - i]
    vo = reverb(np.stack([vo_bus] * 2, 1), 1.1, 6000, .015, .12)
    # rebaixa a música sob a voz (sidechain suave)
    env = signal.lfilter([.0015], [1, -.9985], np.abs(vo_bus))
    duck = 1 - .5 * np.clip(env / .05, 0, 1)
    mix = music * duck[:, None] * .9 + effects * (1 - .25 * np.clip(env / .05, 0, 1))[:, None] * .85 + amb.x * .8 + vo * 1.05
    mix = hp(mix, 25, 2)
    mix = np.tanh(mix / (np.percentile(np.abs(mix), 99.9) + 1e-9) * 1.1)
    mix *= np.minimum(1, (DUR - T) / 2.5)[:, None] * .97
    wavfile.write(path, SR, (mix * 32767).astype(np.int16))
    return [(s, t) for s, t, _ in VO]
