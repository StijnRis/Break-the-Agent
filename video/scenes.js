// The video, scene by scene. Each scene: id, title, dur (s), theme ('dark'|'light'),
// optional clip (file in video/media/, filmed by hand), vo (voiceover text, also the subtitle),
// and build(root, tl, scene): adds elements to `root` and tweens to the GSAP timeline `tl`.
// Times inside build() are seconds from the start of the scene.

const ORANGE = '#FF5B1F', BLUE = '#3D6BFF', GREEN = '#1FA463', INK = '#111113';
const S = D.summary;
const R = k => Object.entries(S).find(([n]) => n.startsWith(k))[1];
const FULL = [0, 0, D.size[0], D.size[1]];
const BLD = padBox(D.bbox, 70);
const vb = b => `${b[0]} ${b[1]} ${b[2] - b[0]} ${b[3] - b[1]}`;

// bottom gradient so white type reads on top of footage
const shade = root => div(root, 'abs', 'inset:0;background:linear-gradient(180deg,rgba(0,0,0,0) 45%,rgba(0,0,0,.65) 100%);');

const SCENES = [

// ───────────────────────────── 0 · intro (filmed, cut from the phone recording)
// media/intro.mp4 = WhatsApp clip trimmed to 2.2 s–35.6 s (starts mid-jump). Times below are seconds in the cut (original − 2.2).
{
  id: 'intro', title: 'Intro', dur: 33.4, clip: 'intro.mp4', clipAudio: true, noTTS: true,
  shot: 'Intro: where are the toilets? (already filmed)',
  vo: 'Yo everybody. After a long day of hacking, I need the toilet. But where is it? I got the schematics of this building. Secret intel. So I take out Gemini 4 Hydrogen, take a picture, and ask: where are the toilets? It’s thinking… it says they’re over there. And that is wrong. Frontier intelligence, and it can’t even tell me where to go. Well, I’m finding an organizer.',
  build(root, tl, scene) {
    if (!document.getElementById('intro-css')) {
      const st = document.createElement('style'); st.id = 'intro-css';
      st.textContent = `
      .ph-wrap{position:absolute;left:90px;top:110px;width:430px;height:860px;transform-origin:50% 100%;}
      .ph-body{position:absolute;inset:0;border-radius:64px;background:#0b0b0d;box-shadow:0 40px 90px rgba(0,0,0,.55),0 0 0 3px #2b2b30,inset 0 0 0 2px #3a3a40;}
      .ph-screen{position:absolute;left:14px;top:14px;right:14px;bottom:14px;border-radius:52px;background:#141416;overflow:hidden;color:#F4F2EE;font-family:'Inter Tight',Inter,system-ui,sans-serif;}
      .ph-notch{position:absolute;left:50%;top:12px;width:120px;height:32px;margin-left:-60px;border-radius:20px;background:#000;z-index:5;}
      .ph-head{position:absolute;left:0;right:0;top:0;height:112px;padding:56px 26px 0;display:flex;align-items:center;gap:12px;font-weight:600;font-size:24px;letter-spacing:-.02em;background:#18181b;border-bottom:1px solid #2a2a2f;box-sizing:border-box;}
      .ph-head i{width:30px;height:30px;border-radius:50%;background:conic-gradient(#FF5B1F,#3D6BFF,#1FA463,#FF5B1F);}
      .ph-head small{margin-left:auto;font:500 15px 'JetBrains Mono',monospace;color:#8C8C93;}
      .ph-chat{position:absolute;left:0;right:0;top:112px;bottom:0;padding:18px 18px 0;display:flex;flex-direction:column;gap:14px;}
      .ph-card{align-self:flex-end;width:296px;border-radius:22px;overflow:hidden;background:#fff;position:relative;box-shadow:0 8px 24px rgba(0,0,0,.4);}
      .ph-card img{display:block;width:100%;}
      .ph-bub{max-width:330px;padding:14px 18px;border-radius:24px;font-size:22px;line-height:1.28;font-weight:500;}
      .ph-bub.u{align-self:flex-end;background:#3D6BFF;color:#fff;border-bottom-right-radius:8px;}
      .ph-bub.a{align-self:flex-start;background:#26262b;border-bottom-left-radius:8px;}
      .ph-dots{align-self:flex-start;background:#26262b;border-radius:24px;border-bottom-left-radius:8px;padding:16px 20px;display:flex;gap:7px;}
      .ph-dots b{width:10px;height:10px;border-radius:50%;background:#8C8C93;display:block;}
      .ph-cam{position:absolute;inset:0;background:#000;z-index:3;}
      .ph-cam .ph-img{position:absolute;left:50%;top:50%;width:330px;transform:translate(-50%,-50%) rotate(-2deg);box-shadow:0 10px 40px rgba(0,0,0,.6);}
      .ph-cam .ph-img img{width:100%;display:block;}
      .ph-cam .corner{position:absolute;width:44px;height:44px;border:0 solid #FFD84A;}
      .ph-wc{position:absolute;width:62px;height:62px;margin:-31px 0 0 -31px;filter:drop-shadow(0 4px 10px rgba(0,0,0,.5));}
      .ph-wc svg{width:100%;height:100%;display:block;}
      .ph-focus{position:absolute;left:50%;top:50%;width:120px;height:120px;margin:-60px 0 0 -60px;border:3px solid #FFD84A;border-radius:12px;}
      .ph-flash{position:absolute;inset:0;background:#fff;z-index:6;opacity:0;}
      .ph-pin{position:absolute;width:46px;height:46px;margin:-46px 0 0 -23px;}
      .ph-pin svg{display:block;width:100%;height:100%;filter:drop-shadow(0 4px 8px rgba(0,0,0,.5));}
      .ph-lab{position:absolute;white-space:nowrap;padding:5px 12px;border-radius:999px;background:#E5302A;color:#fff;font:700 15px 'JetBrains Mono',monospace;}
      .ph-wrong{position:absolute;left:300px;top:420px;padding:10px 26px;border:8px solid #E5302A;color:#E5302A;border-radius:14px;font:900 96px 'Inter Tight',Inter,sans-serif;letter-spacing:-.02em;background:rgba(255,255,255,.92);transform:rotate(-14deg);z-index:9;}
      `;
      document.head.appendChild(st);
    }
    const vid = scene.layer.querySelector('video');

    // vignette over the footage + opening title that peels away
    div(root, 'abs', 'inset:0;background:radial-gradient(ellipse at 40% 50%,rgba(0,0,0,0) 55%,rgba(0,0,0,.55) 100%);pointer-events:none;');
    const tt = div(root, 'abs disp', 'left:90px;top:80px;font-size:64px;color:#fff;text-shadow:0 4px 30px rgba(0,0,0,.6);', 'Day 3. <span class="serif o">Hour 6.</span><div class="mono" style="font-size:30px;margin-top:10px;color:#FF5B1F;">4 hours before the deadline</div>');
    tl.fromTo(tt, { opacity: 0, x: -50 }, { opacity: 1, x: 0, duration: 0.7, ease: 'expo.out' }, 0.5);
    tl.to(tt, { opacity: 0, y: -20, duration: 0.5, ease: 'power2.in' }, 4.6);

    // ---- the fake phone ----
    const wrap = div(root, 'ph-wrap', 'opacity:0;');
    div(wrap, 'ph-body', '');
    const scr = div(wrap, 'ph-screen', '');
    div(scr, 'ph-notch', '');
    div(scr, 'ph-head', '', '<i></i>Gemini 4 Hydrogen<small>online</small>');
    const chat = div(scr, 'ph-chat', '');

    // 1) camera view -> shutter
    const cam = div(scr, 'ph-cam', '');
    const camImg = div(cam, 'ph-img', '', '<img src="media/sketch.jpg">');
    [['left:34px;top:130px;', 'border-width:4px 0 0 4px;'], ['right:34px;top:130px;', 'border-width:4px 4px 0 0;'],
     ['left:34px;bottom:130px;', 'border-width:0 0 4px 4px;'], ['right:34px;bottom:130px;', 'border-width:0 4px 4px 0;']]
      .forEach(([pos, bw]) => div(cam, 'corner', pos + bw));
    const flash = div(scr, 'ph-flash', '');

    // 2) the photo as a chat attachment, with the AI's (wrong) pin
    const card = div(chat, 'ph-card', 'opacity:0;', '<img src="media/sketch.jpg">');
    const pin = div(card, 'ph-pin', 'left:70%;top:25%;opacity:0;',
      '<svg viewBox="0 0 46 46"><path d="M23 44C23 44 6 28 6 18a17 17 0 0 1 34 0c0 10-17 26-17 26z" fill="#E5302A"/><circle cx="23" cy="18" r="6.5" fill="#fff"/></svg>');
    const lab = div(card, 'ph-lab', 'left:46%;top:9%;opacity:0;', 'TOILETS');
    // where the toilets really are: the stalls drawn at the bottom right of the sketch
    const wc = div(card, 'ph-wc', 'left:66%;top:66%;opacity:0;',
      '<svg viewBox="0 0 64 64"><rect x="2" y="2" width="60" height="60" rx="16" fill="#1FA463"/><circle cx="20" cy="15" r="5" fill="#fff"/><rect x="14" y="23" width="12" height="20" rx="3" fill="#fff"/><rect x="15" y="43" width="4" height="12" fill="#fff"/><rect x="21" y="43" width="4" height="12" fill="#fff"/><circle cx="44" cy="15" r="5" fill="#fff"/><path d="M44 23l9 21H35z" fill="#fff"/><rect x="41" y="44" width="3" height="11" fill="#fff"/><rect x="45.5" y="44" width="3" height="11" fill="#fff"/><rect x="31" y="8" width="2" height="48" fill="#1FA463" opacity=".0"/></svg>');
    const wcl = div(card, 'ph-lab', 'left:49%;top:74%;opacity:0;background:#1FA463;', 'REAL TOILETS');
    const focus = div(cam, 'ph-focus', 'opacity:0;');
    const q = div(chat, 'ph-bub u', 'opacity:0;', '');
    const dots = div(chat, 'ph-dots', 'opacity:0;', '<b></b><b></b><b></b>');
    const ans = div(chat, 'ph-bub a', 'opacity:0;', 'The toilets are in the top-right room, about 8 metres away.');
    const stamp = div(wrap, 'ph-wrong', 'opacity:0;', 'WRONG');

    // phone slides in with "I take out my AI" (orig 16.4 s → 14.4 s)
    tl.fromTo(wrap, { x: -520, rotation: -10, opacity: 0 }, { x: 0, rotation: -3, opacity: 1, duration: 0.9, ease: 'expo.out' }, 13.8);
    tl.fromTo(camImg, { scale: 1.25, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.7, ease: 'power3.out' }, 14.4);
    // he lifts the phone at ~16.4 and holds it steady on the paper: focus ring, then the shutter at 17.4
    tl.fromTo(focus, { opacity: 0, scale: 1.6 }, { opacity: 1, scale: 1, duration: 0.35, ease: 'power3.out', immediateRender: false }, 16.5);
    tl.to(focus, { scale: 0.92, duration: 0.2, yoyo: true, repeat: 3, ease: 'sine.inOut' }, 16.9);
    tl.to(focus, { opacity: 0, duration: 0.1 }, 17.35);
    tl.to(flash, { opacity: 1, duration: 0.05 }, 17.4);
    tl.to(flash, { opacity: 0, duration: 0.45, ease: 'power2.out' }, 17.45);
    tl.set(cam, { display: 'none' }, 17.45);
    tl.fromTo(card, { opacity: 0, y: 40, scale: 0.8 }, { opacity: 1, y: 0, scale: 1, duration: 0.5, ease: 'back.out(1.6)', immediateRender: false }, 17.5);
    // question (orig 20.1 → 18.1)
    tl.fromTo(q, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.25, immediateRender: false }, 17.9);
    typeText(tl, q, 'Where are the toilets here?', 17.95, { cps: 17 });
    // thinking (orig 25.1 → 23.1)
    tl.fromTo(dots, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.3, immediateRender: false }, 22.7);
    tl.fromTo(dots.children, { y: 0 }, { y: -7, duration: 0.28, stagger: 0.12, repeat: 7, yoyo: true, ease: 'sine.inOut', immediateRender: false }, 22.7);
    tl.to(dots, { opacity: 0, duration: 0.15 }, 25.1);
    tl.set(dots, { display: 'none' }, 25.25);
    // answer, top right (orig 27.5 → 25.5)
    tl.fromTo(ans, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.3, immediateRender: false }, 25.3);
    tl.fromTo(pin, { opacity: 0, y: -90, scale: 0.6 }, { opacity: 1, y: 0, scale: 1, duration: 0.5, ease: 'bounce.out', immediateRender: false }, 25.4);
    tl.fromTo(lab, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.3, ease: 'back.out(2)', immediateRender: false }, 25.8);
    // "…and that is wrong" (orig 28.5 → 26.5): stamp, shake, punch-in on the footage
    tl.fromTo(stamp, { opacity: 0, scale: 3 }, { opacity: 1, scale: 1, duration: 0.22, ease: 'power4.in', immediateRender: false }, 26.4);
    tl.fromTo(wc, { opacity: 0, scale: 0.2 }, { opacity: 1, scale: 1, duration: 0.45, ease: 'back.out(2.4)', immediateRender: false }, 26.55);
    tl.fromTo(wcl, { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: 0.3, immediateRender: false }, 26.9);
    tl.to(wc, { scale: 1.18, duration: 0.35, yoyo: true, repeat: 5, ease: 'sine.inOut' }, 27.1);
    tl.to(wrap, { x: -14, duration: 0.05, repeat: 7, yoyo: true, ease: 'none' }, 26.65);
    tl.to(vid, { scale: 1.07, duration: 0.25, ease: 'power3.out' }, 26.6);
    tl.to(vid, { scale: 1, duration: 1.2, ease: 'power2.inOut' }, 27.2);
    // phone leaves (orig 33 → 31)
    tl.to(wrap, { x: -560, rotation: -10, opacity: 0, duration: 0.7, ease: 'power3.in' }, 30.5);
  },
},

