#!/usr/bin/env python3
"""Trilha e som do trailer oficial (80 s, 48 kHz estéreo). Composição original em ré menor → ré maior.

Ato I   Memória      0–20   água, vento no canal esquerdo, casco de madeira, violoncelo aos 4 s; chuva, sino distante,
                            cordas graves quase imperceptíveis; a música recua em "enterradas".
Ato II  Travessia   20–44   papel, madeira, vento na fresta, primeiras notas de piano; depois violoncelo, cordas médias,
                            piano espaçado e percussão grave discreta; acento grave no corte dos 37,6 s.
Ato III Confronto   44–59   cordas graves, pulsação contida (não um coração literal), sopros marítimos, madeira rangendo;
                            gritos muito distantes sob o mar escuro; ápice e parada seca aos 59 s.
Ato IV  Esperança   59–80   silêncio com uma única onda; piano em primeiro plano com a segunda metade de Amazing Grace,
                            cordas quentes; último acorde, nota suspensa, vento, o mar.
Amazing Grace: melodia "New Britain" (1829, domínio público), arranjo instrumental original, sem letra.
A primeira frase aparece no violoncelo aos 4 s; a segunda metade fecha o trailer no piano.
Versões: sem narração (principal) e com narração (voz neural pm_alex, Kokoro) — `build(path, narrated)`.

Trilha externa (`--trilha arquivo`): substitui a partitura sintetizada por uma gravação, montada em quatro blocos
alinhados à grade de tempos da faixa e mantendo foley, ambiências, gritos distantes, o recuo em "enterradas" e a
parada seca aos 59 s. Os pontos de corte (`TRACK_MAP`) foram medidos em "Amazing Grace (lofi instrumental)",
The Lofi Christian (70 bpm, fá maior; entrada da bateria aos 46,42 s e retorno pleno aos 142,52 s).
"""
import math, sys
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).parent))
import trailer_audio as TA
from trailer_audio import SR, Bus, at, lp, hp, bp, nm, mtof, saw, piano, cello, strings_chord, bell, reverb, ogg, adsr, boom, VOICES
DUR = 80.0; N = int(DUR * SR); T = np.arange(TA.N) / SR
rng = np.random.default_rng(31)
def curve(points): xs, ys = zip(*points); return np.interp(T, xs, ys)

# ── foley ───────────────────────────────────────────────────────────────────
def creak(d=1.4, f0=210):
    """Madeira sob pressão: atrito irregular (stick-slip) filtrado em ressonâncias de casco."""
    n = int(d * SR); x = np.zeros(n); t = 0.0
    while t < d - .01:
        k = t / d; f = f0 * (1 + .35 * math.sin(math.pi * k)) * (1 + .15 * rng.normal())
        i = int(t * SR); x[i] += rng.uniform(.5, 1); t += 1 / max(40, f)
    y = sum(bp(x, fc * .85, fc * 1.15) * g for fc, g in [(420, 1), (760, .7), (1350, .4)])
    return y * adsr(n, .25, .2, .8, .5, .8) * 2.2
def swell(d=3.5, peak=.6):
    """Uma onda que se aproxima e quebra longe."""
    n = int(d * SR); t = np.arange(n) / SR; e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    body = lp(rng.normal(0, 1, n), 500, 2) * e; crest = bp(rng.normal(0, 1, n), 1500, 6000) * np.clip((t / d - peak) * 4, 0, 1) * np.exp(-(t / d - peak).clip(0) * 6)
    return body * 1.2 + crest * .5
def whistle(d=5.0):
    n = int(d * SR); t = np.arange(n) / SR
    return bp(rng.normal(0, 1, n), 1650, 1900, 2) * (.5 + .5 * np.sin(2 * np.pi * .35 * t)) * np.sin(np.pi * t / d) * 1.6
def rustle(d=1.2):
    n = int(d * SR); x = hp(rng.normal(0, 1, n), 2500) * (rng.random(n) > .985) * 4 + hp(rng.normal(0, 1, n), 3500) * .15
    return lp(x, 9000) * np.sin(np.pi * np.arange(n) / n) ** .5 * .5
