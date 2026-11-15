// Small helpers the scenes are built from. Everything is placed on a 1920x1080 stage.
const SVGNS = 'http://www.w3.org/2000/svg';
const D = window.DATA;

function div(parent, cls, style, html) {
  const e = document.createElement('div');
  if (cls) e.className = cls;
  if (style) e.style.cssText = style;
  if (html != null) e.innerHTML = html;
  parent.appendChild(e);
  return e;
}

function svgEl(tag, attrs, parent) {
  const e = document.createElementNS(SVGNS, tag);
  for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}

const polyPath = pts => 'M' + pts.map(p => p[0] + ' ' + p[1]).join('L') + 'Z';

// The plan drawing in a box, cropped to `view` = [x0,y0,x1,y1] in drawing pixels.
function planView(parent, { x, y, w, h, view, image = true, bg = '#FBFAF6' }) {
  const box = div(parent, 'plan-box', `left:${x}px;top:${y}px;width:${w}px;height:${h}px;background:${bg};`);
  const [x0, y0, x1, y1] = view || padBox(D.bbox, 60);
  const svg = svgEl('svg', { class: 'plan-svg', width: w, height: h, viewBox: `${x0} ${y0} ${x1 - x0} ${y1 - y0}`, preserveAspectRatio: 'xMidYMid meet' }, box);
  if (image) svgEl('image', { href: 'media/plan.jpg', x: 0, y: 0, width: D.size[0], height: D.size[1] }, svg);
  const layers = {};
  const g = name => layers[name] || (layers[name] = svgEl('g', { class: 'L-' + name }, svg));
  return { box, svg, g };
}

function padBox(b, p) { return [b[0] - p, b[1] - p, b[2] + p, b[3] + p]; }

// Draw schematic parts. Each returns the created elements so scenes can animate them.
function drawRooms(g, rooms, color, { fill = 0.22, width = 5 } = {}) {
  return rooms.map(r => svgEl('path', { d: polyPath(r.polygon), fill: color, 'fill-opacity': fill, stroke: color, 'stroke-width': width, 'stroke-linejoin': 'round' }, g));
}
function drawWalls(g, walls, color, { opacity = 0.85 } = {}) {
  return walls.map(w => Array.isArray(w)
    ? svgEl('path', { d: polyPath(w), fill: color, 'fill-opacity': opacity }, g)
    : svgEl('line', { x1: w.p1[0], y1: w.p1[1], x2: w.p2[0], y2: w.p2[1], stroke: color, 'stroke-width': w.t || 10, 'stroke-opacity': opacity }, g));
}
function drawSegs(g, segs, color, width = 9) {
  return segs.map(s => svgEl('line', { x1: s.p1[0], y1: s.p1[1], x2: s.p2[0], y2: s.p2[1], stroke: color, 'stroke-width': width, 'stroke-linecap': 'round' }, g));
}
function drawFixtures(g, fx, color) {
  return fx.map(f => svgEl('circle', { cx: f.x, cy: f.y, r: 16, fill: 'none', stroke: color, 'stroke-width': 6 }, g));
}

// ---------- tween helpers (all deterministic, so the timeline can be scrubbed) ----------

// Stroke-draw paths in, then fade their fill up.
function drawIn(tl, els, at, { dur = 0.8, stagger = 0.08, fill = null } = {}) {
  els.forEach(e => {
    const len = e.getTotalLength ? Math.max(1, e.getTotalLength()) : 1000;
    e.style.strokeDasharray = len;
    e._len = len;
  });
  tl.fromTo(els, { strokeDashoffset: i => els[i]._len, fillOpacity: 0, opacity: 1 },
    { strokeDashoffset: 0, fillOpacity: fill == null ? (i => els[i].getAttribute('fill-opacity') || 0) : fill, duration: dur, stagger, ease: 'power2.out' }, at);
}

function popIn(tl, els, at, { dur = 0.45, stagger = 0.06, y = 30, scale = 0.9 } = {}) {
  tl.fromTo(els, { opacity: 0, y, scale }, { opacity: 1, y: 0, scale: 1, duration: dur, stagger, ease: 'back.out(1.6)' }, at);
}
function fadeIn(tl, els, at, dur = 0.5) { tl.fromTo(els, { opacity: 0 }, { opacity: 1, duration: dur, ease: 'power1.out' }, at); }
function fadeOut(tl, els, at, dur = 0.4) { tl.to(els, { opacity: 0, duration: dur, ease: 'power1.in' }, at); }

// Slam a headline in word by word.
function slam(tl, el, at, { stagger = 0.12 } = {}) {
  // wrap every word of every text node in a span, keeping nested markup intact
  const wrap = node => {
    [...node.childNodes].forEach(n => {
      if (n.nodeType === 3) {
        const frag = document.createDocumentFragment();
        n.textContent.split(/(\s+)/).forEach(w => {
          if (!w) return;
          if (/^\s+$/.test(w)) { frag.appendChild(document.createTextNode(w)); return; }
          const s = document.createElement('span'); s.className = 'slam'; s.textContent = w; frag.appendChild(s);
        });
        n.replaceWith(frag);
      } else if (n.nodeType === 1 && n.tagName !== 'BR') wrap(n);
    });
  };
  wrap(el);
  const spans = el.querySelectorAll('.slam');
  tl.fromTo(spans, { opacity: 0, y: 60, scale: 1.25, filter: 'blur(8px)' },
    { opacity: 1, y: 0, scale: 1, filter: 'blur(0px)', duration: 0.5, stagger, ease: 'expo.out' }, at);
  return spans;
}

function countUp(tl, el, to, at, { dur = 1.2, decimals = 2, from = 0, prefix = '', suffix = '' } = {}) {
  const o = { v: from };
  el.textContent = prefix + from.toFixed(decimals) + suffix;
  tl.fromTo(o, { v: from }, { v: to, duration: dur, ease: 'power2.out', onUpdate: () => { el.textContent = prefix + o.v.toFixed(decimals) + suffix; } }, at);
}

function typeText(tl, el, text, at, { cps = 45 } = {}) {
  const o = { n: 0 };
  el.textContent = '';
  tl.fromTo(o, { n: 0 }, { n: text.length, duration: text.length / cps, ease: 'none', onUpdate: () => { el.textContent = text.slice(0, Math.round(o.n)); } }, at);
}

// Fade a whole scene in at its start and out at its end.
function sceneFades(tl, root, dur, { inn = 0.4, out = 0.4 } = {}) {
  if (inn) tl.fromTo(root, { opacity: 0 }, { opacity: 1, duration: inn }, 0);
  if (out) tl.to(root, { opacity: 0, duration: out }, dur - out);
  tl.set({}, {}, dur); // make the timeline exactly `dur` long
}

// Reveal an element left to right with a clip-path wipe (no per-word animation).
function wipe(tl, el, at, dur = 0.8) {
  tl.fromTo(el, { clipPath: 'inset(-10% 100% -10% 0)', x: -30 }, { clipPath: 'inset(-10% 0% -10% 0)', x: 0, duration: dur, ease: 'power3.out', immediateRender: true }, at);
}