// ───────────────────────────── 1b · the problem: a scan line finds questions on the plan
{
  id: 'problem', title: 'The problem', dur: 10, theme: 'dark',
  vo: 'That’s the problem. Reading a floor plan looks easy. For an AI agent, it isn’t. So we built an environment around it: Blueprint to Schematic.',
  build(root, tl) {
    const BX = 360, BW = 1200, BH = 1080;
    const pv = planView(root, { x: BX, y: 0, w: BW, h: BH, view: BLD });
    pv.box.style.borderRadius = '0';
    tl.fromTo(pv.box, { opacity: 0 }, { opacity: 1, duration: 0.8 }, 0);
    // drawing-pixel -> stage coordinates (the plan is letterboxed in its box)
    const vw = BLD[2] - BLD[0], vh = BLD[3] - BLD[1], sc = Math.min(BW / vw, BH / vh);
    const sx = px => BX + BW / 2 + (px - (BLD[0] + BLD[2]) / 2) * sc;
    const sy = py => BH / 2 + (py - (BLD[1] + BLD[3]) / 2) * sc;
    const cen = r => [r.polygon.reduce((a, p) => a + p[0], 0) / r.polygon.length, r.polygon.reduce((a, p) => a + p[1], 0) / r.polygon.length];

    div(root, 'abs label', 'left:60px;top:60px;', 'The problem');

    // scan line sweeps left → right; every room it passes gets a question
    const T0 = 1.0, T1 = 4.2;
    const line = div(root, 'abs', `left:${BX}px;top:0;width:6px;height:1080px;background:${ORANGE};box-shadow:0 0 40px 10px rgba(255,91,31,.55);opacity:0;`);
    tl.set(line, { opacity: 1 }, T0);
    tl.fromTo(line, { x: 0 }, { x: BW, duration: T1 - T0, ease: 'none' }, T0);
    tl.to(line, { opacity: 0, duration: 0.2 }, T1);
    const qs = ['wall?', 'which room?', 'scale?', 'door?', 'how big?', 'where?', 'wall?', 'how big?'];
    D.gt.rooms.slice(0, 8).forEach((r, i) => {
      const [cx, cy] = cen(r);
      const x = sx(cx), y = sy(cy);
      const t = T0 + (x - BX) / BW * (T1 - T0);
      const tag = div(root, 'abs mono', `left:${x - 70}px;top:${y - 24}px;padding:8px 16px;border-radius:999px;background:${ORANGE};color:#111;font-size:26px;font-weight:600;white-space:nowrap;opacity:0;`, qs[i % qs.length]);
      tl.fromTo(tag, { opacity: 0, scale: 0.2, y: 20 }, { opacity: 1, scale: 1, y: 0, duration: 0.35, ease: 'back.out(2.2)', immediateRender: false }, t);
      tl.to(tag, { y: -8, duration: 0.9, yoyo: true, repeat: 3, ease: 'sine.inOut' }, t + 0.35);
    });

    // lower-third types the thought, then swaps it
    const band = div(root, 'abs', `left:${BX + 80}px;bottom:70px;width:${BW - 160}px;padding:26px 44px;border-radius:22px;background:${INK};box-shadow:0 16px 60px rgba(0,0,0,.5);`);
    const l1 = div(band, 'disp', 'font-size:72px;color:#F4F2EE;', '');
    const l2 = div(band, 'disp', 'font-size:72px;position:absolute;left:44px;top:26px;opacity:0;', '');
    tl.fromTo(band, { y: 140, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, ease: 'expo.out' }, 3.4);
    typeText(tl, l1, 'Looks easy.', 3.8, { cps: 14 });
    tl.to(l1, { opacity: 0, duration: 0.2 }, 5.0);
    tl.set(l2, { opacity: 1 }, 5.2);
    l2.innerHTML = '<span class="serif o" id="x"></span>';
    typeText(tl, l2.firstChild, 'For an agent, it isn’t.', 5.2, { cps: 17 });
    // the answer to the question: what we built
    const pill = div(root, 'abs pill', `left:${BX + 80}px;top:60px;font-size:34px;padding:14px 28px;background:${ORANGE};color:#111;border-color:${ORANGE};`, 'Blueprint → Schematic');
    tl.fromTo(pill, { opacity: 0, x: -40 }, { opacity: 1, x: 0, duration: 0.5, ease: 'expo.out' }, 7.2);
  },
},

