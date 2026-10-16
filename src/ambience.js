// Sons de fundo do Arquivo Vivo: mar, chuva, vento e Amazing Grace.
// Somente iniciado após interação direta; sem endpoints remotos.
const panel=document.getElementById('ambient-panel');
const toggle=document.getElementById('ambience-toggle');
const playButton=document.getElementById('ambient-play');
const close=document.getElementById('ambient-close');
const volumeInput=document.getElementById('ambient-volume');
const volumeLabel=document.getElementById('ambient-volume-label');
const NAMES=new Set(['mar','chuva','vento','graca']);
let state={sound:'mar',volume:35};let opener=toggle;
try {const saved=JSON.parse(localStorage.getItem('cn-ambience-v2')||'{}');if(NAMES.has(saved.sound))state.sound=saved.sound;if(Number.isFinite(saved.volume))state.volume=Math.max(0,Math.min(100,saved.volume));}catch{}
const player=new Audio();player.loop=true;player.preload='none';player.volume=state.volume/100;
player.addEventListener('error',()=>{playButton.textContent='Áudio indisponível';playButton.disabled=true;});
const persist=()=>{try{localStorage.setItem('cn-ambience-v2',JSON.stringify(state));}catch{}};
function announce(){document.dispatchEvent(new CustomEvent('arquivo:ambience-state',{detail:{playing:!player.paused,sound:state.sound}}))}
function render(){announce();volumeInput.value=state.volume;volumeLabel.textContent=state.volume+'%';playButton.textContent=player.paused?'▶ Reproduzir':'Ⅱ Pausar';playButton.setAttribute('aria-label',player.paused?'Reproduzir som ambiente':'Pausar som ambiente');document.querySelectorAll('.sound-toggle,.reader-sound').forEach(b=>b.classList.toggle('audio-playing',!player.paused));panel.querySelectorAll('[data-sound]').forEach(btn=>{const active=btn.dataset.sound===state.sound;btn.setAttribute('aria-pressed',String(active));btn.querySelector('.sound-indicator').textContent=active?'●':'○';});}
function chooseSource(){const path='/assets/audio/'+state.sound+'.ogg';if(!player.src.endsWith(path)){player.src=path;player.load();}}
async function play(){chooseSource();try{await player.play();}catch(e){console.warn('Áudio não autorizado pelo navegador',e);playButton.textContent='Toque para tentar novamente';}render();}
function pause(){player.pause();render();}
function setExpanded(v){document.querySelectorAll('.sound-toggle,.reader-sound').forEach(b=>b.setAttribute('aria-expanded',String(v)));}
function show(from){opener=from||toggle;panel.hidden=false;setExpanded(true);render();panel.querySelector('[aria-pressed="true"]')?.focus({preventScroll:true});}
function hide(){panel.hidden=true;setExpanded(false);if(opener?.isConnected)opener.focus({preventScroll:true});}
toggle.addEventListener('click',()=>panel.hidden?show(toggle):hide());
document.addEventListener('arquivo:toggle-ambience-panel',e=>panel.hidden?show(e.detail?.opener):hide());
document.addEventListener('click',e=>{if(!panel.hidden&&!panel.contains(e.target)&&!e.target.closest('.sound-toggle,.reader-sound'))hide();});
window.addEventListener('hashchange',()=>{if(!panel.hidden){panel.hidden=true;setExpanded(false);}});close.addEventListener('click',hide);
playButton.addEventListener('click',()=>player.paused?play():pause());
volumeInput.addEventListener('input',()=>{state.volume=Number(volumeInput.value);player.volume=state.volume/100;persist();render();});
panel.querySelectorAll('[data-sound]').forEach(btn=>btn.addEventListener('click',()=>{const wasPlaying=!player.paused;state.sound=btn.dataset.sound;persist();player.pause();chooseSource();render();if(wasPlaying)play();}));
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!panel.hidden)hide();});
window.addEventListener('pagehide',()=>player.pause());
document.addEventListener('arquivo:pause-ambience', pause);
// Cenas podem sugerir uma atmosfera; o som continua começando só por um gesto do leitor.
document.addEventListener('arquivo:play-ambience', e=>{const next=e.detail?.sound;if(NAMES.has(next)&&next!==state.sound){state.sound=next;persist();player.pause();}if(player.paused)play();else pause();});
render();
