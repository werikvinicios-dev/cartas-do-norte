// Fluxos reais em Chromium (Playwright): Átrio, leitor, Atlas, Acervo com lacre, Cena do Farol, Observatório.
// Uso: python3 -m http.server 8765 & node tests/v4_flows_qa.js <pasta_de_capturas> [desk|mob]
const {chromium}=require('playwright');
const out=process.argv[2], only=process.argv[3]||'';
const progress={current:'ch4',anchor:null,completed:['prologue','ch1','letter1','ch2','ch3'],seen:{ch4:3},positions:{},lastReader:'ch4'};
async function seed(p){await p.evaluate(async pr=>{await new Promise((res,rej)=>{const r=indexedDB.open('cartas-do-norte-arquivo-vivo',1);r.onupgradeneeded=()=>{r.result.createObjectStore('kv');r.result.createObjectStore('marks',{keyPath:'id'})};r.onsuccess=()=>{const tx=r.result.transaction('kv','readwrite');tx.objectStore('kv').put(pr,'progress');tx.oncomplete=()=>{r.result.close();res()}};r.onerror=rej})},progress)}
(async()=>{
 const b=await chromium.launch();
 for(const [name,w,h] of [['desk',1440,900],['mob',390,844]]){
  if(only&&only!==name)continue;
  const ctx=await b.newContext({viewport:{width:w,height:h},hasTouch:name==='mob',isMobile:name==='mob'});
  const p=await ctx.newPage();const errs=new Set();
  p.on('console',m=>{if(m.type()==='error')errs.add(m.text())});p.on('pageerror',e=>errs.add('pageerror: '+e.message));
  const shot=async n=>{await p.screenshot({path:`${out}/${name}-${n}.png`});const ov=await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);if(ov)console.log(name,n,'HSCROLL')};
  await p.goto('http://localhost:8765/#/atrio');await p.waitForTimeout(4200);await shot('atrio');
  await p.goto('http://localhost:8765/#/ler/ch1');await p.waitForTimeout(1500);await shot('ch1');
  await p.goto('http://localhost:8765/#/biblioteca');await p.waitForTimeout(500);await seed(p);await p.goto('http://localhost:8765/#/atlas');await p.reload();await p.waitForTimeout(1500);await shot('atlas');
  await p.click('.place-btn >> text=Farol da Vigília');await p.waitForTimeout(1300);await shot('atlas-place');
  await p.goto('http://localhost:8765/#/acervo');await p.waitForTimeout(800);await p.click('[data-id="testament"]');await p.waitForTimeout(700);await shot('seal');await p.waitForTimeout(1600);await shot('doc');
  if(name==='mob'){await p.click('.viewer-tabs [data-tab="text"]');await p.waitForTimeout(300);await shot('doc-text')}
  await p.keyboard.press('Escape');
  await p.goto('http://localhost:8765/#/cena/farol');await p.waitForTimeout(2500);await shot('farol');
  await p.goto('http://localhost:8765/#/observatorio');await p.waitForTimeout(1000);await shot('obs');
  await p.goto('http://localhost:8765/#/ler/ch4');await p.waitForTimeout(1500);await shot('ch4');
  console.log(name,'errors',[...errs]);await ctx.close();
 }
 await b.close();
})();
