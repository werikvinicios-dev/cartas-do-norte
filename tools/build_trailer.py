#!/usr/bin/env python3
"""Trailer de Cartas do Norte (63 s, 1920×1080, 30 fps).

Usa apenas aquarelas aprovadas (capa, Parte I, capítulos 1 e 3, primeira carta cartográfica)
e frases literais do prólogo e dos capítulos 1 e 3, sem revelações além do começo da obra.
Os cartões de texto são PNGs transparentes renderizados com a tipografia do site (tools/trailer_cards.js).
Trilha original sintetizada + ambiências já existentes da edição (mar, vento).

Uso: python3 tools/build_trailer.py <pasta_dos_cartoes>
"""
import subprocess, sys, math
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
CARDS = Path(sys.argv[1])
W, H, FPS, DUR = 1920, 1080, 30, 63.0
OUT = ROOT / 'assets/video'
A = lambda p: Image.open(ROOT / p).convert('RGB')

def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def window(img, cx, cy, w):
    """Recorta uma janela 16:9 de largura w centrada em (cx, cy) e entrega 1920×1080 (subpixel, bicúbico)."""
    h = w * H / W
    # A câmera nunca sai da pintura.
    w = min(w, img.width); h = w * H / W
    cx = min(max(cx, w / 2), img.width - w / 2); cy = min(max(cy, h / 2), img.height - h / 2)
    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    return img.transform((W, H), Image.EXTENT, box, Image.BICUBIC)

def plate(path, offset=0):
    """Composição editorial: pintura inteira sobre um fundo desfocado e escurecido dela mesma."""
    img = A(path)
    bg = img.resize((W, int(img.height * W / img.width)), Image.BICUBIC)
    bg = bg.crop((0, (bg.height - H) // 2, W, (bg.height - H) // 2 + H)).filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.38)
    fh = 980; fw = int(img.width * fh / img.height)
    fg = img.resize((fw, fh), Image.LANCZOS)
    shadow = Image.new('RGBA', (fw + 80, fh + 80), (0, 0, 0, 0))
    sh = Image.new('RGBA', (fw, fh), (0, 0, 0, 170))
    shadow.paste(sh, (40, 40)); shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    x = (W - fw) // 2 + offset; y = (H - fh) // 2
    bg.paste(shadow, (x - 40, y - 20), shadow); bg.paste(fg, (x, y))
    return bg

def zoom(img, z, fx=0.5, fy=0.5):
    w = W / z; h = H / z
    cx = W * fx + (W / 2 - W * fx) / z; cy = H * fy + (H / 2 - H * fy) / z
    return img.transform((W, H), Image.EXTENT, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), Image.BICUBIC)

cover = A('assets/branding/cover.webp')
mapimg = A('assets/maps/map_stage_1.webp')
mist = Image.open(ROOT / 'assets/experience/mist.webp').convert('RGBA').resize((2048, 1024))
dark = Image.new('RGB', (W, H), (4, 15, 21))
cover_dark = ImageEnhance.Brightness(window(cover, 500, 760, 1000).filter(ImageFilter.GaussianBlur(18))).enhance(0.3)
P1, CH1, CH3 = plate('assets/branding/part1.webp'), plate('assets/art/ch1.webp', -420), plate('assets/art/ch3.webp', 420)
cards = {k: Image.open(CARDS / f'{k}.png').convert('RGBA') for k in ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'end']}

def with_mist(base, t, alpha=0.5):
    out = base.convert('RGBA')
    off = int(t * 22) % 2048
    layer = Image.new('RGBA', (W, H)); strip = mist.crop((off, 0, off + W, H)) if off + W <= 2048 else None
    if strip is None:
        strip = Image.new('RGBA', (W, 1024)); strip.paste(mist.crop((off, 0, 2048, 1024)), (0, 0)); strip.paste(mist.crop((0, 0, W - (2048 - off), 1024)), (2048 - off, 0))
    layer.paste(strip.resize((W, H)), (0, 0))
    layer.putalpha(layer.getchannel('A').point(lambda v: int(v * alpha)))
    return Image.alpha_composite(out, layer).convert('RGB')

