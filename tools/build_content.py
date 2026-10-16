#!/usr/bin/env python3
"""Rebuild canonical reader content from approved Cartas do Norte production package + v4 reading PDF.
Requires PyMuPDF and Pillow; sources are NOT part of distributed app.
Usage: python tools/build_content.py --package /path/to/v4zip --pdf /path/to/v4_leitura.pdf
"""
import os,re,json,sys,argparse,zipfile,hashlib,io,unicodedata
from pathlib import Path
from collections import Counter
from PIL import Image
import fitz
ROOT=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def write(p,x):
 p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def wasset(path,blob,size=None,quality=80):
 if (ROOT/path).exists():
  f=ROOT/path
  return dict(path='/'+str(path),bytes=f.stat().st_size,sha256=sha(f.read_bytes()))
 im=Image.open(io.BytesIO(blob)).convert('RGB')
 if size:
  im.thumbnail(size,Image.Resampling.LANCZOS)
 out=ROOT/path;out.parent.mkdir(parents=True,exist_ok=True);im.save(out,'WEBP',quality=quality,method=4)
 return dict(path='/'+str(path),bytes=out.stat().st_size,sha256=sha(out.read_bytes()),width=im.width,height=im.height)
# O fac-símile antigo dizia "O Diário Azul" e assinava "Jonas"; no cap. 14 estas linhas são do diário de Elias Moura
# (a imagem assets/docs/diary_blue.webp já foi corrigida)
# ("Ana leu uma última linha escrita por Elias"). A transcrição não pode atribuí-las a Jonas.
TRANSCRIPTION_FIXES={'diary_blue':[('O\xa0Diário\xa0Azul\n','O Diário de Elias\n'),('O Diário Azul\n','O Diário de Elias\n'),('\nJonas','\nElias')]}
def clean(s):return re.sub(r'\s+',' ',s).strip()
def extract_prose(d,from_page,to_page,kind):
 # 1-based inclusive pages; use exact embedded PDF text, discard running heads and folios
 paras=[]; prev_end=None; page_boundaries=[]
 for page_num in range(from_page,to_page+1):
  page=d[page_num-1]; lines=[]
  for blk in page.get_text('dict')['blocks']:
   for l in blk.get('lines',[]):
    tx=''.join(s['text'] for s in l['spans']).strip()
    if not tx:continue
    x,y,x2,y2=l['bbox']
    if y < 43 or y > 600:continue
    # Strip running heads of the book, but not canonical prose.
    if tx.upper() in ('CARTAS DO NORTE','PARTE I — A COSTA','PARTE II — AS ÁGUAS PROFUNDAS','PARTE III — A TEMPESTADE','PARTE IV — O FAROL','EPÍLOGO') and y < 55:continue
    lines.append((round(y,1),round(x,1),round(y2,1),tx))
  lines.sort()
  if not lines:continue
  # The first text pages of prologue / epilogue contain a subtitle y<=95.
  for j,(y,x,y2,txt) in enumerate(lines):
   if kind in ('prologue','epilogue') and page_num==from_page and y<95:continue
   if kind=='letter' and page_num==from_page and re.match(r'^CARTA\s+[IVX]+$',txt,re.I):continue
   if kind=='letter' and page_num==from_page and txt.strip()=='Sumário':continue
   if re.fullmatch(r'\d+',txt):continue
   newpara=False
   if not paras: newpara=True
   elif j==0 and page_num!=from_page:
    # Page breaks inside a paragraph should not introduce a break.
    newpara=bool(re.search(r'[.!?…»”]$',paras[-1]))
   elif prev_end is None:newpara=True
   elif (y-prev_end)>7.6:newpara=True
   if newpara:paras.append(txt)
   else:
    if paras:paras[-1]=paras[-1].rstrip()+('' if paras[-1].endswith('-') else ' ')+txt
    else:paras.append(txt)
   prev_end=y2
  prev_end=None
 return [p for p in paras if p]