def gust(d=4.0):
    n = int(d * SR); t = np.arange(n) / SR; cut = 400 + 900 * np.sin(np.pi * t / d)
    y = np.zeros(n); seg = SR // 20; noise = rng.normal(0, 1, n)
    for s in range(0, n, seg): y[s:s + seg] = bp(noise[max(0, s - 2000):s + seg], float(cut[s]) * .6, float(cut[s]) * 1.4)[-len(y[s:s + seg]):]
    return y * np.sin(np.pi * t / d) ** 2 * 1.4
def timp(f=73.4, d=2.5, g=1.0):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2) + .4 * np.sin(2 * np.pi * f * 1.5 * t) * np.exp(-t * 3) + lp(rng.normal(0, 1, len(t)), 400) * np.exp(-t * 30) * .3) * g
def pad_note(m, d, gain, bright=1800, att=2.0):
    """Cordas em pianíssimo: ataque lento, quase sem vibrato."""
    return TA.strings_note(m, d, bright, att) * gain

def grace_note(bus, t, m, gain, pan=.2):
    """Apojatura curta (nota vizinha superior) antes da nota principal."""
    bus.add(t - .07, piano(m + 2, 1.2, .4), gain * .5, pan)
def rolled(bus, t, notes, gain, spread=.045, pan=0.0, vel=.7, dur=6):
    for k, m in enumerate(notes): bus.add(t + k * spread, piano(m, dur, vel), gain, pan + (k / max(1, len(notes) - 1) - .5) * .4)
def alberti(bus, t0, beat, beats, chord, gain, pan=-.25):
    """Mão esquerda em colcheias quebradas: fundamental, quinta, terça (décima), quinta…"""
    r, third, fifth = chord
    pat = [r, fifth, third + 12, fifth, third + 12, fifth]
    for k in range(int(beats * 2)): bus.add(t0 + k * beat / 2, piano(pat[k % 6], 1.6, .5 if k % 6 else .62), gain, pan)

def screams_far():
    try:
        import trailer_sound_v3 as S3
        return S3.screams()
    except Exception:
        return []

# ── narração (versão alternativa) ───────────────────────────────────────────
VO = [(8.7, 'Toda costa guarda histórias que o mar não conseguiu levar.', .84), (12.5, 'Algumas foram enterradas.', .8),
      (21.0, 'Outras permaneceram esperando…', .82), (24.6, '…que alguém tivesse coragem de voltar.', .84),
      (32.2, 'Mas há viagens que não começam quando partimos.', .86), (38.6, 'Começam quando já não podemos continuar fugindo.', .86),
      (44.6, 'Entre a culpa e a verdade…', .82), (48.2, '…entre aquilo que perdemos…', .82), (54.9, '…e aquilo que ainda podemos escolher.', .82),
      (61.6, 'Porque nem toda história marcada pela perda…', .78), (66.6, '…precisa terminar nela.', .76)]
def narration():
    from kokoro_onnx import Kokoro
    k = Kokoro(str(VOICES / 'kokoro-v1.0.onnx'), str(VOICES / 'voices-v1.0.bin')); bus = np.zeros(TA.N)
    for s, text, sp in VO:
        a, sr = k.create(text.replace('…', ','), voice='pm_alex', speed=sp, lang='pt-br')
        a = signal.resample_poly(a.astype(np.float64), SR, sr); nz = np.where(np.abs(a) > .01)[0]; a = a[max(0, nz[0] - 500):nz[-1] + 2400]
        a = TA.treat_voice(a); i = at(s); bus[i:i + len(a)] += a[:TA.N - i]
    return bus

# ── composição ──────────────────────────────────────────────────────────────
# Hino: frase 1 (pickup + 4 compassos) e segunda metade (8 compassos), em ré maior, 3/4. (nota, tempos)
PHRASE1 = [('A3', 1), ('D4', 2), ('F#4', .5), ('D4', .5), ('F#4', 2), ('E4', 1), ('D4', 2), ('B3', 1), ('A3', 3)]
PHRASE2 = [('A4', 2), ('F#4', 1), ('A4', 2), ('F#4', .5), ('D4', .5), ('F#4', 2), ('E4', 1), ('D4', 2), ('B3', 1),
           ('A3', 2), ('A3', 1), ('D4', 2), ('F#4', .5), ('D4', .5), ('F#4', 2), ('E4', 1), ('D4', 3)]
