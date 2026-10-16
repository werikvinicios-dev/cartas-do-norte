"""Build vector title letterforms from licensed editorial source at build time; no font files included in distribution."""
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from pathlib import Path
import zipfile,re,argparse
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--package',required=True,help='Caminho para o pacote original de produção v4');args=parser.parse_args()
z=zipfile.ZipFile(args.package)
font=z.read('Cartas_do_Norte_v4/assets/fonts/Cartas_do_Norte_Oficial.ttf')
p=root/'tools/.titlefont-temp.ttf';p.write_bytes(font)
f=TTFont(p);cmap=f.getBestCmap();gly=f.getGlyphSet();hmtx=f['hmtx'];units=f['head'].unitsPerEm

def render(text,slug):
 # font's glyph outlines become small standalone svg files
 off=0;paths=[]
 for ch in text:
  gn=cmap.get(ord(ch));
  if not gn:off+=units*.36;continue
  pen=SVGPathPen(gly);gly[gn].draw(pen)
  path=pen.getCommands();paths.append(f'<path d="{path}" transform="translate({off:.2f},0)"/>')
  off+=hmtx[gn][0]*1.035
 w=off
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {-units*0.83:.0f} {w:.0f} {units*1.12:.0f}" role="img"><g fill="currentColor" transform="scale(1,-1)">{''.join(paths)}</g></svg>'''
 # svgs with fill as default dark/gold, no external font 
 svg=svg.replace('fill="currentColor"','fill="#c5a46b"')
 (root/'assets/branding'/slug).write_text(svg,encoding='utf8')

render('CARTAS DO NORTE','wordmark.svg')
render('O ARQUIVO VIVO','archive.svg')
render('BIBLIOTECA','library.svg')
render('O ACERVO','acervo.svg')
render('ATLAS','atlas.svg')
print('generated outlined titles')
p.unlink()
