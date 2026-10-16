const DB_NAME = 'cartas-do-norte-arquivo-vivo';
const VERSION = 1;
let dbPromise;
export function database(){
 if(!('indexedDB' in window))return Promise.reject(Error('IndexedDB indisponível neste navegador.'));
 if(!dbPromise)dbPromise=new Promise((resolve,reject)=>{
  const req=indexedDB.open(DB_NAME,VERSION);
  req.onupgradeneeded=()=>{
   const db=req.result;
   if(!db.objectStoreNames.contains('kv'))db.createObjectStore('kv');
   if(!db.objectStoreNames.contains('marks'))db.createObjectStore('marks',{keyPath:'id'});
  };
  req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(req.error);
 });
 return dbPromise;
}
export async function get(key,store='kv'){
 const db=await database();return new Promise((resolve,reject)=>{
  const request=db.transaction(store,'readonly').objectStore(store).get(key);
  request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);
 });
}
export async function put(key,value,store='kv'){
 const db=await database();return new Promise((resolve,reject)=>{
  const target=db.transaction(store,'readwrite').objectStore(store);
  const req=store==='kv'?target.put(value,key):target.put({...value,id:key});
  req.onsuccess=()=>resolve();req.onerror=()=>reject(req.error);
 });
}
export async function remove(key,store='kv'){
 const db=await database();return new Promise((resolve,reject)=>{
  const req=db.transaction(store,'readwrite').objectStore(store).delete(key);
  req.onsuccess=()=>resolve();req.onerror=()=>reject(req.error);
 });
}
export async function all(store='marks'){
 const db=await database();return new Promise((resolve,reject)=>{
  const req=db.transaction(store,'readonly').objectStore(store).getAll();
  req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);
 });
}
export async function reset(){
 const db=await database();return new Promise((resolve,reject)=>{
  const tx=db.transaction(['kv','marks'],'readwrite');tx.objectStore('kv').clear();tx.objectStore('marks').clear();
  tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error);
 });
}
