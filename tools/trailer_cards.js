const {chromium}=require('playwright');
// Uso: node tools/trailer_cards.js <pasta> (com o site servido em localhost:8765)
const out=process.argv[2];
const cards={
 c1:['center','<p class="q">A primeira luz era a que todos esperavam.</p>'],
 c2:['center','<p class="q">Três pulsações sobre o mar.</p>'],
 c3:['right','<p class="q s">Choveu no funeral de Jonas Vale, embora o céu tivesse passado a manhã inteira prometendo que não choveria.</p><p class="src">CAPÍTULO 1</p>'],
 c4:['left','<p class="q s">A casa do farol tinha aprendido a envelhecer sem testemunhas.</p><p class="src">CAPÍTULO 3</p>'],
 c5:['center','<p class="k">ENTRE CARTAS, FARÓIS E TRAVESSIAS</p>'],
 c6:['center','<p class="q">Um romance para ler.</p>'],
 c7:['center','<p class="q">Um mundo para explorar.</p>'],
 c8:['center','<p class="q">Um arquivo para descobrir.</p>'],
 end:['center','<img src="http://localhost:8765/assets/branding/wordmark.svg"><p class="k">O ARQUIVO VIVO</p><p class="src">UMA OBRA DE WERIK MARTINS</p>'],
};
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
for(const [k,[align,html]] of Object.entries(cards)){
 await p.setContent(`<html><head><style>
 @font-face{font-family:C;src:url(http://localhost:8765/assets/fonts/cormorant-400-italic.woff2);font-style:italic}
 @font-face{font-family:C;src:url(http://localhost:8765/assets/fonts/cormorant-500.woff2)}
 html,body{margin:0;background:transparent;width:1920px;height:1080px}
 body{display:flex;flex-direction:column;justify-content:center;align-items:${align==='center'?'center':align==='right'?'flex-end':'flex-start'};text-align:${align};padding:0 150px;box-sizing:border-box;color:#f4ead6}
 .q{font:italic 400 76px/1.15 C;margin:0;max-width:1300px;text-shadow:0 4px 30px #000c}
 .q.s{font-size:60px;max-width:820px}
 .k{font:500 30px C;letter-spacing:.42em;color:#e6cc9b;margin:24px 0 0;text-shadow:0 2px 20px #000}
 .src{font:500 22px C;letter-spacing:.38em;color:#cdaa72;margin:28px 0 0}
 img{width:1100px;filter:drop-shadow(0 10px 30px #000)}
 </style></head><body>${html}</body></html>`);
 await p.waitForTimeout(400);await p.screenshot({path:`${out}/${k}.png`,omitBackground:true});
}
await b.close()})();
