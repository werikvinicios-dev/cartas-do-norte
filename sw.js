/* Arquivo Vivo 0.5 — shell offline e cache de recursos canônicos e mídias opcionais. */
const VERSION='av-shell-0.6.0';
const OFFLINE='arquivo-vivo-offline-v1';
const BASE=['/','/index.html','/src/main.js','/src/db.js','/src/content.js','/src/ambience.js','/src/motion.js','/src/scene.js','/src/panzoom.js','/src/ui.css','/content/places.json','/content/people.json','/content/plates.json','/assets/experience/letter-paper.webp','/assets/fonts/newsreader.woff2','/assets/fonts/newsreader-italic.woff2','/assets/fonts/cormorant-400.woff2','/assets/fonts/cormorant-400-italic.woff2','/assets/fonts/cormorant-500.woff2','/assets/fonts/cormorant-600.woff2','/assets/experience/mist.webp','/assets/fonts/cartas-display.woff2','/assets/branding/emblem-gold.webp','/assets/branding/emblem-navy.webp','/content/migration-v4.json','/manifest.webmanifest','/content/catalog.json','/assets/branding/cover.webp','/assets/branding/icon-192.png','/assets/branding/wordmark.svg','/assets/branding/compass.webp','/assets/branding/cartographic-frontispiece.webp','/assets/branding/grain.png','/assets/experience/archive-frontispiece.webp','/assets/experience/edition-paper.webp'];
self.addEventListener('install',event=>event.waitUntil(caches.open(VERSION).then(cache=>cache.addAll(BASE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
 for(const key of await caches.keys())if(key.startsWith('av-shell-')&&key!==VERSION)await caches.delete(key);
 await self.clients.claim();
})()));
function isResource(url){return url.pathname.startsWith('/content/reading/')||url.pathname.startsWith('/assets/');}
async function partResponse(res,range){
 const m=/^bytes=(\d+)-(\d*)$/.exec(range||'');if(!m)return new Response('Intervalo inválido',{status:416});
 const bytes=await res.arrayBuffer(),len=bytes.byteLength,start=Number(m[1]),end=m[2]?Math.min(Number(m[2]),len-1):len-1;
 if(start>=len||end<start)return new Response('Intervalo inválido',{status:416,headers:{'Content-Range':`bytes */${len}`}});
 return new Response(bytes.slice(start,end+1),{status:206,headers:{'Content-Type':res.headers.get('Content-Type')||'application/octet-stream','Content-Range':`bytes ${start}-${end}/${len}`,'Accept-Ranges':'bytes','Content-Length':String(end-start+1)}});
}
self.addEventListener('fetch',event=>{
 const req=event.request,url=new URL(req.url);
 if(req.method!=='GET'||url.origin!==self.location.origin)return;
 if(isResource(url)){
  event.respondWith((async()=>{
   const local=await caches.open(OFFLINE),shell=await caches.open(VERSION);
   const cached=await local.match(req.url)||await shell.match(req.url);
   const range=req.headers.get('range');
   if(cached)return range?partResponse(cached,range):cached;
   try{const res=await fetch(req);if(res.status===200&&!range)await local.put(req.url,res.clone());return res;}
   catch{return new Response('Este recurso não foi baixado para leitura offline.',{status:503,headers:{'Content-Type':'text/plain;charset=utf-8'}})}
  })());return;
 }
 event.respondWith((async()=>{
  try{const res=await fetch(req);if(res.ok&&url.pathname.endsWith('.json'))(await caches.open(VERSION)).put(req,res.clone());return res;}
  catch{return await caches.match(req)||((url.pathname==='/'||url.pathname.endsWith('/index.html'))?await caches.match('/index.html'):null)||new Response('Indisponível offline',{status:503});}
 })());
});
