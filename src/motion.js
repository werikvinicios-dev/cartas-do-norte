/* Linguagem de movimento do Arquivo Vivo.
   - Atos guiados pela rolagem nativa: seções [data-scrub] recebem --p (0→1) e data-step, sem sequestrar o scroll.
   - Revelações [data-reveal] quando entram na tela.
   - Barra superior que se recolhe ao descer e volta ao subir.
   - Menu em tela cheia (rosa dos ventos) com prévia de imagem.
   Tudo é aprimoramento: com movimento reduzido, o conteúdo aparece completo e estático. */
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches || document.body.classList.contains('reduce-motion');
const main = document.getElementById('main');
const topbar = document.getElementById('topbar');
const menu = document.getElementById('menu');
let scrubs = [], revealIO = null, raf = 0, lastY = scrollY;

function measure() {
  for (const s of scrubs) {
    const r = s.el.getBoundingClientRect(), span = Math.max(1, r.height - innerHeight);
    const p = Math.min(1, Math.max(0, -r.top / span));
    if (Math.abs(p - s.p) < 0.0005 && r.bottom > 0 && r.top < innerHeight) continue;
    s.p = p; s.el.style.setProperty('--p', p.toFixed(4));
    let step = 0; for (const t of s.steps) if (p >= t) step++;
    if (step !== s.step) { s.step = step; s.el.dataset.step = step; }
    s.el.classList.toggle('is-active', r.top <= 0 && r.bottom >= innerHeight);
  }
}
function onScroll() {
  if (!raf) raf = requestAnimationFrame(() => {
    raf = 0; measure();
    const y = scrollY, down = y > lastY + 4, up = y < lastY - 4;
    if (!menu.hidden) topbar.classList.remove('is-tucked');
    else if (down && y > 160) topbar.classList.add('is-tucked');
    else if (up || y < 80) topbar.classList.remove('is-tucked');
    topbar.classList.toggle('is-solid', y > 40 || !document.querySelector('.atrio'));
    lastY = y;
  });
}
function setup() {
  scrubs = [...main.querySelectorAll('[data-scrub]')].map(el => ({ el, p: -1, step: -1, steps: (el.dataset.steps || '').split(',').filter(Boolean).map(Number) }));
  document.documentElement.classList.toggle('can-animate', !reduced());
  revealIO?.disconnect();
  const items = main.querySelectorAll('[data-reveal]');
  if (reduced() || !('IntersectionObserver' in window)) items.forEach(x => x.classList.add('is-in'));
  else {
    revealIO = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('is-in'); revealIO.unobserve(e.target); } }), { rootMargin: '0px 0px -8% 0px', threshold: .12 });
    items.forEach(x => revealIO.observe(x));
  }
  if (reduced()) scrubs.forEach(s => { s.el.style.setProperty('--p', 1); s.el.dataset.step = s.steps.length; });
  measure(); onScroll();
}
new MutationObserver(() => requestAnimationFrame(setup)).observe(main, { childList: true });
addEventListener('scroll', onScroll, { passive: true });
addEventListener('resize', () => { scrubs.forEach(s => s.p = -1); onScroll(); });
matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', setup);

// ── Menu ─────────────────────────────────────────────────────────────────
const preview = document.getElementById('menu-preview');
let opener = null;
function openMenu(btn) {
  opener = btn || document.activeElement;
  menu.hidden = false; document.body.classList.add('menu-open');
  requestAnimationFrame(() => menu.classList.add('is-open'));
  document.querySelectorAll('[data-menu-toggle]').forEach(b => b.setAttribute('aria-expanded', 'true'));
  (menu.querySelector('[aria-current="page"]') || menu.querySelector('a'))?.focus();
}
function closeMenu(restore = true) {
  if (menu.hidden) return;
  menu.classList.remove('is-open'); document.body.classList.remove('menu-open');
  document.querySelectorAll('[data-menu-toggle]').forEach(b => b.setAttribute('aria-expanded', 'false'));
  setTimeout(() => { if (!menu.classList.contains('is-open')) menu.hidden = true; }, reduced() ? 0 : 420);
  if (restore) opener?.focus?.();
}
document.addEventListener('click', e => {
  const t = e.target.closest('[data-menu-toggle]');
  if (t) { e.preventDefault(); menu.hidden ? openMenu(t) : closeMenu(); return; }
  if (!menu.hidden && e.target.closest('#menu a, #menu [data-action]')) closeMenu(false);
});
function showPreview(el) {
  const src = el?.dataset.preview; if (!src || preview.getAttribute('src') === src) return;
  preview.classList.remove('is-in'); preview.src = src; preview.decode?.().then(() => preview.classList.add('is-in')).catch(() => preview.classList.add('is-in'));
}
menu.addEventListener('pointerover', e => showPreview(e.target.closest('[data-preview]')));
menu.addEventListener('focusin', e => showPreview(e.target.closest('[data-preview]')));
document.addEventListener('keydown', e => {
  if (menu.hidden) return;
  if (e.key === 'Escape') { closeMenu(); return; }
  if (e.key !== 'Tab') return;
  const f = [...menu.querySelectorAll('a,button'), document.getElementById('menu-toggle')].filter(x => x.getClientRects().length);
  const i = f.indexOf(document.activeElement);
  if (e.shiftKey && i <= 0) { e.preventDefault(); f.at(-1).focus(); }
  else if (!e.shiftKey && i === f.length - 1) { e.preventDefault(); f[0].focus(); }
});
addEventListener('hashchange', () => closeMenu(false));
preview.classList.add('is-in');
setup();
