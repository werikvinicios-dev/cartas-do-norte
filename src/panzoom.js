/* Visualizador com zoom e deslocamento para fac-símiles e mapas.
   Gesto de pinça, arrasto, roda do mouse, duplo clique e teclado (+, −, 0, setas).
   A camada recebe --pz-s para que marcadores mantenham tamanho constante. */
export function panZoom(frame, { max = 5, wheel = 'always', onChange } = {}) {
  const layer = frame.querySelector('.pz-layer');
  const img = layer.querySelector('img');
  let fw = 0, fh = 0, w = 0, h = 0, s = 1, x = 0, y = 0;
  const pts = new Map();
  let pinch = null, pan = null, moved = false;

  function fit() {
    fw = frame.clientWidth; fh = frame.clientHeight;
    const iw = img.naturalWidth || 1, ih = img.naturalHeight || 1;
    const k = Math.min(fw / iw, fh / ih);
    w = iw * k; h = ih * k;
    layer.style.width = w + 'px'; layer.style.height = h + 'px';
    set(s, x, y);
  }
  function set(ns, nx, ny) {
    s = Math.min(max, Math.max(1, ns));
    x = w * s <= fw ? (fw - w * s) / 2 : Math.min(0, Math.max(fw - w * s, nx));
    y = h * s <= fh ? (fh - h * s) / 2 : Math.min(0, Math.max(fh - h * s, ny));
    layer.style.transform = `translate3d(${x}px,${y}px,0) scale(${s})`;
    layer.style.setProperty('--pz-s', s);
    frame.classList.toggle('is-zoomed', s > 1.01);
    onChange?.(s);
  }
  function zoomAt(f, cx = fw / 2, cy = fh / 2) {
    const ns = Math.min(max, Math.max(1, s * f));
    const r = ns / s;
    set(ns, cx - (cx - x) * r, cy - (cy - y) * r);
  }
  function animate(fn) {
    layer.classList.add('pz-anim'); fn();
    clearTimeout(animate.t); animate.t = setTimeout(() => layer.classList.remove('pz-anim'), 650);
  }
  const local = e => { const r = frame.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };

  function down(e) {
    if (e.target.closest('button,a')) return;
    pts.set(e.pointerId, local(e)); frame.setPointerCapture?.(e.pointerId); moved = false;
    if (pts.size === 2) {
      const [a, b] = [...pts.values()];
      pinch = { d: Math.hypot(a[0] - b[0], a[1] - b[1]), s, x, y, cx: (a[0] + b[0]) / 2, cy: (a[1] + b[1]) / 2 };
      pan = null;
    } else pan = { p: local(e), x, y };
  }
  function move(e) {
    if (!pts.has(e.pointerId)) return;
    pts.set(e.pointerId, local(e));
    if (pinch && pts.size === 2) {
      const [a, b] = [...pts.values()];
      const ns = Math.min(max, Math.max(1, pinch.s * Math.hypot(a[0] - b[0], a[1] - b[1]) / pinch.d));
      const r = ns / pinch.s, cx = (a[0] + b[0]) / 2, cy = (a[1] + b[1]) / 2;
      set(ns, cx - (pinch.cx - pinch.x) * r, cy - (pinch.cy - pinch.y) * r); moved = true;
    } else if (pan && s > 1) {
      const p = local(e);
      if (Math.abs(p[0] - pan.p[0]) + Math.abs(p[1] - pan.p[1]) > 3) moved = true;
      set(s, pan.x + p[0] - pan.p[0], pan.y + p[1] - pan.p[1]);
    }
  }
  function up(e) { pts.delete(e.pointerId); if (pts.size < 2) pinch = null; if (!pts.size) pan = null; }
  function wheelFn(e) {
    if (wheel === 'ctrl' && !(e.ctrlKey || e.metaKey)) return;
    e.preventDefault();
    const [cx, cy] = local(e); zoomAt(Math.exp(-e.deltaY * 0.0022), cx, cy);
  }
  function dbl(e) { const [cx, cy] = local(e); animate(() => s > 1.5 ? set(1, 0, 0) : zoomAt(2.4, cx, cy)); }
  function key(e) {
    const step = 60;
    const map = { '+': () => zoomAt(1.4), '=': () => zoomAt(1.4), '-': () => zoomAt(1 / 1.4), '0': () => set(1, 0, 0),
      ArrowLeft: () => set(s, x + step, y), ArrowRight: () => set(s, x - step, y), ArrowUp: () => set(s, x, y + step), ArrowDown: () => set(s, x, y - step) };
    if (map[e.key] && (s > 1 || !e.key.startsWith('Arrow'))) { e.preventDefault(); animate(map[e.key]); }
  }
  frame.addEventListener('pointerdown', down);
  frame.addEventListener('pointermove', move);
  frame.addEventListener('pointerup', up);
  frame.addEventListener('pointercancel', up);
  frame.addEventListener('wheel', wheelFn, { passive: false });
  frame.addEventListener('dblclick', dbl);
  frame.addEventListener('keydown', key);
  frame.addEventListener('click', e => { if (moved) { e.stopPropagation(); e.preventDefault(); moved = false; } }, true);
  const ro = new ResizeObserver(fit); ro.observe(frame);
  if (img.complete) fit(); else img.addEventListener('load', fit, { once: true });

  return {
    zoomBy: f => animate(() => zoomAt(f)),
    reset: () => animate(() => set(1, 0, 0)),
    // Centraliza um ponto da imagem (porcentagens) com a escala pedida.
    focus: (pxp, pyp, ns = 2.6) => animate(() => { const t = Math.min(max, ns); set(t, fw / 2 - (pxp / 100) * w * t, fh / 2 - (pyp / 100) * h * t); }),
    get scale() { return s; },
    destroy: () => ro.disconnect(),
  };
}
