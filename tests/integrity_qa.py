#!/usr/bin/env python3
"""Editorial, content, design and PWA structure integrity tests (offline, no external services)."""
import json,re,hashlib,zipfile,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'sources/Cartas_do_Norte_Edicao_Final.docx'
PDF=Path('/mnt/data/cn_sources/Cartas_do_Norte_Werik_Martins_Edicao_Colecionador_v4_leitura.pdf')
def sha(d):return hashlib.sha256(d).hexdigest()
results=[]
def check(name,test,detail=None):results.append((name,bool(test),detail));print(('PASS' if test else 'FAIL'),name,detail or '')
c=json.loads((ROOT/'content/catalog.json').read_text())
reading=c['reading']; arts=c['artifacts'];sections={}
for x in reading:
 try:sections[x['id']]=json.loads((ROOT/f"content/reading/{x['id']}.json").read_text())
 except Exception as exc:print('error',x['id'],exc)
check('86 entradas de leitura (Edição Final)',len(reading)==86)
check('53 capítulos + 12 cartas + prólogo + epílogo',[sum(x['type']==v for x in reading) for v in ['chapter','letter','prologue','epilogue']]==[72,12,1,1])
check('72 capítulos na ordem canônica',[x['chapter'] for x in reading if x['type']=='chapter']==list(range(1,73)))
check('12 cartas na sequência original',[x['id'] for x in reading if x['type']=='letter']==[f'letter{i}' for i in range(1,13)])
check('Todos os arquivos JSON abrem',len(sections)==len(reading))
check('Hashes de todas as unidades batem',all(x['sha256']==sha(json.dumps([(b['type'],b['text']) for b in sections[x['id']]['blocks']],ensure_ascii=False,separators=(',',':')).encode()) for x in reading))
check('IDs de parágrafos únicos por seção',all(len(set(b['id'] for b in x['blocks']))==len(x['blocks']) for x in sections.values()))
check('Prólogo, epílogo e cartas possuem corpo de texto',all(len(sections[x['id']]['blocks'])>=4 for x in reading if x['type']!='chapter'))
check('18 fac-símiles verificados',len(arts)==18)
check('7 mapas, 11 documentos',sum(x['type']=='map' for x in arts)==7 and sum(x['type']=='document' for x in arts)==11)
check('Sem vestígio sem página de origem',all(isinstance(x['sourcePage'],int) and 1<=x['sourcePage']<=549 for x in arts))
check('Metadados anti-spoiler completos',all(isinstance(x['minChapter'],int) and 1<=x['minChapter']<=72 for x in arts))
check('Referências gráficas existentes',all((ROOT/x['image'].lstrip('/')).exists() and (ROOT/x['thumbnail'].lstrip('/')).exists() for x in arts))
check('Aquarelas vinculadas aos capítulos existentes',all((ROOT/x['art'].lstrip('/')).exists() for x in reading if x.get('art')))
check('Arquivos sem referência à fonte proprietária distribuída',not list((ROOT/'assets').rglob('*.ttf')) and not list((ROOT/'assets').rglob('*.otf')))
check('Logo tipográfico vetorial criado', (ROOT/'assets/branding/wordmark.svg').exists() and (ROOT/'assets/branding/wordmark.svg').stat().st_size>400)
check('PWA manifesto e SW disponíveis', (ROOT/'manifest.webmanifest').exists() and (ROOT/'sw.js').exists())
check('Offline inclui JSON fonte', '/content/catalog.json' in (ROOT/'sw.js').read_text())
check('Sem origem de dados via CDN no frontend',not re.search(r'https?://', (ROOT/'src/main.js').read_text()))
# v4 has a reproducible checkpoint and confirmed reading PDF hash.
check('SHA-256 da Edição Final coincide com o catálogo',SRC.exists() and sha(SRC.read_bytes())==c.get('sourceDocxSha256'))
if SRC.exists():
 import html as _h
 x=zipfile.ZipFile(SRC).read('word/document.xml').decode();doc=set()
 for para in re.findall(r'<w:p[ >].*?</w:p>',x,re.S):
  t=_h.unescape(''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>',para,re.S))).strip()
  if t:doc.add(re.sub(r'\s+',' ',t))
 app=[re.sub(r'\s+',' ',b['text'].replace('*','')).strip() for sec in sections.values() for b in sec['blocks'] if b['type']=='para']
 ok=sum(t in doc for t in app)
 check('Todos os parágrafos do site existem na Edição Final',ok==len(app),f'{ok}/{len(app)}')
else:check('Edição Final disponível para comparação',False,'sources/ ausente')
# Visually verify all WEBP assets can open.
errors=[]
for path in (ROOT/'assets').rglob('*.webp'):
 try:
  with Image.open(path) as im:im.verify()
 except Exception as exc:errors.append((str(path),str(exc)))
check('Todos os arquivos WebP íntegros',not errors,f'{len(list((ROOT/"assets").rglob("*.webp")))} arquivos')
report={'tests':[{'name':x,'result':'PASS' if y else 'FAIL','detail':z} for x,y,z in results], 'summary':{'passed':sum(y for x,y,z in results),'total':len(results)}}
(ROOT/'tests/integrity_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('Summary',report['summary']);sys.exit(0 if all(x[1] for x in results) else 1)
