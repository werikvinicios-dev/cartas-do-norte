#!/usr/bin/env python3
"""Versões curtas a partir do trailer principal (vídeo e som cortados juntos, com fusões curtas).

  30 s: funeral + frases · caixão · farol apagado · "Começam quando…" · "Entre a culpa… / entre aquilo que perdemos…" · emblema e chamada
  15 s: o mar · farol apagado · "Entre a culpa e a verdade…" · emblema e chamada
Uso: python3 tools/trailer_cortes.py <principal.mp4> <saida_30.mp4> <saida_15.mp4>
"""
import subprocess, sys
CUTS = {
    '30': [(8.0, 11.6), (12.3, 15.3), (15.4, 18.4), (38.4, 43.8), (44.0, 52.4), (71.0, 80.0)],
    '15': [(2.6, 6.2), (15.4, 18.0), (44.0, 47.4), (73.6, 80.0)],
}
X = .5  # fusão entre segmentos

def make(src, dst, segs):
    inputs, fv, fa = [], [], []
    for i, (a, b) in enumerate(segs):
        inputs += ['-ss', str(a), '-t', str(b - a), '-i', src]
    lv, la, off = '[0:v]', '[0:a]', segs[0][1] - segs[0][0]
    for i in range(1, len(segs)):
        o = off - X
        fv.append(f'{lv}[{i}:v]xfade=transition=fade:duration={X}:offset={o:.3f}[v{i}]'); lv = f'[v{i}]'
        fa.append(f'{la}[{i}:a]acrossfade=d={X}[a{i}]'); la = f'[a{i}]'
        off += (segs[i][1] - segs[i][0]) - X
    graph = ';'.join(fv + fa)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', graph, '-map', lv, '-map', la,
                    '-c:v', 'libx264', '-crf', '20', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                    '-movflags', '+faststart', dst], check=True)

if __name__ == '__main__':
    src, d30, d15 = sys.argv[1:4]
    make(src, d30, CUTS['30']); make(src, d15, CUTS['15'])
