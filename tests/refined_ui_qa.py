"""Real UI source in Chromium but isolated memory fixtures due browser navigation policy.
Test operations, semantics and render quality. Not a network/PWA production test.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json,re,base64,mimetypes
root=Path(__file__).resolve().parents[1]
html=(root/'index.html').read_text()
css=(root/'src/styles.css').read_text()+'\n'+(root/'src/refined.css').read_text()+'\n'+(root/'src/premium.css').read_text()
js=(root/'src/main.js').read_text()
js='\n'.join(x for x in js.splitlines() if not x.startswith('import '))
audiojs=(root/'src/ambience.js').read_text()
mock_catalog=json.loads((root/'content/catalog.json').read_text())
mock_sections={x['id']:json.loads((root/'content/reading'/f"{x['id']}.json").read_text()) for x in mock_catalog['reading']}
assets={}
for rel in ['branding/cover.webp','branding/compass.webp','branding/part1.webp','branding/lighthouse.webp','branding/archive.svg','branding/atlas.svg','branding/wordmark.svg','branding/grain.png','branding/cartographic-frontispiece.webp','experience/hero-panorama.webp','experience/edition-paper.webp','experience/archive-frontispiece.webp']:
 f=root/'assets'/rel
 mime=mimetypes.guess_type(str(f))[0] or 'image/webp'
 assets['/assets/'+rel]=f'data:{mime};base64,'+base64.b64encode(f.read_bytes()).decode()
for url,data in assets.items():css=css.replace("url('"+url+"')", "url('"+data+"')")
html=re.sub(r'<link[^>]+href="/[^>]+>','',html)
html=re.sub(r'<script type="module"[^>]*></script>','',html)
html=html.replace('</head>','<style>'+css+'</style></head>')
for url,data in assets.items():html=html.replace('src="'+url+'"','src="'+data+'"')
prelude="""
const MOCK_KV=new Map();const MOCK_MARKS=new Map();
const db={get:async key=>MOCK_KV.get(key),put:async(key,value,store='kv')=>{(store==='kv'?MOCK_KV:MOCK_MARKS).set(key,value)},remove:async(key,store='kv')=>{(store==='kv'?MOCK_KV:MOCK_MARKS).delete(key)},all:async()=>[...MOCK_MARKS.values()],reset:async()=>{MOCK_KV.clear();MOCK_MARKS.clear()}};
const catalog=async()=>window.MOCK_CATALOG;
const section=async id=>window.MOCK_SECTIONS[id];
const normalize=s=>String(s||'').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
"""
checks=[]
def check(test,ok):
 checks.append((test,bool(ok)));print(('PASS' if ok else 'FAIL'),test)

def hydrate(page):
 page.evaluate('imgs=>{for(const img of document.querySelectorAll("img"))if(imgs[img.getAttribute("src")])img.src=imgs[img.getAttribute("src")]}',assets)

with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 for device,width,height in [('small',320,690),('mobile',390,844),('tablet',768,1024),('desktop',1440,900)]:
  page=browser.new_page(viewport={'width':width,'height':height},has_touch=device!='desktop',is_mobile=device!='desktop',accept_downloads=True,reduced_motion='reduce')
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html,wait_until='domcontentloaded')
  page.evaluate('v=>{window.MOCK_CATALOG=v[0];window.MOCK_SECTIONS=v[1]}',[mock_catalog,mock_sections])
  page.evaluate('src=>eval(src)',prelude+js)
  page.evaluate('src=>eval(src)',audiojs)
  try:
   page.locator('.v3-hero').wait_for(timeout=8000);hydrate(page)
   check(f'{device} Átrio cinematográfico',page.locator('.v3-hero-logo').count()==1 and page.locator('.v3-feature').count()==4)
   check(f'{device} Átrio sem scroll horizontal',page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 2'))
   check(f'{device} rolagem do Átrio tem controle acionável',page.locator('button[data-action="scroll-salas"]').count()==1)
   check(f'{device} Observatório possui acesso',page.locator('a[href="#/observatorio"]').count()>=1)
   if width<650:
    check(f'{device} navegação inferior distribuída',page.locator('.mobile-nav').evaluate('(x)=>getComputedStyle(x).display')=='grid')
   page.locator('button[data-action="open-film"]').click()
   check(f'{device} filme com player real',page.locator('.film-dialog video[controls]').count()==1)
   page.locator('button[data-action="close-modal"]').click()
   check(f'{device} Ambiências reais: três escolhas',page.locator('[data-sound]').count()==3)
   page.locator('#ambience-toggle').click();check(f'{device} painel de som abre',page.locator('#ambient-panel').is_visible())
   page.locator('[data-sound="vento"]').click();check(f'{device} seleção de vento',page.locator('[data-sound="vento"]').get_attribute('aria-pressed')=='true')
   page.locator('#ambient-volume').fill('50');check(f'{device} volume funcional',page.locator('#ambient-volume-label').inner_text()=='50%')
   page.locator('#ambient-close').click();check(f'{device} painel fecha',not page.locator('#ambient-panel').is_visible())
   page.screenshot(path=str(root/'tests'/f'v3_atrium_{device}.png'),full_page=True)
   page.locator('a[href="#/ler/prologue"]').first.click();page.locator('#reader-article').wait_for(timeout=8000)
   check(f'{device} prólogo integral carregado',page.get_by_text('A primeira luz era a que todos esperavam.').count()>0)
   check(f'{device} leitor sem sidebar',page.evaluate("document.body.classList.contains('is-reading')"))
   check(f'{device} leitor sem scroll horizontal',page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 2'))
   page.screenshot(path=str(root/'tests'/f'v3_reader_{device}.png'),full_page=False)
   page.locator('button[data-action="reader-settings"]').click();page.locator('#pref-size').wait_for()
   page.locator('button[data-pref="theme"][data-value="noite"]').click()
   check(f'{device} tema noturno',page.locator('.reader-shell[data-reader-theme="noite"]').count()==1)
   page.locator('button[data-action="close-modal"]').click()
   page.locator('button[data-action="reader-toc"]').click()
   check(f'{device} índice com 67 entradas',page.locator('.toc-row').count()==67)
   page.locator('a.toc-row[href="#/ler/ch1"]').click();page.locator('.reader-heading').get_by_text('O funeral do faroleiro').wait_for()
   page.locator('button[data-action="bookmark"]').click();page.locator('button[data-action="reader-notes"]').click()
   check(f'{device} marcador funcional',page.locator('.note-item').count()==1)
   page.locator('button[data-action="close-modal"]').click()
   page.evaluate("location.hash='#/atlas'");page.locator('.atlas-selector').wait_for()
   check(f'{device} mapa protegido',page.locator('.atlas-selector button:not([disabled])').count()==0)
   page.evaluate("location.hash='#/galeria'");page.locator('.gallery-preface').wait_for()
   check(f'{device} galeria sem spoilers',page.locator('.watercolor-tile').count()==0)
   page.evaluate("location.hash='#/ler/ch1'");page.locator('#reader-article').wait_for()
   page.locator('button[data-action="complete"]').click()
   page.evaluate("location.hash='#/atlas'");page.locator('.atlas-selector').wait_for()
   check(f'{device} mapa desbloqueado',page.locator('.atlas-selector button:not([disabled])').count()>=1)
   page.evaluate("location.hash='#/galeria'");page.locator('.gallery-preface').wait_for()
   check(f'{device} galeria desbloqueada após capítulo',page.locator('.watercolor-tile').count()==1)
   page.locator('.watercolor-tile').first.click();check(f'{device} aquarela ampliável',page.locator('.artwork-view img').count()==1)
   page.locator('button[data-action="close-modal"]').click()
   page.evaluate("location.hash='#/busca'");page.locator('#search-input').wait_for();page.locator('#search-input').fill('Miguel');page.locator('#search-form button').click();page.locator('.search-hit').first.wait_for(timeout=8000)
   check(f'{device} busca protegida',page.locator('.search-hit').count()>0)
   page.evaluate("location.hash='#/biblioteca'");page.locator('.part-list').wait_for()
   check(f'{device} biblioteca integral',page.locator('.chapter-row').count()==67)
   check(f'{device} nenhum erro JS',not errors)
   if errors:print('SCRIPT ERRORS',errors)
  except Exception as exc:
   check(f'{device}: smoke test interrompido',False);print('TEST ERROR',str(exc)[:1200],errors)
  page.close()
 browser.close()
(root/'tests/v3_results.json').write_text(json.dumps({'mode':'Browser source UI with mocked fetch and memory storage due policy blocked localhost','tests':[{'name':n,'passed':passed} for n,passed in checks]},ensure_ascii=False,indent=2))
print('RESULT',sum(x[1] for x in checks),'/',len(checks))