PHRASE1_MINOR = [('A3', 1), ('D4', 2), ('F4', .5), ('D4', .5), ('F4', 2), ('E4', 1), ('D4', 2), ('Bb3', 1), ('A3', 3)]
BEAT1 = .75; BEAT2 = (74.8 - 60.6) / 24          # a última nota ("see") cai no acorde final, com o emblema
HARM2 = ['D', 'D', 'G', 'D', 'D', 'Bm', 'A', 'D']
CHORDS2 = {'D': ['D3', 'A3', 'D4', 'F#4'], 'G': ['G2', 'B3', 'D4', 'G4'], 'Bm': ['B2', 'B3', 'D4', 'F#4'], 'A': ['A2', 'A3', 'C#4', 'E4']}

# (início no trailer, fim no trailer, início na faixa): a bateria entra quando a Constância surge (30,9 s); o retorno
# pleno da faixa cai na revelação do emblema (70 s); a ponte mais leve da faixa acompanha a primeira luz.
TRACK_MAP = [(0.0, 59.0, 46.424 - 30.9), (60.6, 80.0, 142.52 - 9.4)]

def external_score(track):
    """Monta a gravação sobre a linha do tempo do trailer (mesmas curvas de recuo e silêncio da partitura original)."""
    import subprocess
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(track), '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    src = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)
    out = np.zeros((TA.N, 2))
    for t0, t1, s0 in TRACK_MAP:
        i0, i1, j0 = int(t0 * SR), int(t1 * SR), int(s0 * SR)
        seg = src[j0:j0 + i1 - i0]; out[i0:i0 + len(seg)] += seg
    # Ato III: a faixa fica abafada, como ouvida debaixo d'água, e se abre aos poucos até a parada seca
    muffled = lp(lp(out, 650, 2), 900, 2)
    open_ = curve([(0, 1), (43.9, 1), (44.15, .0), (50.0, .05), (56.0, .35), (58.9, 1), (80, 1)])[:, None]
    out = out * open_ + muffled * (1 - open_) * 1.6
    out *= curve([(0, 0), (1.0, 0), (4.0, 1), (80, 1)])[:, None]                               # entra sob a água
    out *= curve([(0, 1), (60.59, 1), (60.6, 0), (61.4, 1), (80, 1)])[:, None]                 # volta depois do silêncio
    return out

