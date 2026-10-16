#!/usr/bin/env python3
"""Prepara uma gravação como fundo de leitura em repetição (assets/audio/graca.ogg).

Corta o silêncio do começo e do fim, faz fades curtíssimos nas pontas (sem clique na volta) e normaliza em −18 LUFS,
abaixo das ambiências do painel, para não competir com o texto. A faixa toca inteira e recomeça do início, como uma
música posta para repetir.
Uso: python3 tools/fundo_leitura.py <faixa> assets/audio/graca.ogg
"""
import subprocess, sys
import numpy as np
from scipy.io import wavfile
SR = 48000

def build(src, dst):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)
    hop = SR // 100; e = np.sqrt(np.convolve((x ** 2).mean(1), np.ones(hop) / hop, 'same'))
    loud = np.flatnonzero(e > 10 ** (-50 / 20))
    a = max(0, loud[0] - SR // 4); b = min(len(x), loud[-1] + SR // 2)
    y = x[a:b].copy(); f = int(.012 * SR); ramp = np.linspace(0, 1, f)[:, None]
    y[:f] *= ramp; y[-f:] *= ramp[::-1]
    wav = dst + '.wav'; wavfile.write(wav, SR, (np.clip(y, -1, 1) * 32767).astype(np.int16))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-af', 'loudnorm=I=-18:TP=-2:LRA=9', '-ar', str(SR),
                    '-c:a', 'libvorbis', '-q:a', '3', dst], check=True)
    subprocess.run(['rm', wav]); print('ok', dst, round(len(y) / SR, 1), 's')

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
