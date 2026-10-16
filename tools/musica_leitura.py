#!/usr/bin/env python3
"""Música contínua para fundo de leitura: "Graça" — variações de Amazing Grace ao piano.

Melodia "New Britain" (1829, domínio público); arranjo instrumental original, sem letra.
Ré maior, 3/4, ♩ = 66. Estrutura (≈ 3 min), pensada para tocar em repetição sem emenda:
  introdução (arpejos) · variação I (melodia simples) · interlúdio · variação II (uma oitava acima, mão esquerda
  em arpejos, violoncelo em contracanto) · interlúdio · variação III (melodia no grave, arpejos no agudo) · coda
  que volta ao acorde inicial. A cauda de reverberação do fim é somada ao início, então o loop não tem corte.
Dinâmica baixa e sem percussão: feita para não competir com a leitura.
Uso: python3 tools/musica_leitura.py assets/audio/graca.ogg
"""
import sys, subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).parent))
import trailer_audio as TA
from trailer_audio import SR, nm, piano, cello, reverb, lp, hp

BEAT = 60 / 66
MEL = [('A3', 1), ('D4', 2), ('F#4', .5), ('D4', .5), ('F#4', 2), ('E4', 1), ('D4', 2), ('B3', 1), ('A3', 2), ('A3', 1),
       ('D4', 2), ('F#4', .5), ('D4', .5), ('F#4', 2), ('E4', 1), ('A4', 3),
       ('A4', 2), ('F#4', 1), ('A4', 2), ('F#4', .5), ('D4', .5), ('F#4', 2), ('E4', 1), ('D4', 2), ('B3', 1),
       ('A3', 2), ('A3', 1), ('D4', 2), ('F#4', .5), ('D4', .5), ('F#4', 2), ('E4', 1), ('D4', 3)]
# harmonia por compasso (a anacruse fica sobre o compasso anterior)
HARM = ['D', 'G', 'D', 'A', 'D', 'G', 'A', 'D', 'D', 'G', 'D', 'D', 'Bm', 'A', 'D']
CH = {'D': ('D', 'F#', 'A'), 'G': ('G', 'B', 'D'), 'A': ('A', 'C#', 'E'), 'Bm': ('B', 'D', 'F#')}
def tri(c, octave):
    r, t, f = CH[c]; base = nm(r + str(octave)); third = nm(t + str(octave)); fifth = nm(f + str(octave))
    if third < base: third += 12
    while fifth < third: fifth += 12
    return base, third, fifth

class Track:
    def __init__(self, seconds): self.n = int(seconds * SR); self.x = np.zeros((self.n, 2))
    def add(self, t, y, g=1.0, pan=0.0):
        if y.ndim == 1: y = np.stack([y * (1 - pan) ** .5, y * (1 + pan) ** .5], 1) * .75
        i = int(t * SR); j = min(self.n, i + len(y))
        if j > i: self.x[i:j] += y[:j - i] * g

def pad(m, d, g): return TA.strings_note(m, d, 1500, 2.2) * g

def arpeggio_bar(tr, t0, chord, octave, g, pattern=(0, 2, 1, 2, 1, 2), vel=.45, pan=-.2):
    r, th, f = tri(chord, octave); notes = [r, th, f, r + 12]
    for k, idx in enumerate(pattern): tr.add(t0 + k * BEAT / 2, piano([r, th + 12 if idx == 1 else th, f][idx] if idx < 3 else notes[3], 2.0, vel), g, pan)

def melody(tr, t0, transpose, g, vel=.7, double=0.0, grace=False, pan=.18):
    t = t0
    for k, (n, b) in enumerate(MEL):
        m = nm(n) + transpose
        if grace and b >= 2 and k > 0: tr.add(t - .07, piano(m + 2, 1.0, .35), g * .4, pan)
        tr.add(t, piano(m, max(2.5, b * BEAT + 1.5), vel), g, pan)
        if double: tr.add(t, piano(m + 12, 2.5, .3), g * double, pan + .1)
        t += b * BEAT
    return t

def verse_bars(t_pickup):
    """Início de cada compasso (a anacruse ocupa 1 tempo antes do compasso 1)."""
    return [t_pickup + BEAT + i * 3 * BEAT for i in range(len(HARM))]

