// Cartas: envelope lacrado, abertura, carta dentro de capítulo e Acervo · Correspondência.
// Uso: python3 -m http.server 8765 & node tests/letters_qa.js <pasta_de_capturas>
const {chromium}=require('playwright');const out=process.argv[2];
(async()=>{const b=await chromium.launch();
for(const [n,w,h] of [['d',1440,900],['m',390,844]]){const p=await b.newPage({viewport:{width:w,height:h}});const errs=new Set();p.on('pageerror',e=>errs.add(e.message));p.on('console',m=>{if(m.type()==='error')errs.add(m.text())});
 const sh=k=>p.screenshot({path:`${out}/${n}-L${k}.png`});
 await p.goto('http://localhost:8765/#/ler/letter1');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('.envelope').scrollIntoView({block:'center'}));await p.waitForTimeout(500);await sh(1);
 await p.click('.whole-letter .wax');await p.waitForTimeout(650);await sh(2);await p.waitForTimeout(1900);await sh(3);
 await p.evaluate(()=>document.querySelector('.paper-text .sig')?.scrollIntoView({block:'center'}));await p.waitForTimeout(400);await sh(4);
 await p.goto('http://localhost:8765/#/ler/ch3');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('.inline-letter').scrollIntoView({block:'center'}));await p.waitForTimeout(500);await sh(5);
 await p.click('.inline-letter .wax');await p.waitForTimeout(2600);await p.evaluate(()=>document.querySelector('.inline-letter.is-open').scrollIntoView({block:'start'}));await p.waitForTimeout(400);await sh(6);
 await p.goto('http://localhost:8765/#/acervo');await p.waitForTimeout(1500);await p.evaluate(()=>document.querySelector('.correspondence').scrollIntoView());await p.waitForTimeout(1200);await sh(7);
 await p.click('.corr-card[data-id="letter1"]');await p.waitForTimeout(800);await sh(8);
 console.log(n,'erros',[...errs],'abertas',await p.evaluate(()=>document.querySelectorAll('.corr-card:not(.is-sealed)').length));await p.close()}
await b.close()})();
