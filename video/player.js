// The player: one clock, scrubbable GSAP timelines per scene, and media kept in sync with the clock.
(() => {
  const stage = document.getElementById('stage');
  const viewport = document.getElementById('viewport');
  const subs = document.getElementById('subs');
  const scrub = document.getElementById('scrub');
  const head = document.getElementById('head');
  const list = document.getElementById('list');
  const prompter = document.getElementById('prompter');
  const playBtn = document.getElementById('play');
  const timeEl = document.getElementById('time');

  let t = 0, playing = false, last = 0, total = 0, cur = -1;
  const media = []; // {el, start, end, offset, ok, scene}

  const fmt = s => `${Math.floor(s / 60)}:${(s % 60).toFixed(1).padStart(4, '0')}`;

  // ---------- build the scenes ----------
  SCENES.forEach((s, i) => {
    s.start = total; total += s.dur; s.end = total;
    s.layer = div(stage, 'layer ' + (s.theme || 'dark'));
    s.layer.style.zIndex = 1;
    if (s.clip) {
      const ph = div(s.layer, 'ph', '', `<div class="tag">FILM THIS · ${s.dur}s</div><div class="shot">${s.shot || ''}</div><div class="file">drop it in: video/media/${s.clip}</div>`);
      const v = document.createElement('video');
      v.src = 'media/' + s.clip; v.preload = 'auto'; v.playsInline = true; v.muted = !s.clipAudio;
      v.style.visibility = 'hidden';
      s.layer.appendChild(v);
      const m = { el: v, start: s.start, end: s.end, offset: s.clipFrom || 0, ok: false, scene: s, kind: 'clip' };
      v.addEventListener('loadeddata', () => { m.ok = true; v.style.visibility = 'visible'; ph.style.display = 'none'; renderList(); render(); });
      v.addEventListener('error', () => { m.ok = false; renderList(); });
      media.push(m);
    }
    s.root = div(s.layer, '', 'position:absolute;inset:0;');
    s.tl = gsap.timeline({ paused: true });
    if (s.build) s.build(s.root, s.tl, s);
    s.tl.set({}, {}, s.dur * (s.warp || 1)); // warp > 1 squeezes an animation built for a longer scene
    // per-scene voiceover recording: video/media/vo/<id>.mp3
    const a = new Audio();
    const vm = { el: a, start: s.start, end: s.end, offset: 0, ok: false, scene: s, kind: 'vo' };
    a.preload = 'auto';
    a.addEventListener('loadeddata', () => { vm.ok = true; renderList(); });
    a.src = `media/vo/${s.id}.mp3`;
    media.push(vm);
  });
  stage.appendChild(subs);

  // optional single voiceover track for the whole video: video/media/voiceover.mp3
  const full = new Audio();
  const fm = { el: full, start: 0, end: total, offset: 0, ok: false, kind: 'vo-full' };
  full.addEventListener('loadeddata', () => { fm.ok = true; renderList(); });
  full.src = 'media/voiceover.mp3';
  media.push(fm);


  // ---------- sound effects (synthesized by make_sfx.py, timed by media/sfx/events.json) ----------
  const sfx = { events: null, gains: {}, bank: {} };
  fetch('media/sfx/events.json').then(r => r.json()).then(j => { sfx.events = j.events; sfx.gains = j.gains; }).catch(() => {});
  const playSfx = name => {
    let a = sfx.bank[name];
    if (!a) a = sfx.bank[name] = new Audio(`media/sfx/${name}.wav`);
    const c = a.cloneNode(); c.volume = Math.min(1, (sfx.gains[name] || 0.3) * 1.6); c.play().catch(() => {});
  };
  let sfxLast = 0;
  function fireSfx(from, to) {
    if (!sfx.events || !playing) return;
    SCENES.forEach(s => {
      (sfx.events[s.id] || []).forEach(([dt, name]) => {
        const at = s.start + dt;
        if (at > from && at <= to && dt < s.dur) playSfx(name);
      });
    });
  }


  // ---------- subtitles: media/subs.json ({start, end, text}), written by make_subs.py ----------
  let cues = [];
  fetch('media/subs.json').then(r => r.json()).then(j => { cues = j; }).catch(() => {});
  const showSub = () => {
    const c = cues.find(c => t >= c.start && t < c.end);
    const text = c ? c.text : '';
    if (subs.textContent !== text) subs.textContent = text;
  };

  // ---------- scrubber + list ----------
  SCENES.forEach(s => {
    const seg = div(scrub, 'seg ' + (s.clip ? 'clip' : 'anim'), `flex:${s.dur}`, s.title);
    s.seg = seg;
    seg.addEventListener('pointerdown', e => e.preventDefault());
  });
  scrub.appendChild(head);
  let dragging = false;
  const seekFromEvent = e => { const r = scrub.getBoundingClientRect(); seek(((e.clientX - r.left) / r.width) * total); };
  scrub.addEventListener('pointerdown', e => { dragging = true; scrub.setPointerCapture(e.pointerId); seekFromEvent(e); });
  scrub.addEventListener('pointermove', e => { if (dragging) seekFromEvent(e); });
  scrub.addEventListener('pointerup', () => { dragging = false; });

  function renderList() {
    list.innerHTML = '';
    SCENES.forEach((s, i) => {
      const clipM = media.find(m => m.scene === s && m.kind === 'clip');
      const voM = media.find(m => m.scene === s && m.kind === 'vo');
      const bits = [];
      if (s.clip) bits.push(clipM && clipM.ok ? `<span class="ok">● ${s.clip}</span>` : `<span class="no">○ ${s.clip} missing</span>`);
      else bits.push('animation');
      if (voM && voM.ok) bits.push('<span class="ok">● vo</span>');
      const it = div(list, 'item' + (i === cur ? ' cur' : ''), '', `<span class="t">${fmt(s.start).replace(/\.\d$/, '')}</span><span class="n">${s.title}</span><span class="m">${bits.join(' · ')}</span>`);
      it.addEventListener('click', () => seek(s.start + 0.001));
      if (s.clip && s.seg) s.seg.classList.toggle('missing', !(clipM && clipM.ok));
    });
  }

  // ---------- render ----------
  function sceneAt(time) {
    for (let i = 0; i < SCENES.length; i++) if (time < SCENES[i].end) return i;
    return SCENES.length - 1;
  }

  function render() {
    const i = sceneAt(t);
    if (i !== cur) {
      SCENES.forEach((s, j) => s.layer.classList.toggle('on', j === i));
      cur = i;
      const s = SCENES[i], n = SCENES[i + 1];
      prompter.innerHTML = (s.vo || '<i>no voiceover</i>') + (n ? `<span class="next">next · ${n.title}: ${(n.vo || '').slice(0, 90)}…</span>` : '');
      renderList();
      SCENES.forEach(x => x.seg.classList.toggle('cur', x === s));
    }
    const s = SCENES[i];
    s.tl.time(Math.min(s.dur * (s.warp || 1), Math.max(0, (t - s.start) * (s.warp || 1))));
    head.style.left = (t / total * 100) + '%';
    timeEl.textContent = `${fmt(t)} / ${fmt(total).replace(/\.\d$/, '')}`;
    showSub();
    syncMedia();
  }

  function syncMedia() {
    const useFull = fm.ok;
    for (const m of media) {
      if (!m.ok) continue;
      if (m.kind === 'vo' && useFull) { m.el.pause(); continue; }
      const active = t >= m.start && t < m.end;
      const target = t - m.start + m.offset;
      if (!active || (m.el.duration && target >= m.el.duration)) { if (!m.el.paused) m.el.pause(); continue; }
      if (playing) {
        if (Math.abs(m.el.currentTime - target) > 0.25) m.el.currentTime = target;
        if (m.el.paused) m.el.play().catch(() => {});
      } else {
        if (!m.el.paused) m.el.pause();
        if (Math.abs(m.el.currentTime - target) > 0.04) m.el.currentTime = target;
      }
    }
  }

  function tick(now) {
    if (playing) {
      const prev = t;
      t += (now - last) / 1000;
      fireSfx(prev, t);
      if (t >= total) { t = total - 0.001; setPlaying(false); }
    }
    last = now;
    render();
    requestAnimationFrame(tick);
  }

  function setPlaying(p) {
    playing = p;
    playBtn.textContent = p ? '❚❚ Pause' : '▶ Play';
    if (!p) media.forEach(m => m.el.pause && m.el.pause());
  }
  function seek(time) { t = Math.max(0, Math.min(total - 0.001, time)); render(); }
  function jumpScene(d) {
    const i = sceneAt(t);
    const into = t - SCENES[i].start;
    const j = d < 0 && into > 1 ? i : Math.max(0, Math.min(SCENES.length - 1, i + d));
    seek(SCENES[j].start + 0.001);
  }

  playBtn.onclick = () => { if (t >= total - 0.01) t = 0; setPlaying(!playing); };
  document.getElementById('prev').onclick = () => jumpScene(-1);
  document.getElementById('next').onclick = () => jumpScene(1);
  document.getElementById('subsBtn').onclick = () => document.body.classList.toggle('nosubs');
  document.getElementById('cleanBtn').onclick = () => { document.body.classList.toggle('clean'); fit(); };
  document.getElementById('fsBtn').onclick = () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen());

  document.addEventListener('keydown', e => {
    if (e.target.tagName === 'INPUT') return;
    const k = e.key;
    if (k === ' ') { e.preventDefault(); playBtn.click(); }
    else if (k === 'ArrowRight') seek(t + (e.shiftKey ? 5 : 1));
    else if (k === 'ArrowLeft') seek(t - (e.shiftKey ? 5 : 1));
    else if (k === ']') jumpScene(1);
    else if (k === '[') jumpScene(-1);
    else if (k === 'Home') seek(0);
    else if (k === 'h' || k === 'H') document.getElementById('cleanBtn').click();
    else if (k === 'c' || k === 'C') document.body.classList.toggle('nosubs');
    else if (k === 'f' || k === 'F') document.getElementById('fsBtn').click();
  });

  // ---------- fit the 1920x1080 stage into the window ----------
  function fit() {
    const r = viewport.getBoundingClientRect();
    const sc = Math.min(r.width / 1920, r.height / 1080);
    stage.style.transformOrigin = '50% 50%';
    stage.style.transform = `translate(-50%, -50%) scale(${sc})`;
  }
  window.addEventListener('resize', fit);
  document.addEventListener('fullscreenchange', fit);
  fit();

  // deep link: index.html#t=37.5
  const m = location.hash.match(/t=([\d.]+)/);
  if (m) t = parseFloat(m[1]);
  renderList();
  requestAnimationFrame(now => { last = now; render(); requestAnimationFrame(tick); });
  window.PLAYER = { seek, get t() { return t; }, total };
})();
