// Renderiza tools/promo/promo.html quadro a quadro e entrega JPEGs ao ffmpeg.
// Uso: node tools/promo/render_promo.js <largura> <altura> <saida.mp4> [fps=30] [duração=30]
//      node tools/promo/render_promo.js <largura> <altura> --frames <dir> <t1,t2,...>   (quadros soltos para revisão)
// Precisa do site servido em http://localhost:8765 (python3 -m http.server 8765 na raiz do repositório).
const {chromium}=require('playwright');const {spawn}=require('child_process');const fs=require('fs');
(async()=>{const [w,h,out,a4,a5]=process.argv.slice(2);const W=+w,H=+h;
 const b=await chromium.launch();const p=await b.newPage({viewport:{width:W,height:H},deviceScaleFactor:1});
 const errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.goto(`http://localhost:8765/tools/promo/promo.html?w=${W}&h=${H}`);await p.evaluate(()=>window.ready);await p.waitForTimeout(300);
 if(out==='--frames'){fs.mkdirSync(a4,{recursive:true});for(const t of a5.split(',').map(Number)){await p.evaluate(t=>render(t),t);await p.screenshot({path:`${a4}/f_${t.toFixed(2)}.jpg`,type:'jpeg',quality:88})}console.log('erros',errs);await b.close();return}
 const fps=+(a4||30),dur=+(a5||30),N=Math.round(fps*dur);
 const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','slow','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',out],{stdio:['pipe','inherit','inherit']});
 for(let i=0;i<N;i++){await p.evaluate(t=>render(t),i/fps);const buf=await p.screenshot({type:'jpeg',quality:93});if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));if(i%150===0)process.stdout.write(`${i}/${N} `)}
 ff.stdin.end();await new Promise(r=>ff.on('close',r));console.log('\nok',out,'erros',errs);await b.close()})();
