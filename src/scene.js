/* Cena Viva — uma pintura aprovada tratada como plano de câmera.
   Camadas: pintura (câmera), luzes pintadas reforçadas, névoa em duas profundidades, vinheta.
   Tudo o que anima é transform/opacity; a cena pausa fora da tela, com a aba oculta e com movimento reduzido.
   Os pontos interativos são links reais: funcionam sem JavaScript e pelo teclado. */
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches || document.body.classList.contains('reduce-motion');
let introPlayed = false;

export function mountScene(root, { aspect = 1.5, focus = [0.6, 0.5], intro = false, zoom = 1 } = {}) {
  const viewport = root.querySelector('.scene-viewport');
  const cam = root.querySelector('.scene-cam');
  const plate = root.querySelector('.scene-plate');
  if (!viewport || !cam || !plate) return () => {};
  let W = 0, H = 0, PW = 0, PH = 0, baseX = 0, baseY = 0, dragX = 0, minX = 0, maxX = 0;
  let px = 0, py = 0, tx = 0, ty = 0, raf = 0, visible = true, intro0 = null;

  function layout() {
    W = viewport.clientWidth; H = viewport.clientHeight;
    PW = Math.max(W, H / aspect) * 1.06 * zoom; PH = PW * aspect;
    plate.style.width = PW + 'px'; plate.style.height = PH + 'px';
    minX = W - PW; maxX = 0;
    baseX = clamp(W / 2 - PW * focus[0], minX, maxX);
    baseY = clamp(H / 2 - PH * focus[1], H - PH, 0);
    dragX = clamp(dragX, minX - baseX, maxX - baseX);
    paint();
  }
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  function paint() {
    let y = baseY;
    if (intro0 !== null) {
      const t = Math.min(1, (performance.now() - intro0) / 3600);
      const e = 1 - Math.pow(1 - t, 3);
      y = (1 - e) * clamp(H * 0.08, H - PH, 0) + e * baseY;
      if (t >= 1) intro0 = null;
    }
    const x = clamp(baseX + dragX + px * 14, minX, maxX);
    cam.style.transform = `translate3d(${x.toFixed(1)}px,${(y + py * 10).toFixed(1)}px,0)`;
    root.style.setProperty('--mx', (-px * 26).toFixed(1) + 'px');
    root.style.setProperty('--my', (-py * 12).toFixed(1) + 'px');
  }
  function loop() {
    raf = 0;
    px += (tx - px) * 0.08; py += (ty - py) * 0.08;
    paint();
    if (visible && (intro0 !== null || Math.abs(tx - px) > 0.002 || Math.abs(ty - py) > 0.002)) raf = requestAnimationFrame(loop);
  }
  const kick = () => { if (!raf && visible) raf = requestAnimationFrame(loop); };

  function onMove(e) {
    if (e.pointerType !== 'mouse' || reduced()) return;
    const r = viewport.getBoundingClientRect();
    tx = ((e.clientX - r.left) / r.width - 0.5) * 2; ty = ((e.clientY - r.top) / r.height - 0.5) * 2; kick();
  }
  function onLeave() { tx = 0; ty = 0; kick(); }
  // Arrasto horizontal no toque: explora a largura da pintura sem impedir a rolagem vertical.
  let drag = null;
  function onDown(e) { if (e.pointerType === 'mouse' || e.target.closest('a,button')) return; drag = { x: e.clientX, y: e.clientY, d: dragX, active: false }; }
  function onDrag(e) {
    if (!drag) return;
    const dx = e.clientX - drag.x;
    if (!drag.active && Math.abs(dx) > 8 && Math.abs(dx) > Math.abs(e.clientY - drag.y)) drag.active = true;
    if (drag.active) { dragX = clamp(drag.d + dx, minX - baseX, maxX - baseX); paint(); }
  }
  function onUp() { drag = null; }

  // Mergulho de câmera no ponto escolhido antes de seguir o link.
  function onClick(e) {
    const spot = e.target.closest('.hotspot');
    if (!spot || spot.dataset.action || e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || reduced()) return;
    e.preventDefault(); e.stopPropagation();
    const r = spot.getBoundingClientRect(), v = viewport.getBoundingClientRect();
    root.classList.add('is-diving');
    root.style.setProperty('--dive-x', (r.left + r.width / 2 - v.left) + 'px');
    root.style.setProperty('--dive-y', (r.top + r.height / 2 - v.top) + 'px');
    setTimeout(() => { location.hash = spot.getAttribute('href'); }, 520);
  }

  const io = new IntersectionObserver(([en]) => {
    visible = en.isIntersecting; root.classList.toggle('is-paused', !visible); if (visible) kick();
  }, { threshold: 0.02 });
  io.observe(root);
  const onVis = () => root.classList.toggle('is-hidden-tab', document.hidden);
  const ro = new ResizeObserver(layout);
  ro.observe(viewport);
  viewport.addEventListener('pointermove', onMove);
  viewport.addEventListener('pointerleave', onLeave);
  viewport.addEventListener('pointerdown', onDown);
  window.addEventListener('pointermove', onDrag, { passive: true });
  window.addEventListener('pointerup', onUp);
  window.addEventListener('pointercancel', onUp);
  root.addEventListener('click', onClick);
  document.addEventListener('visibilitychange', onVis);
  layout();
  if (intro && !introPlayed && !reduced()) { intro0 = performance.now(); kick(); }
  introPlayed = true;
  requestAnimationFrame(() => root.classList.add('is-ready'));

  return function destroy() {
    cancelAnimationFrame(raf); io.disconnect(); ro.disconnect();
    window.removeEventListener('pointermove', onDrag); window.removeEventListener('pointerup', onUp);
    window.removeEventListener('pointercancel', onUp); document.removeEventListener('visibilitychange', onVis);
  };
}
