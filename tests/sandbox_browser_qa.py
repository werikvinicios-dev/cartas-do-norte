"""Chromium UI smoke tests under sandbox policy blocking all browser navigations.
Actual main.js source is executed after replacing only ES module imports with in-memory fixtures.
Validates UI/interaction behavior, NOT real network fetch, IndexedDB, Service Worker or Lighthouse.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json,re,base64
root=Path(__file__).resolve().parents[1]
html=(root/'index.html').read_text()
css=(root/'src/styles.css').read_text()
js=(root/'src/main.js').read_text()
js='\n'.join(x for x in js.splitlines() if not x.startswith('import {') and not x.startswith('import *'))
mock_catalog=json.loads((root/'content/catalog.json').read_text())
mock_sections={x['id']:json.loads((root/'content/reading'/f"{x['id']}.json").read_text()) for x in mock_catalog['reading']}
html=re.sub(r'<link[^>]+href="/[^>]+>','',html)
html=re.sub(r'<script type="module"[^>]*></script>','',html)
html=html.replace('</head>','<style>'+css+'</style></head>')
mock_prelude="""
const MOCK_KV = new Map();const MOCK_MARKS = new Map();
const db={get:async key=>MOCK_KV.get(key),put:async(key,value,store='kv')=>{(store==='kv'?MOCK_KV:MOCK_MARKS).set(key,value)},remove:async(key,store='kv')=>{(store==='kv'?MOCK_KV:MOCK_MARKS).delete(key)},all:async()=>[...MOCK_MARKS.values()],reset:async()=>{MOCK_KV.clear();MOCK_MARKS.clear()}};
const catalog=async()=>window.MOCK_CATALOG;
const section=async id=>window.MOCK_SECTIONS[id];
const normalize=s=>String(s||'').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
"""
results=[]
def check(name,condition):
 results.append((name,bool(condition)));print(('PASS' if condition else 'FAIL'),name)
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for device in ['mobile','desktop']:
  mobile=device=='mobile';page=browser.new_page(viewport={'width':390 if mobile else 1440,'height':844 if mobile else 900},has_touch=mobile,is_mobile=mobile,accept_downloads=True)
  errs=[];page.on('pageerror',lambda err:errs.append(str(err)))
  page.set_content(html,wait_until='domcontentloaded')
  page.evaluate('x=>{window.MOCK_CATALOG=x[0];window.MOCK_SECTIONS=x[1]}',[mock_catalog,mock_sections])
  page.evaluate('src=>{eval(src)}',mock_prelude+js)
  try:
   page.locator('.atrium-title').wait_for(timeout=8000)
   check(f'{device}: Átrio',True)
   image_path=root/'assets/branding/cover.webp'
   uri='data:image/webp;base64,'+base64.b64encode(image_path.read_bytes()).decode()
   page.locator('.hero-art img').evaluate('(el,url)=>el.src=url',uri)
   svg_uri='data:image/svg+xml;base64,'+base64.b64encode((root/'assets/branding/wordmark.svg').read_bytes()).decode()
   page.locator('.brand-wordmark').evaluate('(el,url)=>el.src=url',svg_uri)
   page.screenshot(path=str(root/'tests'/f'atrium_{device}.png'),full_page=True)
   page.locator('a[href="#/ler/prologue"]').first.click()
   page.locator('#reader-article').wait_for(timeout=8000)
   check(f'{device}: texto real do prólogo',page.get_by_text('A primeira luz era a que todos esperavam.').count()>0)
   page.screenshot(path=str(root/'tests'/f'reader_{device}.png'))
   page.locator('button[data-action="reader-settings"]').click()
   check(f'{device}: abrir preferências',page.locator('#pref-size').count()==1)
   page.locator('button[data-pref="theme"][data-value="noite"]').click()
   check(f'{device}: tema noite',page.locator('.reader-shell[data-reader-theme="noite"]').count()==1)
   page.locator('button[data-action="close-modal"]').click()
   page.locator('button[data-action="reader-toc"]').click()
   check(f'{device}: 67 entradas no índice',page.locator('.toc-row').count()==67)
   page.locator('a.toc-row[href="#/ler/ch1"]').click()
   page.locator('.reader-heading').get_by_text('O funeral do faroleiro').wait_for(timeout=8000)
   page.locator('#reader-article').wait_for(timeout=8000)
   check(f'{device}: capítulo real',page.get_by_text('Choveu no funeral de Jonas Vale',exact=False).count()>0)
   page.locator('button[data-action="reader-toc"]').click()
   check(f'{device}: sem spoiler no índice',page.locator('a.toc-row[href="#/ler/ch53"]').inner_text()=='Capítulo 53')
   page.locator('button[data-action="close-modal"]').click()
   page.locator('button[data-action="bookmark"]').click()
   page.locator('button[data-action="reader-notes"]').click()
   check(f'{device}: marcador gravado',page.locator('.note-item').count()==1)
   page.locator('button[data-action="close-modal"]').click()
   page.evaluate("location.hash='#/atlas'")
   page.locator('.atlas-selector').wait_for(timeout=8000)
   check(f'{device}: atlas protegido',page.locator('.atlas-selector button:not([disabled])').count()==0)
   page.evaluate("location.hash='#/ler/ch1'");page.locator('#reader-article').wait_for()
   page.locator('button[data-action="complete"]').click()
   page.evaluate("location.hash='#/atlas'");page.locator('.atlas-selector').wait_for()
   check(f'{device}: atlas desbloqueado',page.locator('.atlas-selector button:not([disabled])').count()>=1)
   page.evaluate("location.hash='#/busca'")
   page.locator('#search-input').wait_for();page.locator('#search-input').fill('Miguel');page.locator('#search-form button').click()
   page.locator('.search-hit').first.wait_for(timeout=8000)
   check(f'{device}: busca autorizada',page.locator('.search-hit').count()>0)
   page.evaluate("location.hash='#/biblioteca'");page.locator('.part-list').wait_for()
   check(f'{device}: biblioteca completa',page.locator('.chapter-row').count()==67)
   page.screenshot(path=str(root/'tests'/f'library_{device}.png'))
   check(f'{device}: sem exceções JavaScript',not errs)
   if errs:print('errors',errs)
  except Exception as exc:
   check(f'{device}: execução de ponta a ponta',False)
   print('Browser error',str(exc)[:600],errs)
  page.close()
 browser.close()
(root/'tests/sandbox_browser_results.json').write_text(json.dumps({'limitations':'Runs actual UI JS with in-memory data and storage; network navigation disabled by administrator','tests':[{'name':n,'status':'PASS' if b else 'FAIL'} for n,b in results]},ensure_ascii=False,indent=2))
print('Passed',sum(x[1] for x in results),'/',len(results))