def build(path, narrated=False, track=None):
    mus, fx, amb = Bus(), Bus(), Bus()
    # Ato I
    fx.add(.4, swell(3.6, .7), .55, .1)
    fx.add(1.0, gust(3.0), .5, -.9)                      # respiração de vento no canal esquerdo
    fx.add(2.6, creak(1.6, 190), .35, .3)
    # "Amazing Grace" (melodia New Britain, 1829, domínio público): primeira frase no violoncelo, sem harmonia, sobre o pedal grave
    t = 4.0
    for n, b in PHRASE1:
        mus.add(t, cello(nm(n) + 12, b * BEAT1 + .15), .7, -.15)
        mus.add(t, piano(nm(n) + 24, max(2.0, b * BEAT1 + 1.2), .42), .32, .25); t += b * BEAT1
    mus.add(4.0, np.stack([TA.lp(saw(mtof(nm('D2')), int(10.5 * SR)), 160)] * 2, 1) * adsr(int(10.5 * SR), 2.5, .1, 1, 2, 1)[:, None], .12)
    for m in ('D3', 'A3', 'F4'): mus.add(8.2, pad_note(nm(m), 12.0, .16, 1500, 3.0))
    fx.add(10.0, bell(220, 7), .14, .5)
    fx.add(6.2, creak(1.2, 230), .25, -.4)
    mus.add(15.4, cello(nm('D2'), 4.6), .45)
    # Ato II — o que ficou para trás
    fx.add(20.8, creak(1.4, 260), .22, .4); fx.add(21.5, whistle(5.5), .22, .7); fx.add(24.2, rustle(1.4), .55, .5); fx.add(26.0, rustle(.9), .3, .55)
    t = 21.4
    for n, b in PHRASE1_MINOR:
        mus.add(t, piano(nm(n) + 12, 4.5, .62), .62, .2); t += b * .62
    mus.add(27.6, piano(nm('A5'), 3, .35), .3, .4)        # o brilho na bússola
    fx.add(29.4, swell(2.4, .5), .55)                     # o pigmento vira água
    # Ato II — a travessia
    prog = [('Dm', 31.0), ('Bb', 34.3), ('F', 37.6), ('C', 39.8), ('Gm', 41.9)]
    for i, (c, s0) in enumerate(prog):
        dur = (prog[i + 1][1] if i + 1 < len(prog) else 44.0) - s0
        strings_chord(mus, s0, dur + .4, TA.CH[c], .2 + .04 * i, 2000 + 250 * i, 1.0 if i == 0 else .5)
        mus.add(s0, cello(nm(TA.CH[c][0]) - (12 if nm(TA.CH[c][0]) > 45 else 0), dur + .3), .5, -.2)
        mus.add(s0, timp(mtof(nm(TA.CH[c][0]) - 12) if nm(TA.CH[c][0]) > 45 else mtof(nm(TA.CH[c][0])), 2.4, .5), .5)
    for k, n in enumerate(['D5', 'C5', 'A4', 'F4', 'G4', 'A4', 'Bb4', 'A4', 'G4', 'E4']):
        mus.add(31.8 + k * 1.15, piano(nm(n), 4, .55), .45, .25)
    for k, n in enumerate(['A3', 'Bb3', 'C4', 'D4', 'F4', 'E4']):  # linha de violoncelo
        mus.add(37.6 + k * 1.05, cello(nm(n), 1.2), .38, -.3)
    fx.add(37.6, boom(2.6, 44, 26), .55)                  # acento grave no corte
    amb_sea = [(0, 0), (.3, .35), (8, .3), (20, .2), (31, .4), (44, .3), (50, .45), (52.4, .3), (59.0, .25), (59.05, 0), (60.2, 0), (61, .25), (70, .3), (76, .35), (79.2, .4), (80, 0)]
    # Ato III — confronto
    for i, (c, s0) in enumerate([('Dm', 44.0), ('Bb', 47.0), ('Gm', 50.0), ('A', 52.4), ('Dm', 54.4), ('A', 56.6)]):
        dur = [3.0, 3.0, 2.4, 2.0, 2.2, 2.4][i]
        strings_chord(mus, s0, dur + .2, TA.CH[c] + ['D2'] if c == 'Dm' else TA.CH[c], .38 + .08 * i, 2400 + 450 * i, .3)
    t, step = 44.0, .75
    while t < 59.0:                                       # pulsação contida em contrabaixos
        mus.add(t, TA.ostinato(nm('D2'), .32, .5), .85 + .45 * (t - 44) / 15, -.2); t += step * (1 - .3 * (t - 44) / 15)
    for s in (45.0, 49.2, 53.0, 56.0): fx.add(s, creak(1.3, rng.uniform(180, 260)), .3, rng.uniform(-.6, .6))
    for s in (46.0, 51.0, 55.5): fx.add(s, gust(3.5), .45, rng.uniform(-.5, .5))
    cries = screams_far()
    cry = Bus()
    for s, k_, g, pan in [(50.3, 0, .25, -.5), (50.9, 1, .2, .45), (51.6, 3, .18, -.1)]:
        if cries: cry.add(s, cries[k_], g, pan)
    fx.add(58.0, TA.riser(1.0), .35)
    # Ato IV — esperança
    fx.add(59.25, swell(3.0, .55), .7)                    # uma única onda no silêncio
    t = 60.6; THIRD = {'A': -3, 'F#': -4, 'E': -3, 'D': -3, 'B': -4}
    for k, (n, b) in enumerate(PHRASE2):
        m = nm(n) + 12
        if b >= 2 and k not in (0,): grace_note(mus, t, m, .5)
        mus.add(t, piano(m, max(2.5, b * BEAT2 + 1.6), .82), .78, .15)
        if b >= 2: mus.add(t, piano(m + THIRD.get(n[:-1], -3) - 12 + 12, 2.6, .45), .32, .25)   # terça/sexta por baixo
        t += b * BEAT2
    for i, c in enumerate(HARM2):
        t0 = 60.6 + i * 3 * BEAT2; notes = CHORDS2[c]
        mus.add(t0, piano(nm(notes[0]) - 12, 4, .55), .42, -.2)
        r = nm(notes[0]); third = nm(notes[3]) - 12 if c != 'G' else nm('B2'); fifth = r + 7
        alberti(mus, t0, BEAT2, 3, (r, third, fifth), .28)
        for m in notes[1:]: mus.add(t0, pad_note(nm(m), 3 * BEAT2 + .6, .12 + .012 * i, 2400 + 80 * i, .9))
    rolled(mus, 74.8, [nm(x) for x in ('D2', 'A2', 'D3', 'F#3', 'A3', 'D4', 'F#4', 'A4', 'D5')], .4, .05)
    mus.add(75.5, piano(nm('D6'), 5, .4), .25, .4)
    mus.add(74.8, pad_note(nm('A4'), 4.6, .22, 3000, .6), 1.0)                                    # nota suspensa
    fx.add(75.6, gust(4.0), .3, -.6)
    # ambiências
    amb.x += np.stack([ogg('mar') * curve(amb_sea)] * 2, 1)
    amb.x += np.stack([ogg('vento') * curve([(0, 0), (1, .12), (8, .2), (15.4, .3), (20, .15), (31, .1), (44, .25), (58.9, .35), (59.0, 0), (75, 0), (77, .15), (80, 0)])] * 2, 1)
    amb.x += np.stack([ogg('chuva') * curve([(0, 0), (7.9, 0), (8.0, .45), (12.4, .5), (15.3, .5), (15.4, .2), (20, .1), (21, 0), (80, 0)])] * 2, 1)
    # mixagem
    music = external_score(track) if track else reverb(mus.x, 3.6, 5200, .035, .45)
    # "enterradas": a música recua e a chuva ocupa o espaço
    music *= curve([(0, 1), (13.2, 1), (13.6, .35), (15.2, .35), (15.4, 1), (80, 1)])[:, None]
    music *= curve([(0, 1), (58.95, 1), (59.0, 0), (60.4, 0), (60.6, 1), (80, 1)])[:, None]   # parada seca
    music *= curve([(0, 1), (77.0, 1), (79.5, 0), (80, 0)])[:, None]                             # a música desaparece
    effects = reverb(fx.x, 2.4, 4200, .02, .3)
    cry_mix = lp(reverb(cry.x, 3.6, 3000, .06, 1.2), 1600, 2)
    mix = music * .8 + effects * .8 + amb.x * (.5 if track else .75) + cry_mix * .5   # com a gravação, a música vem à frente
    if narrated:
        vo = narration(); env = signal.lfilter([.0015], [1, -.9985], np.abs(vo))
        duck = 1 - .45 * np.clip(env / .05, 0, 1)
        mix = mix * duck[:, None] + reverb(np.stack([vo] * 2, 1), 1.0, 6000, .012, .1) * 1.0
    mix = mix[:N]; mix = hp(mix, 25, 2)
    peak = np.max(np.abs(mix)); mix = mix / peak * .89
    mix *= np.minimum(1, (DUR - np.arange(N) / SR) / 1.0)[:, None]
    wavfile.write(path, SR, (mix * 32767).astype(np.int16))

if __name__ == '__main__':
    a = sys.argv[1:]
    build(a[0], '--narrado' in a, a[a.index('--trilha') + 1] if '--trilha' in a else None)