// ───────────────────────────── 2 · by hand: see, calibrate, measure (animated, replaces the filmed close-ups)
{
  id: 'measure', title: 'By hand', dur: 9, theme: 'light',
  vo: 'To read one, you have to see the walls, find the scale, and measure every room. That’s spatial reasoning. There’s no answer to look up.',
  build(root, tl) {
    const truth = D.gt.m_per_px;
    const beat = (n, word, at, until) => {
      const e = div(root, 'abs', 'left:80px;top:56px;opacity:0;', `<span class="label" style="font-size:24px;">0${n}</span><br><span class="disp" style="font-size:88px;color:${INK};">${word}</span>`);
      tl.fromTo(e, { opacity: 0, x: -40 }, { opacity: 1, x: 0, duration: 0.5, ease: 'expo.out', immediateRender: false }, at);
      tl.to(e, { opacity: 0, duration: 0.25 }, until - 0.25);
    };
    const show = (box, at, until) => {
      tl.fromTo(box, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out', immediateRender: false }, at);
      tl.to(box, { opacity: 0, duration: 0.3 }, until - 0.3);
    };
    const T = [[0, 2.9], [2.7, 5.4], [5.2, 9]];

    // ---- 01 See: a pencil traces an interior wall, then the walls fill in
    beat(1, 'See.', T[0][0] + 0.2, T[0][1]);
    const C = planView(root, { x: 480, y: 70, w: 1300, h: 940, view: BLD });
    tl.set(C.box, { opacity: 0 }, 0);
    show(C.box, T[0][0], T[0][1] + 0.1);
    const trace = svgEl('line', { x1: 1092, y1: 915, x2: 1092, y2: 1215, stroke: INK, 'stroke-width': 14, 'stroke-linecap': 'round' }, C.g('pencil'));
    const wl = svgEl('line', { x1: 1092, y1: 915, x2: 1092, y2: 1215, stroke: ORANGE, 'stroke-width': 18, 'stroke-linecap': 'round', opacity: 0.9 }, C.g('pencil'));
    wl.style.strokeDasharray = 300;
    const pen = svgEl('g', {}, C.g('pencil'));
    svgEl('polygon', { points: '0,0 -16,-50 16,-50', fill: '#E8B98A', stroke: INK, 'stroke-width': 4 }, pen);
    svgEl('polygon', { points: '-16,-50 16,-50 16,-260 -16,-260', fill: '#F5C542', stroke: INK, 'stroke-width': 4 }, pen);
    svgEl('polygon', { points: '-16,-260 16,-260 16,-285 -16,-285', fill: '#E5302A', stroke: INK, 'stroke-width': 4 }, pen);
    svgEl('polygon', { points: '0,0 -5,-16 5,-16', fill: INK }, pen);
    pen.style.transformOrigin = '0 0';
    trace.setAttribute('opacity', 0);
    tl.fromTo(wl, { strokeDashoffset: 300 }, { strokeDashoffset: 0, duration: 1.0, ease: 'none' }, 0.5);
    tl.fromTo(pen, { x: 1092, y: 915, rotation: 28, opacity: 0 }, { x: 1092, y: 1215, rotation: 28, opacity: 1, duration: 1.0, ease: 'none', immediateRender: false }, 0.5);
    tl.to(pen, { opacity: 0, duration: 0.25 }, 1.6);
    C.g('walls').setAttribute('opacity', 0.55);
    const rw = drawWalls(C.g('walls'), D.ref.schematic.walls, BLUE, { opacity: 1 });
    tl.fromTo(rw, { opacity: 0 }, { opacity: 1, duration: 0.15, stagger: { amount: 1.0, from: 'start' } }, 1.7);

    // ---- 02 Calibrate: tap "1:100", the scale bar lights up
    beat(2, 'Calibrate.', T[1][0] + 0.2, T[1][1]);
    const A = planView(root, { x: 210, y: 300, w: 1500, h: 600, view: [1560, 1400, 2440, 1752] });
    tl.set(A.box, { opacity: 0 }, 0);
    show(A.box, T[1][0], T[1][1] + 0.1);
    const gA = A.g('tap');
    const ring = svgEl('ellipse', { cx: 1928, cy: 1546, rx: 80, ry: 30, fill: 'none', stroke: ORANGE, 'stroke-width': 7 }, gA);
    const bar = svgEl('rect', { x: 612, y: 1606, width: 300, height: 26, fill: ORANGE, 'fill-opacity': 0.25, stroke: ORANGE, 'stroke-width': 5, rx: 6 }, A.g('tap'));
    tl.fromTo(ring, { opacity: 0, scale: 2.2, transformOrigin: '1928px 1546px' }, { opacity: 1, scale: 1, duration: 0.45, ease: 'back.out(2)', immediateRender: false }, T[1][0] + 0.7);
    [0, 0.35].forEach(d => {
      const rp = svgEl('circle', { cx: 1928, cy: 1546, r: 10, fill: 'none', stroke: ORANGE, 'stroke-width': 6, opacity: 0 }, gA);
      tl.fromTo(rp, { attr: { r: 10 }, opacity: 0.9 }, { attr: { r: 120 }, opacity: 0, duration: 0.8, ease: 'power2.out', immediateRender: false }, T[1][0] + 1.2 + d);
    });
    const sc = div(root, 'abs mono', `left:210px;top:920px;font-size:44px;font-weight:600;color:${INK};opacity:0;`, `1 : 100 <span class="o">→</span> ${truth.toFixed(4)} m / px`);
    fadeIn(tl, sc, T[1][0] + 1.9, 0.4); tl.to(sc, { opacity: 0, duration: 0.25 }, T[1][1] - 0.25);

    // ---- 03 Measure: a ruler lies across a room
    beat(3, 'Measure.', T[2][0] + 0.2, T[2][1] + 1);
    const B = planView(root, { x: 360, y: 135, w: 1200, h: 810, view: [1030, 985, 1430, 1255] });
    tl.set(B.box, { opacity: 0 }, 0);
    tl.fromTo(B.box, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out', immediateRender: false }, T[2][0]);
    const gB = B.g('ruler');
    const ruler = svgEl('g', {}, gB);
    svgEl('rect', { x: 1072, y: 1050, width: 310, height: 34, fill: '#F2D26B', stroke: INK, 'stroke-width': 2.5, rx: 3 }, ruler);
    for (let k = 0; k <= 30; k++) svgEl('line', { x1: 1072 + k * 10 + 5, y1: 1050, x2: 1072 + k * 10 + 5, y2: 1050 + (k % 5 === 0 ? 20 : 11), stroke: INK, 'stroke-width': 2 }, ruler);
    tl.fromTo(ruler, { x: -520, opacity: 0 }, { x: 0, opacity: 1, duration: 0.9, ease: 'expo.out', immediateRender: false }, T[2][0] + 0.5);
    const dim = svgEl('line', { x1: 1092, y1: 1105, x2: 1092, y2: 1105, stroke: ORANGE, 'stroke-width': 6, 'stroke-linecap': 'round' }, gB);
    const capL = svgEl('line', { x1: 1092, y1: 1090, x2: 1092, y2: 1120, stroke: ORANGE, 'stroke-width': 6, 'stroke-linecap': 'round' }, gB);
    const capR = svgEl('line', { x1: 1362, y1: 1090, x2: 1362, y2: 1120, stroke: ORANGE, 'stroke-width': 6, 'stroke-linecap': 'round', opacity: 0 }, gB);
    tl.fromTo(dim, { attr: { x2: 1092 } }, { attr: { x2: 1362 }, duration: 0.9, ease: 'power2.inOut', immediateRender: false }, T[2][0] + 1.6);
    tl.fromTo(capL, { opacity: 0 }, { opacity: 1, duration: 0.1, immediateRender: false }, T[2][0] + 1.6);
    tl.fromTo(capR, { opacity: 0 }, { opacity: 1, duration: 0.1, immediateRender: false }, T[2][0] + 2.5);
    const m = div(root, 'abs score o', 'left:1600px;top:420px;font-size:96px;opacity:0;', '');
    countUp(tl, m, 270 * truth, T[2][0] + 1.6, { dur: 0.9, decimals: 2, suffix: ' m' });
    fadeIn(tl, m, T[2][0] + 1.6, 0.2);
  },
},

// ───────────────────────────── 3 · the environment: tools orbit the drawing, then three things are taken away
{
  id: 'machine', title: 'The setup', dur: 12.5, theme: 'light',
  vo: 'Here’s the environment. The agent gets one drawing and eight tools: zoom, OCR, segmentation, measurement. No shell. No code. Just its eyes and its judgement.',
  build(root, tl) {
    const CX = 960, CY = 560;
    const ring = div(root, 'abs', 'inset:0;');
    const pv = planView(ring, { x: CX - 260, y: CY - 220, w: 520, h: 440, view: BLD });
    tl.fromTo(pv.box, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.9, ease: 'expo.out' }, 0);
    const title = div(root, 'abs label', 'left:80px;top:70px;font-size:26px;', '');
    typeText(tl, title, 'The environment · one drawing · eight tools', 0.3, { cps: 38 });

    const svg = svgEl('svg', { width: 1920, height: 1080, style: 'position:absolute;left:0;top:0;' }, ring);
    const tools = ['view_region', 'estimate_scale', 'read_room_labels', 'segment_rooms', 'measure_area', 'preview_schematic', 'get_task', 'submit_schematic'];
    tools.forEach((name, i) => {
      const a = -Math.PI / 2 + i * 2 * Math.PI / tools.length;
      const x = CX + Math.cos(a) * 720, y = CY + Math.sin(a) * 390;
      const ex = CX + Math.cos(a) * 270, ey = CY + Math.sin(a) * 240; // line starts at the plan's edge
      const ln = svgEl('line', { x1: ex, y1: ey, x2: x, y2: y, stroke: '#C9C4B8', 'stroke-width': 3, 'stroke-dasharray': '10 8' }, svg);
      const len = Math.hypot(x - ex, y - ey);
      const dot = svgEl('circle', { cx: ex, cy: ey, r: 9, fill: ORANGE, opacity: 0 }, svg);
      const t0 = 0.9 + i * 0.42;
      tl.fromTo(ln, { opacity: 0 }, { opacity: 1, duration: 0.3 }, t0);
      // a pulse of "information" travels out to the tool and the tool lights up
      tl.fromTo(dot, { attr: { cx: ex, cy: ey }, opacity: 1 }, { attr: { cx: x, cy: y }, duration: 0.55, ease: 'power2.in' }, t0 + 0.1);
      tl.to(dot, { opacity: 0, duration: 0.1 }, t0 + 0.65);
      const node = div(ring, 'abs pill', `left:${x}px;top:${y}px;font-size:26px;`, name);
      gsap.set(node, { xPercent: -50, yPercent: -50 });
      tl.fromTo(node, { opacity: 0, scale: 0.5 }, { opacity: 1, scale: 1, duration: 0.4, ease: 'back.out(2)' }, t0 + 0.6);
      tl.fromTo(node, { backgroundColor: '#fff' }, { backgroundColor: '#FFE3D6', borderColor: ORANGE, duration: 0.2, yoyo: true, repeat: 1, immediateRender: false }, t0 + 0.7);
    });

    // …then the ring dims and three things are crossed out
    tl.to(ring, { opacity: 0.12, duration: 0.6 }, 6.6);
    const items = [['$ bash', 7.0], ['import numpy', 7.9], ['answer_key.json', 8.8]];
    items.forEach(([txt, t], i) => {
      const y = 330 + i * 150;
      const chip = div(root, 'abs mono', `left:${CX}px;top:${y}px;font-size:68px;font-weight:600;color:${INK};padding:18px 40px;border-radius:20px;background:#fff;box-shadow:0 14px 40px rgba(17,17,19,.12);white-space:nowrap;opacity:0;`, txt);
      const strike = div(root, 'abs', `left:${CX - 330}px;top:${y + 52}px;width:660px;height:10px;border-radius:5px;background:#E5302A;transform-origin:left center;`);
      gsap.set(strike, { scaleX: 0, rotation: -3 });
      gsap.set(chip, { xPercent: -50 });
      tl.fromTo(chip, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.4, ease: 'expo.out', immediateRender: false }, t);
      tl.to(strike, { scaleX: 1, duration: 0.35, ease: 'power3.out' }, t + 0.45);
    });
    const fin = div(root, 'abs serif o', 'left:0;right:0;top:800px;text-align:center;font-size:100px;opacity:0;', 'Just spatial reasoning.');
    tl.fromTo(fin, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.7, ease: 'expo.out', immediateRender: false }, 9.9);
  },
},