# Plano de cena: (início, fim, função de quadro). Transições: dissolução de 1 s entre planos sobrepostos.
SHOTS = [
    (0, 6.5, lambda t: with_mist(dark, t, .55)),
    (5.5, 15.5, lambda t: window(cover, 500 + 40 * ease((t - 5.5) / 10), 300 + 450 * ease((t - 5.5) / 10), 1000 - 80 * ease((t - 5.5) / 10))),
    (14.5, 21.5, lambda t: ImageEnhance.Brightness(window(cover, 540 + 300 * ease((t - 14.5) / 7), 750 - 120 * ease((t - 14.5) / 7), 920 - 380 * ease((t - 14.5) / 7))).enhance(1 - .35 * ease((t - 15) / 1.5))),
    (20.5, 28.5, lambda t: zoom(P1, 1 + .07 * (t - 20.5) / 8)),
    (27.5, 36.5, lambda t: zoom(CH1, 1 + .06 * (t - 27.5) / 9, .3, .5)),
    (35.5, 43.5, lambda t: zoom(CH3, 1 + .06 * (t - 35.5) / 8, .7, .5)),
    (42.5, 49.5, lambda t: ImageEnhance.Brightness(window(mapimg, 432, 520 + 330 * ease((t - 42.5) / 7), 864 - 120 * ease((t - 42.5) / 7))).enhance(.42)),
    (48.5, 56.5, lambda t: with_mist(cover_dark, t, .45)),
    (55.5, DUR, lambda t: with_mist(cover_dark, t, .3)),
]
TEXT = [('c1', 1.0, 5.6), ('c2', 15.8, 20.6), ('c3', 29.0, 35.6), ('c4', 37.0, 42.8), ('c5', 44.0, 48.8),
        ('c6', 49.2, 51.6), ('c7', 51.8, 54.2), ('c8', 54.4, 56.6), ('end', 57.2, 63.0)]

def frame(t):
    active = [(a, b, f) for a, b, f in SHOTS if a <= t < b] or [SHOTS[-1]]
    img = active[0][2](t)
    if len(active) > 1:
        a2 = active[1]; k = ease((t - a2[0]) / 1.0)
        img = Image.blend(img, a2[2](t), k)
    img = img.convert('RGBA')
    for k, a, b in TEXT:
        if a <= t < b:
            al = min(ease((t - a) / .7), ease((b - t) / .7)) if k != 'end' else ease((t - a) / 1.2)
            c = cards[k].copy(); c.putalpha(c.getchannel('A').point(lambda v: int(v * al)))
            img = Image.alpha_composite(img, c)
    img = img.convert('RGB')
    if t > DUR - 1.6: img = Image.blend(img, dark, ease((t - (DUR - 1.6)) / 1.6))
    return img

def build_audio(path):
    bells = [6.4, 7.2, 8.0, 49.2, 51.8, 54.4, 57.2]
    inputs = ['-f', 'lavfi', '-i', f"aevalsrc='0.10*sin(2*PI*55*t)*(0.6+0.4*sin(2*PI*0.07*t))+0.07*sin(2*PI*82.41*t)*(0.6+0.4*sin(2*PI*0.05*t+1))+0.04*sin(2*PI*110*t)*(0.5+0.5*sin(2*PI*0.03*t))':s=48000:d={DUR}",
              '-stream_loop', '3', '-i', str(ROOT / 'assets/audio/mar.ogg'),
              '-stream_loop', '3', '-i', str(ROOT / 'assets/audio/vento.ogg')]
    for _ in bells:
        inputs += ['-f', 'lavfi', '-i', "aevalsrc='0.22*sin(2*PI*659.25*t)*exp(-2.2*t)+0.07*sin(2*PI*1318.5*t)*exp(-3.5*t)+0.05*sin(2*PI*988*t)*exp(-3*t)':s=48000:d=4.5"]
    f = ['[0]lowpass=f=700,volume=1.0[d]', f'[1]atrim=0:{DUR},volume=0.55,afade=t=in:d=4[m]', f'[2]atrim=0:{DUR},volume=0.4,afade=t=in:st=5:d=5[v]']
    labels = '[d][m][v]'
    for i, s in enumerate(bells):
        f.append(f'[{3 + i}]adelay={int(s * 1000)}|{int(s * 1000)},apad=whole_dur={DUR}[b{i}]'); labels += f'[b{i}]'
    f.append(f'{labels}amix=inputs={3 + len(bells)}:normalize=0,afade=t=in:d=2,afade=t=out:st={DUR - 3}:d=3,alimiter=limit=0.89,atrim=0:{DUR}[out]')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(f), '-map', '[out]', '-ac', '2', '-c:a', 'aac', '-b:a', '160k', str(path)], check=True)

if __name__ == '__main__':
    tmp = OUT / '_trailer_video.mp4'; aud = OUT / '_trailer_audio.m4a'
    build_audio(aud)
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-preset', 'slow', '-crf', '29', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(tmp)], stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        enc.stdin.write(frame(i / FPS).tobytes())
        if i % 150 == 0: print(f'{i}/{n}', flush=True)
    enc.stdin.close(); enc.wait()
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(tmp), '-i', str(aud), '-c', 'copy', '-shortest', '-movflags', '+faststart', str(OUT / 'trailer.mp4')], check=True)
    frame(25.0).resize((1280, 720), Image.LANCZOS).save(OUT / 'trailer-poster.webp', quality=82)
    tmp.unlink(); aud.unlink()
    print('ok', OUT / 'trailer.mp4')