def build(dst):
    VERSE = sum(b for _, b in MEL) * BEAT; INTRO = 4 * 3 * BEAT
    total = INTRO + 3 * VERSE + 2 * INTRO + INTRO + 6.0
    tr = Track(total + 8)
    t = 0.0
    # introdução: arpejos D – G – D – A
    for i, c in enumerate(['D', 'G', 'D', 'A']): arpeggio_bar(tr, t + i * 3 * BEAT, c, 3, .5)
    for m in ('D3', 'A3', 'F#4'): tr.add(t, pad(nm(m), INTRO, .1))
    t += INTRO - BEAT
    # variação I: melodia simples, acordes em blocos
    bars = verse_bars(t)
    melody(tr, t, 12, .6, .62)
    for i, c in enumerate(HARM):
        r, th, f = tri(c, 2); tr.add(bars[i], piano(r, 3, .5), .4, -.25); tr.add(bars[i] + BEAT, piano(th + 12, 2, .35), .3, -.2); tr.add(bars[i] + 2 * BEAT, piano(f + 12, 2, .35), .3, -.2)
        for m in tri(c, 3): tr.add(bars[i], pad(m, 3 * BEAT + .5, .07))
    t = bars[-1] + 3 * BEAT
    # interlúdio
    for i, c in enumerate(['G', 'D', 'Bm', 'A']): arpeggio_bar(tr, t + i * 3 * BEAT, c, 3, .45, (0, 1, 2, 1, 2, 1))
    t += INTRO - BEAT
    # variação II: uma oitava acima, mão esquerda em arpejos, violoncelo em contracanto
    bars = verse_bars(t)
    melody(tr, t, 24, .55, .7, double=.0, grace=True)
    for i, c in enumerate(HARM):
        arpeggio_bar(tr, bars[i], c, 3, .38)
        r, th, f = tri(c, 2); tr.add(bars[i], cello(r, 3 * BEAT + .3), .22, -.35)
        for m in tri(c, 4): tr.add(bars[i], pad(m, 3 * BEAT + .5, .06))
    t = bars[-1] + 3 * BEAT
    # interlúdio
    for i, c in enumerate(['D', 'G', 'A', 'A']): arpeggio_bar(tr, t + i * 3 * BEAT, c, 4, .38, (2, 1, 0, 1, 2, 1))
    t += INTRO - BEAT
    # variação III: melodia no grave (tenor), arpejos no agudo
    bars = verse_bars(t)
    melody(tr, t, 0, .62, .66, pan=-.15)
    for i, c in enumerate(HARM):
        arpeggio_bar(tr, bars[i], c, 5, .26, (0, 1, 2, 1, 2, 1), vel=.35, pan=.35)
        for m in tri(c, 3): tr.add(bars[i], pad(m, 3 * BEAT + .5, .07))
    t = bars[-1] + 3 * BEAT
    # coda: volta ao acorde inicial, como a introdução
    for i, c in enumerate(['G', 'D', 'A', 'D']): arpeggio_bar(tr, t + i * 3 * BEAT, c, 3, .4 * (1 - .15 * i))
    end = t + 4 * 3 * BEAT
    # reverberação própria (o buffer pode passar dos 90 s do barramento do trailer)
    x = tr.x
    from scipy import signal
    n = int(4.2 * SR); tt = np.arange(n) / SR
    irs = [lp(np.random.default_rng(s).normal(0, 1, n) * np.exp(-tt * 6.9 / 4.2), 4800, 2) for s in (1, 2)]
    irs = [ir / np.sqrt((ir ** 2).sum()) for ir in irs]
    mono = x.mean(1); wet = np.stack([signal.fftconvolve(mono, ir)[:len(x)] for ir in irs], 1)
    y = x + wet * .5
    L = int(end * SR)
    loop = y[:L].copy(); tail = y[L:]
    loop[:len(tail)] += tail[:L]                    # a cauda do fim cai sobre o começo: loop sem emenda
    loop = hp(loop, 40, 2); loop = loop / np.max(np.abs(loop)) * .7
    wav = Path(dst).with_suffix('.wav'); wavfile.write(wav, SR, (loop * 32767).astype(np.int16))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(wav), '-af', 'loudnorm=I=-22:TP=-2:LRA=9', '-ar', '48000',
                    '-c:a', 'libvorbis', '-q:a', '4', str(dst)], check=True)
    wav.unlink(); print('ok', dst, round(end, 1), 's')

if __name__ == '__main__':
    build(sys.argv[1])