// ───────────────────────────── 4 · side-by-side replay (the money shot)
{
  id: 'demo', title: 'Replay', dur: 25, theme: 'light',
  vo: 'Watch Gemini 3.1 Pro work. Zoom. Zoom. Zoom. It works out the right scale, then second-guesses itself. Then it draws every room by hand: loose boxes, no interior walls. Our plain computer-vision solver traces the walls and snaps rooms to the lines, with no model in the loop. Point five one against point zero four.',
  build(root, tl) {
    div(root, 'abs label', 'left:80px;top:64px;', `Replay · plan ${D.task.split('_')[0]} · same drawing, same tools`);
    const W = 860, H = 640, Y = 196;
    const tagL = div(root, 'abs tag', `left:80px;top:140px;color:${INK};`, `<i style="background:${ORANGE}"></i>Gemini 3.1 Pro`);
    const tagR = div(root, 'abs tag', `left:980px;top:140px;color:${INK};`, `<i style="background:${BLUE}"></i>Our reference · plain CV, no ground truth`);
    const L = planView(root, { x: 80, y: Y, w: W, h: H, view: FULL });
    const Rv = planView(root, { x: 980, y: Y, w: W, h: H, view: FULL });
    fadeIn(tl, [tagL, tagR, L.box, Rv.box], 0, 0.5);

    // ---- right: the reference
    tl.to(Rv.svg, { attr: { viewBox: vb(BLD) }, duration: 1.4, ease: 'power3.inOut' }, 1.2);
    const rs = D.ref.schematic;
    Rv.g('walls').setAttribute('opacity', 0.55); // flat colour where wall boxes overlap
    const rw = drawWalls(Rv.g('walls'), rs.walls, BLUE, { opacity: 1 });
    tl.fromTo(rw, { opacity: 0 }, { opacity: 1, duration: 0.2, stagger: { amount: 1.6, from: 'start' } }, 2.6);
    const rr = drawRooms(Rv.g('rooms'), rs.rooms, BLUE, { fill: 0.16, width: 4 });
    drawIn(tl, rr, 4.2, { dur: 0.7, stagger: 0.1 });
    const rd = drawSegs(Rv.g('doors'), rs.doors, GREEN, 10);
    popIn(tl, rd, 6.4, { stagger: 0.04, y: 0, scale: 0.4 });
    const done = div(root, 'abs pill', 'left:1000px;top:770px;font-size:22px;', 'done · no model calls');
    popIn(tl, done, 8.2);

    // ---- left: Gemini, replayed from its real tool trace
    const box = svgEl('rect', { x: 0, y: 0, width: 10, height: 10, fill: ORANGE, 'fill-opacity': 0.08, stroke: ORANGE, 'stroke-width': 10, rx: 6, opacity: 0 }, L.g('zoom'));
    const counter = div(root, 'abs mono', `left:96px;top:${Y + H - 56}px;font-size:22px;color:#fff;background:${INK};padding:8px 14px;border-radius:999px;opacity:0;`, '');
    const STEP = 0.95, T0 = 1.0;
    let k = 0;
    D.agent.trace.forEach((c, i) => {
      const at = T0 + i * STEP;
      tl.call(() => { counter.textContent = `call ${i + 1} / ${D.agent.trace.length} · ${c.tool}`; }, null, at);
      tl.set(counter, { opacity: 1 }, at);
      if (c.tool === 'view_region' && c.args.x1 != null) {
        const a = c.args;
        const to = { x: a.x0, y: a.y0, width: a.x1 - a.x0, height: a.y1 - a.y0 };
        if (k++ === 0) tl.fromTo(box, { attr: to, opacity: 0 }, { attr: to, opacity: 1, duration: 0.25 }, at);
        else tl.to(box, { attr: to, duration: 0.55, ease: 'power3.inOut' }, at);
      }
      if (c.tool === 'segment_rooms' && c.args.seeds) {
        const dots = c.args.seeds.map(p => svgEl('circle', { cx: p[0], cy: p[1], r: 16, fill: ORANGE }, L.g('seeds')));
        popIn(tl, dots, at, { stagger: 0.02, y: 0, scale: 0 });
        fadeOut(tl, dots, at + 3.5, 0.5);
      }
    });
    const tEnd = T0 + D.agent.trace.length * STEP;
    tl.to(box, { opacity: 0, duration: 0.3 }, tEnd - 0.4);

    // what it was thinking (real snippets from the trace)
    const th = div(root, 'abs thought', `left:120px;top:${Y + 330}px;opacity:0;`, '');
    const who = '<span class="who">Gemini · thinking</span>';
    const scaleAt = T0 + 3 * STEP;
    tl.set(th, { opacity: 1, y: 0 }, scaleAt);
    tl.fromTo(th, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.3, immediateRender: false }, scaleAt);
    const line1 = div(th, '', '', ''); line1.insertAdjacentHTML('beforebegin', who);
    typeText(tl, line1, '“…1:100 means 0.016935 m/px.”', scaleAt + 0.2, { cps: 40 });
    const line2 = div(th, '', `color:${ORANGE};margin-top:6px;`, '');
    typeText(tl, line2, '“Wait, let’s look at the scale bar again.”', scaleAt + 1.3, { cps: 40 });
    tl.to(th, { opacity: 0, duration: 0.3 }, scaleAt + 3.6);

    const th2 = div(root, 'abs thought', `left:120px;top:${Y + 330}px;opacity:0;`, who);
    const l3 = div(th2, '', '', '');
    tl.fromTo(th2, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.3 }, tEnd - 1.2);
    typeText(tl, l3, '“Now I’ll build the polygons for each room manually using the images.”', tEnd - 1.0, { cps: 50 });
    tl.to(th2, { opacity: 0, duration: 0.3 }, tEnd + 1.6);

    // its submission: rooms only, drawn by hand
    tl.to(L.svg, { attr: { viewBox: vb(BLD) }, duration: 1.2, ease: 'power3.inOut' }, tEnd + 0.4);
    const gr = drawRooms(L.g('rooms'), D.agent.schematic.rooms, ORANGE, { fill: 0.18, width: 5 });
    drawIn(tl, gr, tEnd + 1.5, { dur: 0.6, stagger: 0.12 });
    tl.set(counter, { opacity: 0 }, tEnd + 1.0);

    // scores
    const sAt = 21.0;
    const sl = div(root, 'abs score', `left:80px;top:${Y + H + 40}px;color:${ORANGE};`, '');
    const sr = div(root, 'abs score', `left:980px;top:${Y + H + 40}px;color:${BLUE};`, '');
    const ll = div(root, 'abs label', `left:86px;top:${Y + H + 172}px;`, 'reward');
    const lr = div(root, 'abs label', `left:986px;top:${Y + H + 172}px;`, 'reward');
    fadeIn(tl, [sl, sr, ll, lr], sAt, 0.2);
    countUp(tl, sl, D.agent.reward, sAt, { dur: 1.0 });
    countUp(tl, sr, D.ref.reward, sAt, { dur: 1.4 });
    const x = div(root, 'abs disp', `left:1440px;top:${Y + H + 60}px;font-size:88px;color:${INK};`, `${Math.round(D.ref.reward / D.agent.reward)}<span class="serif">×</span>`);
    const xl = div(root, 'abs label', `left:1446px;top:${Y + H + 172}px;`, 'the score');
    popIn(tl, [x, xl], sAt + 1.6, { stagger: 0.1 });
    tl.set({}, {}, 25);
  },
},

