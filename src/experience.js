/* Progressive enhancement only: no essential content relies on this file. */
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
let viewObserver=null;
function enhance(){
 document.documentElement.classList.toggle('v3-can-animate',!reduced.matches&&!document.body.classList.contains('reduce-motion'));
 viewObserver?.disconnect();
 if(reduced.matches||document.body.classList.contains('reduce-motion'))return;
 const sections=[...document.querySelectorAll('.v3-reveal')];
 if(!('IntersectionObserver' in window)){sections.forEach(x=>x.classList.add('v3-visible'));return;}
 viewObserver=new IntersectionObserver(entries=>{for(const x of entries)if(x.isIntersecting){x.target.classList.add('v3-visible');viewObserver.unobserve(x.target)}},{rootMargin:'0px 0px 0px 0px',threshold:.08});
 for(const el of sections){if(el.getBoundingClientRect().top<innerHeight*.98)el.classList.add('v3-visible');else viewObserver.observe(el)}
}
const target=document.querySelector('#main');
new MutationObserver(()=>requestAnimationFrame(enhance)).observe(target,{childList:true});
reduced.addEventListener('change',enhance);
window.addEventListener('hashchange',()=>{viewObserver?.disconnect();requestAnimationFrame(enhance)});
requestAnimationFrame(enhance);