def make_blocks(raw):
 c=Counter();blocks=[]
 for typ,txt in raw:
  if not str(txt).strip():continue
  if typ in ('h1','h2') and str(txt).strip().isdigit():continue
  text=str(txt);digest=sha(text.encode())[:12];c[digest]+=1
  blocks.append({'id':f'p-{digest}-{c[digest]}','type':typ,'text':text})
 return blocks

def main(package,pdf):
 pdf_blob=Path(pdf).read_bytes();pdf_sha=sha(pdf_blob);d=fitz.open(pdf);toc=d.get_toc()
 with zipfile.ZipFile(package) as z:
  prefix='Cartas_do_Norte_v4/'
  def load(p):return z.read(prefix+p)
  source=json.loads(load('manifests/chapters.json'))
  special=json.loads(load('manifests/specials_v4.json'))
  cp=json.loads(load('manifests/checkpoint_v4_final.json'))
  titlefont=load('assets/fonts/Cartas_do_Norte_Oficial.ttf')
  reading=[];parts=[];part='Prólogo';last_index=0
  roman={1:'I',2:'II',3:'III',4:'IV',5:'V',6:'VI',7:'VII',8:'VIII',9:'IX',10:'X',11:'XI',12:'XII'}
  for i,(depth,title,start) in enumerate(toc):
   if title.startswith('PARTE '):
    part=title;parts.append({'title':title,'page':start,'order':len(reading)})
    continue
   match=re.match(r'^Capítulo\s+(\d+)\s+[—–]\s+(.+)',title)
   if match:
    n=int(match.group(1)); item=source[n-1]
    assert item['id']==n and item['title'].casefold()==match.group(2).casefold(),(title,item['title'])
    blocks=make_blocks(item['blocks']);typ='chapter';rid='ch'+str(n);heading=item['title'];min_ch=n
    provenance={'source':'production-v4:manifests/chapters.json','original_chapter_ids':item['originals'],'source_pdf_page':start,'verification':'structured-source'}
   elif title.startswith('CARTA '):
    m=re.search('CARTA ([IVX]+)',title);num=next((k for k,v in roman.items() if v==m.group(1)),None)
    if num is None:continue
    rid='letter'+str(num);typ='letter';heading=f'Carta {roman[num]}'
    nextstart=next((r[2] for r in toc[i+1:] if (r[1].startswith('Capítulo') or r[1].startswith('CARTA') or r[1].startswith('PARTE') or r[1]=='Epílogo')),start+2)
    raw=extract_prose(d,start,nextstart-1,'letter')
    blocks=make_blocks([('para',x) for x in raw]);min_ch=int(re.search(r'Capítulo\s+(\d+)',next((t[1] for t in reversed(toc[:i]) if t[1].startswith('Capítulo')),'Capítulo 1')).group(1));
    provenance={'source':'collector-v4-reading-pdf','source_pdf_pages':[start,nextstart-1],'verification':'pdf-extracted-needs-human-paragraph-proof'}
   elif title=='Prólogo' or title=='Epílogo':
    typ='prologue' if title=='Prólogo' else 'epilogue';rid=typ;heading=title
    if typ=='prologue':raw=extract_prose(d,14,17,typ);subtitle='A segunda luz';min_ch=0
    else:raw=extract_prose(d,545,548,typ);subtitle='Uma carta para quem retorna';min_ch=53
    blocks=make_blocks([('para',x) for x in raw]);provenance={'source':'collector-v4-reading-pdf','source_pdf_pages':[14,17] if typ=='prologue' else [545,548],'verification':'pdf-extracted-needs-human-paragraph-proof'}
   else:continue
   data={'id':rid,'type':typ,'title':heading,'subtitle':subtitle if typ in ('prologue','epilogue') else None,'part':part,'blocks':blocks,'provenance':provenance}
   data['blocks_sha256']=sha(json.dumps([(b['type'],b['text']) for b in blocks],ensure_ascii=False,separators=(',',':')).encode())
   write(f'content/reading/{rid}.json',data)
   reading.append({'id':rid,'type':typ,'title':heading,'part':part,'chapter':n if typ=='chapter' else None,'page':start,'blocks':len(blocks),'minChapter':min_ch,'sha256':data['blocks_sha256']})
  assert len(reading)==67,(len(reading),Counter(x['type'] for x in reading)) # 53 chapters + 12 letters + prologue + epilogue
  # Approved maps are rendered directly from FINAL PDF so their labels/illustration remain canonical.
  artifacts=[]
  artifact_meta={
   'map_stage_1':('map','A Costa e o Primeiro Rumo',1,'Mapa progressivo do litoral'),
   'map_stage_2':('map','Águas Profundas',14,'Mapa progressivo da travessia'),
   'map_stage_3':('map','A Rota sob a Tempestade',24,'Mapa progressivo da tempestade'),
   'map_stage_4':('map','O Regresso à Luz',39,'Mapa progressivo do retorno'),
   'canal_chart':('map','Carta do Canal da Agulha',3,'Levantamento costeiro'),
   'gruta_map':('map','Mapa da Gruta das Vozes',33,'Cartografia do arquipélago'),
   'north_restored_chart':('map','Carta Restaurada do Norte',53,'Cartografia restaurada'),
  }
  # Infer images by toc rows; metadata from special manifests authoritative for source chapter
  specials={x['id']:x for x in special.get('replace_pages_v3',[])+special.get('insert_before_v3',[])}
  docidmap={'Documento — O Testamento':'testament','Documento — O Diário Azul':'diary_blue','Documento — A Ordem Guardada':'order','Documento — O Tubo de Latão':'brass_tube',
  'Documento — Prancha da Constância':'constancia_blueprint','Documento — A Folha dos Passageiros':'passenger_register','Documento — Fita do Registro de Rádio':'radio_log','Documento — A Folha no Bolso':'tomas_note','Documento — Transmissão da Estação Norte':'balu_transmission','Documento — Carta de Ana':'ana_letter','Documento — Extrato da Sentença':'sentence_extract',
  'Mapa narrativo — Carta do Canal da Agulha':'canal_chart','Mapa narrativo — Mapa da Gruta das Vozes':'gruta_map','Mapa narrativo — Carta Restaurada do Norte':'north_restored_chart',
  'Mapa progressivo — A Costa e o Primeiro Rumo':'map_stage_1','Mapa progressivo — Águas Profundas':'map_stage_2','Mapa progressivo — A Rota sob a Tempestade':'map_stage_3','Mapa progressivo — O Regresso à Luz':'map_stage_4'}
  for depth,title,page in toc:
   if title not in docidmap:continue
   id=docidmap[title];type='map' if title.startswith('Mapa') else 'document'
   s=specials.get(id,{})
   src_ch=s.get('source_chapter') or s.get('stage')
   if id in artifact_meta: src_ch=artifact_meta[id][2]
   if not src_ch:
    # conservative lock to last completed chapter prior to artifact
    preceding=[x for x in reading if x['type']=='chapter' and x['page']<=page]
    src_ch=(preceding[-1]['chapter'] if preceding else 53)
   pix=d[page-1].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False)
   im=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
   # crop page bottom folio + pad edge? Preserve all canonical image; images resized to max 950 wide
   ob=io.BytesIO();im.save(ob,format='PNG')
   path=f'assets/{"maps" if type=="map" else "docs"}/{id}.webp'
   asset=wasset(path,ob.getvalue(),(950,1440),81)
   thumbpath=f'assets/{"maps" if type=="map" else "docs"}/{id}_thumb.webp'
   wasset(thumbpath,ob.getvalue(),(320,480),72)
   # page original selectable text is best available transcription
   doc_lines=[]
   for blk in d[page-1].get_text('dict')['blocks']:
    for l in blk.get('lines',[]):
     y=l['bbox'][1]
     if y>600 or y<24:continue
     t=''.join(s['text'] for s in l['spans']).strip()
     if t and not re.fullmatch(r'\d+',t):doc_lines.append(t)
   transcript='\n'.join(doc_lines)
   # Correções editoriais conferidas com o romance: o fac-símile imprime algo que o texto contradiz.
   for a,b in TRANSCRIPTION_FIXES.get(id,[]):transcript=transcript.replace(a,b)
   artifacts.append({'id':id,'type':type,'title':title.replace('Mapa narrativo — ','').replace('Mapa progressivo — ','').replace('Documento — ','').replace('O Diário Azul','O Diário de Elias'),
    'sourcePage':page,'minChapter':src_ch,'image':asset['path'],'thumbnail':'/'+thumbpath,
    'transcription':transcript,'transcriptionStatus':'PDF extraction; revisão humana recomendada',
    'provenance':'Edição de Colecionador v4 (página %d)'%page,'sha256':asset['sha256']})
  # Additional maps and doc artifact names must not be made up; only verified TOC references.
  # A few artistic resources for navigation are generated from approved source images.
  asset_files={'cover':'assets/cover/capa_sem_linhas.png','logo':'assets/identity/logo_aprovada_dourada_transparente.png',
  'part1':'assets/part_frames/part_01_costa.png','part2':'assets/part_frames/part_02_aguas_profundas.png','part3':'assets/part_frames/part_03_tempestade.png','part4':'assets/part_frames/part_04_farol.png',
  'compass':'assets/ornaments/derived/bussola.png','lighthouse':'assets/ornaments/derived/farol.png','ship':'assets/ornaments/derived/navio.png'}
  for key,src in asset_files.items():
   raw=load(src);name='assets/branding/'+key+'.webp'
   if key in ('logo','compass','lighthouse','ship'):
    # alpha matters: webp supports transparency
    im=Image.open(io.BytesIO(raw)).convert('RGBA');im.thumbnail((600,850),Image.Resampling.LANCZOS)
    (ROOT/name).parent.mkdir(parents=True,exist_ok=True);im.save(ROOT/name,'WEBP',quality=83,method=4)
   else:wasset(name,raw,(1000,1500),81)
  # the complete source includes editorial approved chapter illustrations between opening and prose
  for x in reading:
   if x['type']!='chapter':continue
   page=x['page']+1
   if len(d[page-1].get_text().strip())>20:continue
   pix=d[page-1].get_pixmap(matrix=fitz.Matrix(1.35,1.35),alpha=False)
   wasset(f'assets/art/{x["id"]}.webp',pix.tobytes('png'),(680,1000),77)
   x['art']=f'/assets/art/{x["id"]}.webp'
  write('content/catalog.json',{'edition':'Edição de Colecionador v4','title':'Cartas do Norte','subtitle':'Uma jornada entre a névoa, o mar e a graça','author':'Werik Martins',
   'sourceReadingSha256':pdf_sha,'sourceHashExpected':cp['reading_pdf']['sha256'],'sourceHashMatched':pdf_sha==cp['reading_pdf']['sha256'],
   'canonicalTextExpectedSha256':cp['canonical_text_sha256'],'parts':parts,'reading':reading,'artifacts':artifacts})
  inventory=[]
  for x in reading:inventory.append({'id':x['id'],'title':x['title'],'type':x['type'],'status':'APROVADO' if x['type']=='chapter' else 'EXISTENTE, NÃO VALIDADO','source': 'manifests/chapters.json' if x['type']=='chapter' else 'PDF v4 leitura','minChapter':x['minChapter'],'integrity':x['sha256']})
  for a in artifacts:inventory.append({'id':a['id'],'title':a['title'],'type':a['type'],'status':'APROVADO (arte-facsímile)','source':'PDF v4, p. %d'%a['sourcePage'],'minChapter':a['minChapter'],'integrity':a['sha256']})
  write('docs/inventario_mestre.json',{'assets':inventory,'unverifiedTextExtraction':'Prólogo, epílogo e cartas precisam de conferência editorial de parágrafos no PDF.'})
  # Relative to official canon PDF, source blocks are immutable; internal digest re-validated by tests.
  print('Catalog:',len(reading),'items; chapters:',len(source),'letters:',sum(x['type']=='letter' for x in reading),'artifacts:',len(artifacts),'pdf hash matched?',pdf_sha==cp['reading_pdf']['sha256'])
  print('assets MB',round(sum(p.stat().st_size for p in (ROOT/'assets').rglob('*.webp'))/1e6,2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--package',required=True);ap.add_argument('--pdf',required=True);a=ap.parse_args();main(a.package,a.pdf)