// ───────────────────────────── 5 · the gap
{
  id: 'gap', title: 'The gap', dur: 16, theme: 'dark',
  vo: 'Across fifteen unseen plans, three runs each, Gemini scores point three four. Our solver: point five nine. Stop our solver halfway, and it still beats the frontier agent. Three runs, within two hundredths.',
  build(root, tl) {
    div(root, 'abs label', 'left:120px;top:110px;', '15 unseen plans · 3 runs each · reward 0 → 1');
    const h = div(root, 'abs disp', 'left:120px;top:170px;font-size:104px;width:1700px;', 'Half our solver beats<br>the <span class="serif o">frontier.</span>');
    wipe(tl, h, 0.3, 0.9);
    const rows = [
      ['Our reference', R('reference').reward, BLUE, 'deterministic'],
      ['Our reference, stopped at 50 %', R('stop early (50').reward, '#5A5A62', ''],
      ['Gemini 3.1 Pro', R('agent: gemini-3.1-pro-preview').reward, ORANGE, R('agent: gemini-3.1-pro-preview').runs.map(v => v.toFixed(3)).join(' · ')],
      ['Do nothing', 0, '#5A5A62', ''],
    ];
    const MAXW = 1120;
    rows.forEach((r, i) => {
      const y = 520 + i * 118;
      div(root, 'abs', `left:120px;top:${y + 4}px;width:520px;font-size:34px;font-weight:600;color:#F4F2EE;`, r[0]);
      if (r[3]) div(root, 'abs mono', `left:120px;top:${y + 50}px;font-size:20px;color:#8C8C93;`, r[3]);
      div(root, 'abs', `left:660px;top:${y}px;width:${MAXW}px;height:76px;border-radius:12px;background:#161618;`);
      const bar = div(root, 'abs', `left:660px;top:${y}px;width:${Math.max(8, r[1] * MAXW)}px;height:76px;border-radius:12px;background:${r[2]};transform-origin:left center;`);
      const val = div(root, 'abs score', `left:${680 + Math.max(8, r[1] * MAXW)}px;top:${y + 8}px;font-size:60px;color:#F4F2EE;`, '');
      tl.fromTo(bar, { scaleX: 0 }, { scaleX: 1, duration: 1.1, ease: 'expo.out' }, 2.2 + i * 0.5);
      countUp(tl, val, r[1], 2.2 + i * 0.5, { dur: 1.1, decimals: 3 });
      r.el = bar;
    });
    // kicker: highlight the 50 % row against Gemini
    const ring = div(root, 'abs', `left:100px;top:${520 + 118 - 18}px;width:1720px;height:${118 * 2 + 0}px;border:3px solid ${ORANGE};border-radius:20px;`);
    tl.fromTo(ring, { opacity: 0, scale: 1.03 }, { opacity: 1, scale: 1, duration: 0.5, ease: 'expo.out' }, 7.8);
    const k = div(root, 'abs pill', `left:1460px;top:${520 + 118 * 3 - 4}px;background:${ORANGE};color:#111;border-color:${ORANGE};`, '0.438 > 0.342');
    popIn(tl, k, 8.3);
  },
},

