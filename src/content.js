let catalogPromise;
const sections=new Map();
export async function catalog(){
 if(!catalogPromise)catalogPromise=fetch('/content/catalog.json').then(r=>{if(!r.ok)throw Error('O catálogo não pôde ser carregado.');return r.json()});
 return catalogPromise;
}
export async function section(id){
 if(!/^(ch\d{1,2}|letter\d{1,2}|prologue|epilogue)$/.test(id))throw Error('Identificador inválido.');
 if(!sections.has(id))sections.set(id,fetch(`/content/reading/${id}.json`).then(r=>{if(!r.ok)throw Error('Conteúdo indisponível.');return r.json()}));
 return sections.get(id);
}
export function normalize(s){return String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()}