// ───────────────────────────── 6 · why it fails: two scale numbers on a number line, then the room grows
{
  id: 'scale', title: 'Why it fails', dur: 13, theme: 'light',
  vo: 'So what goes wrong? It computed the right scale. Then it eyeballed the scale bar, used a different number, and every area came out six percent off. It can see. It can’t measure.',
  build(root, tl) {
    const truth = D.gt.m_per_px, used = D.agent.schematic.m_per_px;
    const V0 = 0.0165, V1 = 0.0178, AX0 = 210, AXW = 1500, AY = 430;
    const pos = v => AX0 + (v - V0) / (V1 - V0) * AXW;
    div(root, 'abs label', 'left:80px;top:60px;', `Gemini 3.1 Pro · scale in metres per pixel`);

    // axis with ticks
    const axis = div(root, 'abs', `left:${AX0}px;top:${AY}px;width:${AXW}px;height:5px;background:${INK};transform-origin:left center;`);
    tl.fromTo(axis, { scaleX: 0 }, { scaleX: 1, duration: 1.0, ease: 'power3.out' }, 0.2);
    for (let v = V0, i = 0; v <= V1 + 1e-9; v += 0.0001, i++) {
      const x = pos(v);
      const t = div(root, 'abs', `left:${x - 1.5}px;top:${AY}px;width:3px;height:${i % 5 === 0 ? 30 : 16}px;background:${INK};opacity:0;`);
      tl.fromTo(t, { opacity: 0 }, { opacity: 1, duration: 0.2 }, 0.5 + i * 0.05);
      if (i % 5 === 0) { const l = div(root, 'abs mono', `left:${x - 60}px;top:${AY + 40}px;width:120px;text-align:center;font-size:20px;color:#6B6B72;opacity:0;`, v.toFixed(4)); tl.fromTo(l, { opacity: 0 }, { opacity: 1, duration: 0.3 }, 0.9 + i * 0.05); }
    }

    // flag for a value: stem up from the axis, label card on top
    const flag = (x, color, head, val, note, at, from) => {
      const stem = div(root, 'abs', `left:${x - 3}px;top:${AY - 170}px;width:6px;height:170px;background:${color};transform-origin:bottom;`);
      const card = div(root, 'abs card', `left:${x - 230}px;top:${AY - 300}px;width:460px;padding:16px 24px;box-shadow:0 0 0 3px ${color},0 14px 40px rgba(17,17,19,.1);display:flex;flex-direction:column;gap:2px;`,
        `<span class="label" style="font-size:18px;">${head}</span><span class="score" style="font-size:60px;color:${color};">${val}</span><span class="mono" style="font-size:20px;color:${color};">${note}</span>`);
      const g = [stem, card];
      tl.fromTo(g, { opacity: 0, y: -50 }, { opacity: 1, y: 0, duration: 0.5, ease: 'bounce.out', immediateRender: false }, at);
      return g;
    };
    flag(pos(truth), GREEN, 'from “1:100 on A3”', '0.016935', `✓ survey: ${truth.toFixed(6)}`, 2.2);
    const f2 = flag(pos(used), ORANGE, 'from the scale bar, by eye', used.toFixed(6), '✗ the one it submitted', 4.0);
    tl.fromTo(f2, { x: 360 }, { x: 0, duration: 0.7, ease: 'back.out(1.4)', immediateRender: false }, 4.0);

    // the gap between them
    const bx = pos(truth), bw = pos(used) - pos(truth);
    const br = div(root, 'abs', `left:${bx}px;top:${AY + 90}px;width:${bw}px;height:26px;border:5px solid ${ORANGE};border-top:none;border-radius:0 0 14px 14px;transform-origin:left;`);
    tl.fromTo(br, { scaleX: 0 }, { scaleX: 1, duration: 0.5, ease: 'power3.out' }, 5.2);
    const pct = div(root, 'abs score o', `left:${bx}px;width:${bw}px;top:${AY + 128}px;text-align:center;font-size:64px;`, '');
    countUp(tl, pct, (used / truth - 1) * 100, 5.5, { dur: 0.6, decimals: 1, prefix: '+', suffix: ' %' });
    tl.fromTo(pct, { opacity: 0 }, { opacity: 1, duration: 0.2 }, 5.5);

    // one real room, drawn with each scale: it swells and falls out of tolerance
    const rm = D.gt.rooms.map(r => ({ r, a: Math.abs(r.polygon.reduce((s, p, i, A) => { const q = A[(i + 1) % A.length]; return s + p[0] * q[1] - q[0] * p[1]; }, 0)) / 2 }))
      .filter(o => o.a * truth * truth > 14 && o.a * truth * truth < 45).sort((a, b) => b.a - a.a)[0] || { r: D.gt.rooms[0], a: 1 };
    const xs = rm.r.polygon.map(p => p[0]), ys = rm.r.polygon.map(p => p[1]);
    const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    const RW = 480, RH = 330, k = Math.min(RW / (x1 - x0), RH / (y1 - y0)) * 0.86;
    const rsvg = svgEl('svg', { width: RW, height: RH, style: `position:absolute;left:250px;top:690px;overflow:visible;` }, root);
    const pts = rm.r.polygon.map(p => [(p[0] - (x0 + x1) / 2) * k + RW / 2, (p[1] - (y0 + y1) / 2) * k + RH / 2]);
    const pG = svgEl('path', { d: polyPath(pts), fill: GREEN, 'fill-opacity': 0.18, stroke: GREEN, 'stroke-width': 6, 'stroke-linejoin': 'round' }, rsvg);
    const pO = svgEl('path', { d: polyPath(pts), fill: ORANGE, 'fill-opacity': 0.12, stroke: ORANGE, 'stroke-width': 6, 'stroke-linejoin': 'round', 'stroke-dasharray': '14 10' }, rsvg);
    pO.style.transformOrigin = `${RW / 2}px ${RH / 2}px`;
    tl.fromTo([pG, pO], { opacity: 0 }, { opacity: 1, duration: 0.5 }, 7.0);
    tl.fromTo(pO, { scale: 1 }, { scale: used / truth, duration: 1.2, ease: 'elastic.out(1,0.6)', immediateRender: false }, 7.6);
    const aT = rm.a * truth * truth, aU = rm.a * used * used;
    const t1 = div(root, 'abs', 'left:880px;top:700px;font-size:34px;font-weight:600;', `<span class="mono" style="color:${GREEN}">${aT.toFixed(1)} m²</span> true`);
    const t2 = div(root, 'abs', 'left:880px;top:760px;font-size:34px;font-weight:600;', `<span class="mono" style="color:${ORANGE}">${aU.toFixed(1)} m²</span> submitted`);
    const t3 = div(root, 'abs score o', 'left:880px;top:810px;font-size:90px;', `+${((used / truth) ** 2 * 100 - 100).toFixed(1)} %`);
    const t4 = div(root, 'abs mono', 'left:880px;top:925px;font-size:26px;color:#6B6B72;', `tolerance 5 % → right in <b style="color:${ORANGE}">1 of ${D.gt.rooms.length}</b> rooms`);
    fadeIn(tl, t1, 8.2); fadeIn(tl, t2, 8.8); popIn(tl, t3, 9.4); fadeIn(tl, t4, 10.4);
  },
},

// ───────────────────────────── 7a · try to cheat: a fat marker scribbles over the whole plan (animated)
{
  id: 'marker', title: 'Cheat (paper)', dur: 5.5, theme: 'light',
  vo: 'So can you cheat?',
  build(root, tl) {
    div(root, 'abs label', 'left:80px;top:56px;', 'Cheat attempt');
    const pv = planView(root, { x: 160, y: 100, w: 1600, h: 900, view: FULL });
    tl.fromTo(pv.box, { opacity: 0, scale: 0.96 }, { opacity: 1, scale: 1, duration: 0.5, ease: 'expo.out' }, 0);
    const g = pv.g('marker');
    const [x0, y0, x1, y1] = D.bbox;
    const m = 50;
    const A = [x0 - m, y0 - m], B = [x1 + m + 14, y0 - m + 12], C = [x1 + m - 8, y1 + m], Dd = [x0 - m + 10, y1 + m + 16];
    const outline = svgEl('path', { d: `M${A}L${B}L${C}L${Dd}L${A[0] + 4},${A[1] + 6}`, fill: 'none', stroke: ORANGE, 'stroke-width': 34, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', opacity: 0.88 }, g);
    const zig = [];
    for (let i = 0, y = y0; y < y1 + m; i++, y += 120) zig.push((i % 2 ? [x0 - m + 20, y] : [x1 + m - 20, y]));
    const hatch = svgEl('path', { d: 'M' + zig.map(p => p.join(',')).join('L'), fill: 'none', stroke: ORANGE, 'stroke-width': 26, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', opacity: 0.5 }, g);
    const lens = [outline, hatch].map(p => p.getTotalLength());
    [outline, hatch].forEach((p, i) => { p.style.strokeDasharray = lens[i]; p.style.strokeDashoffset = lens[i]; });
    // marker pen that follows the stroke
    const pen = svgEl('g', {}, g);
    svgEl('polygon', { points: '0,0 -30,-60 30,-60', fill: ORANGE, stroke: INK, 'stroke-width': 6 }, pen);
    svgEl('polygon', { points: '-30,-60 30,-60 30,-330 -30,-330', fill: '#2B2B30', stroke: INK, 'stroke-width': 6 }, pen);
    svgEl('rect', { x: -30, y: -210, width: 60, height: 70, fill: ORANGE }, pen);
    pen.style.transformOrigin = '0 0';
    gsap.set(pen, { rotation: 24, opacity: 0 });
    const run = (path, len, at, dur) => {
      const o = { p: 0 };
      tl.fromTo(o, { p: 0 }, { p: 1, duration: dur, ease: 'none', immediateRender: false, onUpdate: () => {
        path.style.strokeDashoffset = len * (1 - o.p);
        const pt = path.getPointAtLength(len * o.p);
        gsap.set(pen, { x: pt.x, y: pt.y, opacity: 1 });
      } }, at);
    };
    run(outline, lens[0], 0.6, 1.5);
    run(hatch, lens[1], 2.1, 1.3);
    tl.to(pen, { opacity: 0, duration: 0.2 }, 3.45);
    // stabbed dots
    const dots = [];
    for (let i = 0; i < 28; i++) {
      const dx = x0 + ((i * 37) % 100) / 100 * (x1 - x0), dy = y0 + ((i * 61 + 13) % 100) / 100 * (y1 - y0);
      dots.push(svgEl('circle', { cx: dx, cy: dy, r: 20, fill: INK, opacity: 0 }, g));
    }
    tl.fromTo(dots, { opacity: 0, scale: 3, transformOrigin: '50% 50%' }, { opacity: 1, scale: 1, duration: 0.15, stagger: { amount: 1.2, from: 'random' }, immediateRender: false }, 3.5);
  },
},

// ───────────────────────────── 7b · exploits score nothing
{
  id: 'cheat', title: 'Cheat (score)', dur: 10, theme: 'dark',
  vo: 'One giant room: zero. A thousand doors: point zero one. A wall around it all: point zero seven.',
  build(root, tl) {
    const pv = planView(root, { x: 120, y: 120, w: 900, h: 760, view: BLD });
    fadeIn(tl, pv.box, 0, 0.3);
    const [x0, y0, x1, y1] = D.bbox;
    const g = pv.g('cheat');
    const big = svgEl('rect', { x: x0, y: y0, width: x1 - x0, height: y1 - y0, fill: ORANGE, 'fill-opacity': 0.3, stroke: ORANGE, 'stroke-width': 12 }, g);
    const dots = [];
    for (let i = 0; i < 31; i++) for (let j = 0; j < 31; j++)
      dots.push(svgEl('circle', { cx: x0 + (x1 - x0) * i / 30, cy: y0 + (y1 - y0) * j / 30, r: 9, fill: ORANGE }, g));
    const ring = svgEl('rect', { x: x0, y: y0, width: x1 - x0, height: y1 - y0, fill: 'none', stroke: ORANGE, 'stroke-width': 60, 'stroke-opacity': 0.8 }, g);
    const ex = D.exploits;
    const steps = [
      [big, 'One giant room', ex['one giant room']],
      [dots, '961 doors, windows, fixtures', ex['door/window/fixture spam (961 each)']],
      [ring, 'Thick wall around the building', ex['thick ring wall around the building']],
    ];
    const name = div(root, 'abs', 'left:1100px;top:250px;width:700px;font-size:44px;font-weight:600;letter-spacing:-0.02em;', '');
    const sc = div(root, 'abs score o', 'left:1100px;top:330px;font-size:220px;', '');
    div(root, 'abs label', 'left:1104px;top:200px;', 'exploit');
    steps.forEach(([els, label, v], i) => {
      const at = 0.4 + i * 2.2;
      const arr = Array.isArray(els) ? els : [els];
      tl.fromTo(arr, { opacity: 0 }, { opacity: 1, duration: 0.25, stagger: arr.length > 1 ? { amount: 0.5, from: 'random' } : 0 }, at);
      tl.call(() => { name.textContent = label; }, null, at);
      countUp(tl, sc, v, at + 0.3, { dur: 0.8, decimals: 3, from: 1 });
      if (i < steps.length - 1) tl.to(arr, { opacity: 0, duration: 0.25 }, at + 2.0);
    });
    tl.call(() => { name.textContent = ''; }, null, 0);
    const foot = div(root, 'abs', 'left:1100px;top:640px;width:720px;display:flex;flex-direction:column;gap:14px;font-size:30px;',
      `<div style="display:flex;justify-content:space-between;"><span class="m">Best cheat</span><b class="mono">${Math.max(...Object.values(ex).filter(v => v < 0.5)).toFixed(3)}</b></div>
       <div style="display:flex;justify-content:space-between;"><span class="m">A quarter of honest work</span><b class="mono">${R('stop early (25').reward.toFixed(3)}</b></div>
       <div style="display:flex;justify-content:space-between;"><span class="m">Do nothing</span><b class="mono">0.000</b></div>`);
    fadeIn(tl, foot, 6.6, 0.5);
  },
},

// ───────────────────────────── 8 · reproducible: a real terminal session
{
  id: 'repro', title: 'Reproducible', dur: 13, theme: 'dark',
  vo: 'And it’s reproducible. Everything runs in Harbor, with OpenCode, over MCP. A real playthrough is logged with its verifier score, and one command reproduces every number.',
  build(root, tl) {
    const win = div(root, 'abs', 'left:180px;top:130px;width:1560px;height:800px;border-radius:22px;background:#0A0A0B;box-shadow:0 0 0 1.5px #2A2A2E,0 40px 120px rgba(0,0,0,.6);overflow:hidden;');
    tl.fromTo(win, { opacity: 0, y: 60, scale: 0.96 }, { opacity: 1, y: 0, scale: 1, duration: 0.7, ease: 'expo.out' }, 0);
    const bar = div(win, 'abs', 'left:0;right:0;top:0;height:56px;background:#18181B;display:flex;align-items:center;gap:10px;padding:0 22px;');
    ['#FF5F57', '#FEBC2E', '#28C840'].forEach(c => div(bar, '', `width:16px;height:16px;border-radius:50%;background:${c};`));
    div(bar, 'mono', 'margin-left:20px;font-size:18px;color:#8C8C93;', 'blueprint-lab — harbor');
    const body = div(win, 'abs mono', 'left:40px;top:84px;right:40px;font-size:29px;line-height:1.7;color:#D4D4D8;white-space:pre;');
    const L = (cls, color) => div(body, '', `color:${color || '#D4D4D8'};min-height:1.7em;${cls || ''}`);
    const rows = [
      ['$ harbor run -p ./harbor_task -a opencode -m google/gemini-3.1-pro-preview', 0.9, 2.7, '#F4F2EE'],
      ['  task    afterquery/blueprint-schematic-site279', 3.6, 1.2, '#8C8C93'],
      ['  agent   opencode · gemini-3.1-pro-preview · 8 MCP tools', 4.4, 1.4, '#8C8C93'],
      ['  submit  88 walls · 20 rooms · 23 doors · 12 fixtures', 5.6, 1.4, '#8C8C93'],
      ['  verifier ✓ wrote reward.txt', 6.9, 1.0, '#1FA463'],
    ];
    rows.forEach(([txt, at, dur, col]) => {
      const el = L('', col);
      typeText(tl, el, txt, at, { cps: txt.length / dur });
    });
    const rew = div(body, 'disp', `font-size:120px;margin-top:10px;color:${ORANGE};`, '');
    rew.style.whiteSpace = 'nowrap';
    countUp(tl, rew, 0.616, 8.0, { dur: 1.2, decimals: 3, prefix: 'reward  ' });
    tl.fromTo(rew, { opacity: 0, scale: 0.9, transformOrigin: 'left center' }, { opacity: 1, scale: 1, duration: 0.3, immediateRender: false }, 8.0);
    const cmd = L('', '#F4F2EE'); cmd.style.marginTop = '14px';
    typeText(tl, cmd, '$ python -m blueprint_env.evaluate   # one command, every number', 10.0, { cps: 34 });
  },
},

// ───────────────────────────── 9 · close: the reference solver draws the schematic while the line is wiped in
{
  id: 'end', title: 'End card', dur: 9, theme: 'dark',
  vo: 'Blueprint to Schematic. Agents can see the drawing. Now let’s teach them to measure it.',
  build(root, tl) {
    const pv = planView(root, { x: 960, y: 0, w: 960, h: 1080, view: BLD });
    pv.box.style.borderRadius = '0';
    tl.fromTo(pv.box, { opacity: 0 }, { opacity: 1, duration: 0.6 }, 0);
    const rs = D.ref.schematic;
    pv.g('walls').setAttribute('opacity', 0.55);
    const w = drawWalls(pv.g('walls'), rs.walls, BLUE, { opacity: 1 });
    tl.fromTo(w, { opacity: 0 }, { opacity: 1, duration: 0.2, stagger: { amount: 1.8, from: 'random' } }, 0.8);
    const rr = drawRooms(pv.g('rooms'), rs.rooms, BLUE, { fill: 0.16, width: 4 });
    drawIn(tl, rr, 2.4, { dur: 0.7, stagger: 0.08 });
    popIn(tl, drawSegs(pv.g('doors'), rs.doors, GREEN, 10), 3.6, { stagger: 0.03, y: 0, scale: 0.4 });

    const a = div(root, 'abs disp', 'left:90px;top:300px;font-size:92px;width:820px;', 'Agents can see<br>the drawing.');
    const b = div(root, 'abs disp', 'left:90px;top:520px;font-size:92px;width:820px;', 'Now let’s teach<br>them to <span class="serif o">measure</span> it.');
    wipe(tl, a, 0.6); wipe(tl, b, 2.2);
    const logo = div(root, 'abs disp', 'left:90px;top:230px;font-size:76px;width:820px;opacity:0;', 'Blueprint <span class="o">→</span> Schematic');
    tl.to([a, b], { opacity: 0, x: -60, duration: 0.5, ease: 'power2.in' }, 5.2);
    tl.fromTo(logo, { opacity: 0, x: 60 }, { opacity: 1, x: 0, duration: 0.7, ease: 'expo.out', immediateRender: false }, 5.8);
    const team = div(root, 'abs label', 'left:94px;top:420px;font-size:26px;width:800px;', 'Blueprint Lab · Junction 2026 · Break the Agent');
    fadeIn(tl, team, 6.6);
    const cmd = div(root, 'abs mono', 'left:94px;top:520px;font-size:30px;color:#F4F2EE;', '');
    typeText(tl, cmd, '$ python -m blueprint_env.evaluate', 7.0, { cps: 30 });
  },
},

];
