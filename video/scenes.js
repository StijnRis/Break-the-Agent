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
// media/intro.mp4 = WhatsApp clip trimmed to 2.2 s–37.6 s (starts mid-jump). Times below are seconds in the cut (original − 2.2).
{
  id: 'intro', title: 'Intro', dur: 35.4, clip: 'intro.mp4', clipAudio: true, noTTS: true,
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

    // cover: this is the very first frame (also exported as cover.png), it fades out into the clip
    {
      const cv = div(root, 'abs', 'inset:0;background:#0C0C0D;z-index:30;');
      const cp = planView(cv, { x: 1010, y: 130, w: 800, h: 820, view: BLD });
      const rs = D.ref.schematic;
      cp.g('walls').setAttribute('opacity', 1);
      drawRooms(cp.g('rooms'), rs.rooms, BLUE, { fill: 0.14, width: 5 });
      drawSegs(cp.g('doors'), rs.doors, GREEN, 10);
      div(cv, 'abs disp', 'left:110px;top:290px;font-size:122px;width:900px;white-space:nowrap;color:#F4F2EE;', 'Drawing<span class="o">Sense</span>');
      div(cv, 'abs serif o', 'left:116px;top:610px;font-size:62px;width:860px;line-height:1.1;', 'Can an AI agent read a floor plan?');
      div(cv, 'abs mono', 'left:116px;bottom:90px;font-size:26px;color:#8C8C93;', 'DrawingSense · Junction 2026 · Break the Agent');
      tl.fromTo(cv, { opacity: 1 }, { opacity: 0, duration: 0.45, ease: 'power1.in', immediateRender: true }, 0.4);
    }

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

// ───────────────────────────── 2 · by hand: problem, then see / calibrate / measure (timed to the voiceover)
// voiceover timestamps: looks easy 1.2 · isn’t 3.5 · see the walls 5.1 · find the scale 6.0 · measure every room 7.0
{
  id: 'measure', title: 'By hand', dur: 8.9, theme: 'light',
  vo: 'Reading a floor plan looks easy. For an AI agent, it isn’t: it has to see the walls, find the scale, and measure every room.',
  build(root, tl) {
    const truth = D.gt.m_per_px;
    const BX = 310, BY = 50, BW = 1300, BH = 800;       // one stage for all three beats, so nothing jumps around
    const boxes = [
      planView(root, { x: BX, y: BY, w: BW, h: BH, view: BLD }),
      planView(root, { x: BX, y: BY, w: BW, h: BH, view: [1560, 1400, 2440, 1752] }),
      planView(root, { x: BX, y: BY, w: BW, h: BH, view: [1030, 985, 1430, 1255] }),
    ];
    const [C, A, B] = boxes;
    const cuts = [0, 6.0, 7.0];                          // when each view takes over
    boxes.forEach((b, i) => {
      tl.set(b.box, { opacity: i === 0 ? 1 : 0 }, 0);
      if (i > 0) { tl.set(b.box, { opacity: 1 }, cuts[i]); tl.set(boxes[i - 1].box, { opacity: 0 }, cuts[i]); }
    });
    tl.fromTo(C.box, { opacity: 0 }, { opacity: 1, duration: 0.5 }, 0);

    // ---- “Reading a floor plan looks easy. For an AI agent, it isn’t.”: a scan line finds questions
    {
      const vw = BLD[2] - BLD[0], vh = BLD[3] - BLD[1], k = Math.min(BW / vw, BH / vh);
      const sx = px => BX + BW / 2 + (px - (BLD[0] + BLD[2]) / 2) * k, sy = py => BY + BH / 2 + (py - (BLD[1] + BLD[3]) / 2) * k;
      const cen = r => [r.polygon.reduce((a, p) => a + p[0], 0) / r.polygon.length, r.polygon.reduce((a, p) => a + p[1], 0) / r.polygon.length];
      const S0 = 2.1, S1 = 4.3;
      const line = div(root, 'abs', `left:${BX}px;top:${BY}px;width:6px;height:${BH}px;background:${ORANGE};box-shadow:0 0 40px 10px rgba(255,91,31,.55);opacity:0;`);
      tl.set(line, { opacity: 1 }, S0);
      tl.fromTo(line, { x: 0 }, { x: BW, duration: S1 - S0, ease: 'none' }, S0);
      tl.to(line, { opacity: 0, duration: 0.2 }, S1);
      const qs = ['wall?', 'which room?', 'scale?', 'door?', 'how big?', 'where?', 'wall?', 'how big?'], tagEls = [];
      D.gt.rooms.slice(0, 8).forEach((r, i) => {
        const [cx, cy] = cen(r), x = sx(cx), y = sy(cy), t = S0 + (x - BX) / BW * (S1 - S0);
        const tag = div(root, 'abs mono', `left:${x - 70}px;top:${y - 24}px;padding:8px 16px;border-radius:999px;background:${ORANGE};color:#111;font-size:26px;font-weight:600;white-space:nowrap;opacity:0;`, qs[i % qs.length]);
        tagEls.push(tag);
        tl.fromTo(tag, { opacity: 0, scale: 0.2, y: 20 }, { opacity: 1, scale: 1, y: 0, duration: 0.35, ease: 'back.out(2.2)', immediateRender: false }, t);
      });
      tl.to(tagEls, { opacity: 0, scale: 0.5, duration: 0.25, stagger: 0.02 }, 4.6);
      const band = div(root, 'abs', `left:${BX + 80}px;top:${BY + BH - 120}px;width:${BW - 160}px;padding:22px 44px;border-radius:22px;background:${INK};box-shadow:0 16px 60px rgba(0,0,0,.4);`);
      const l1 = div(band, 'disp', 'font-size:64px;color:#F4F2EE;', '');
      const l2 = div(band, 'disp', 'font-size:64px;position:absolute;left:44px;top:22px;', '<span class="serif o"></span>');
      tl.fromTo(band, { y: 120, opacity: 0 }, { y: 0, opacity: 1, duration: 0.4, ease: 'expo.out' }, 0.6);
      typeText(tl, l1, 'Looks easy.', 1.2, { cps: 14 });
      tl.to(l1, { opacity: 0, duration: 0.12 }, 2.05);
      tl.set(l2, { opacity: 0 }, 0); tl.set(l2, { opacity: 1 }, 2.1);
      typeText(tl, l2.firstChild, 'For an agent, it isn’t.', 2.1, { cps: 17 });
      tl.to(band, { opacity: 0, y: 60, duration: 0.35 }, 4.5);
    }

    // one big word per beat, always in the same spot
    const word = (w, at, until) => {
      const e = div(root, 'abs disp', `left:80px;top:50px;font-size:88px;color:${INK};opacity:0;`, w);
      tl.set(e, { opacity: 1 }, at); tl.set(e, { opacity: 0 }, until);
    };
    word('See.', 4.9, 6.0); word('Calibrate.', 6.0, 7.0); word('Measure.', 7.0, 8.9);

    // ---- See: a pencil traces an interior wall, the walls fill in
    const gC = C.g('pencil');
    const wl = svgEl('line', { x1: 1092, y1: 915, x2: 1092, y2: 1215, stroke: ORANGE, 'stroke-width': 18, 'stroke-linecap': 'round' }, gC);
    wl.style.strokeDasharray = 300;
    const pen = svgEl('g', {}, gC);
    svgEl('polygon', { points: '0,0 -16,-50 16,-50', fill: '#E8B98A', stroke: INK, 'stroke-width': 4 }, pen);
    svgEl('polygon', { points: '-16,-50 16,-50 16,-260 -16,-260', fill: '#F5C542', stroke: INK, 'stroke-width': 4 }, pen);
    svgEl('polygon', { points: '-16,-260 16,-260 16,-285 -16,-285', fill: '#E5302A', stroke: INK, 'stroke-width': 4 }, pen);
    svgEl('polygon', { points: '0,0 -5,-16 5,-16', fill: INK }, pen);
    gsap.set(pen, { svgOrigin: '0 0' });                // rotate around the pencil tip so the tip stays on the line
    tl.fromTo(wl, { strokeDashoffset: 300 }, { strokeDashoffset: 0, duration: 0.7, ease: 'none', immediateRender: false }, 5.0);
    tl.fromTo(pen, { x: 1092, y: 915, rotation: 28, opacity: 0 }, { x: 1092, y: 1215, rotation: 28, opacity: 1, duration: 0.7, ease: 'none', immediateRender: false }, 5.0);
    tl.to(pen, { opacity: 0, duration: 0.15 }, 5.75);
    C.g('walls').setAttribute('opacity', 1);
    drawIn(tl, drawRooms(C.g('rooms'), D.ref.schematic.rooms, BLUE, { fill: 0.14, width: 6 }), 5.45, { dur: 0.35, stagger: 0.03 });

    // ---- Calibrate: tap “1:100”, read the scale
    const gA = A.g('tap');
    const ring = svgEl('ellipse', { cx: 1928, cy: 1546, rx: 85, ry: 32, fill: 'none', stroke: ORANGE, 'stroke-width': 8 }, gA);
    tl.fromTo(ring, { opacity: 0, scale: 2.4, svgOrigin: '1928 1546' }, { opacity: 1, scale: 1, svgOrigin: '1928 1546', duration: 0.35, ease: 'back.out(2)', immediateRender: false }, 6.15);
    [0, 0.25].forEach(d => {
      const rp = svgEl('circle', { cx: 1928, cy: 1546, r: 10, fill: 'none', stroke: ORANGE, 'stroke-width': 7, opacity: 0 }, gA);
      tl.fromTo(rp, { attr: { r: 10 }, opacity: 0.9 }, { attr: { r: 130 }, opacity: 0, duration: 0.5, ease: 'power2.out', immediateRender: false }, 6.5 + d);
    });
    const sc = div(root, 'abs mono', `left:${BX}px;top:${BY + BH + 20}px;width:${BW}px;text-align:center;font-size:44px;font-weight:600;color:${INK};opacity:0;`, `1 : 100 <span class="o">→</span> ${truth.toFixed(4)} m / px`);
    tl.set(sc, { opacity: 1 }, 6.55); tl.set(sc, { opacity: 0 }, 7.0);

    // ---- Measure: a ruler across a room, the length counts up
    const gB = B.g('ruler');
    const ruler = svgEl('g', {}, gB);
    svgEl('rect', { x: 1072, y: 1050, width: 310, height: 34, fill: '#F2D26B', stroke: INK, 'stroke-width': 2.5, rx: 3 }, ruler);
    for (let k = 0; k <= 30; k++) svgEl('line', { x1: 1072 + k * 10 + 5, y1: 1050, x2: 1072 + k * 10 + 5, y2: 1050 + (k % 5 === 0 ? 20 : 11), stroke: INK, 'stroke-width': 2 }, ruler);
    tl.fromTo(ruler, { x: -520, opacity: 0 }, { x: 0, opacity: 1, duration: 0.6, ease: 'expo.out', immediateRender: false }, 7.05);
    const dim = svgEl('line', { x1: 1092, y1: 1105, x2: 1092, y2: 1105, stroke: ORANGE, 'stroke-width': 6, 'stroke-linecap': 'round' }, gB);
    const capL = svgEl('line', { x1: 1092, y1: 1090, x2: 1092, y2: 1120, stroke: ORANGE, 'stroke-width': 6, 'stroke-linecap': 'round' }, gB);
    const capR = svgEl('line', { x1: 1362, y1: 1090, x2: 1362, y2: 1120, stroke: ORANGE, 'stroke-width': 6, 'stroke-linecap': 'round' }, gB);
    tl.fromTo(dim, { attr: { x2: 1092 } }, { attr: { x2: 1362 }, duration: 0.8, ease: 'power2.inOut', immediateRender: false }, 7.6);
    tl.fromTo([capL, capR], { opacity: 0 }, { opacity: 1, duration: 0.1, immediateRender: false }, 7.6);
    const m = div(root, 'abs score o', 'left:1640px;top:480px;font-size:72px;opacity:0;', '');
    countUp(tl, m, 270 * truth, 7.6, { dur: 0.8, decimals: 2, suffix: ' m' });
    tl.set(m, { opacity: 1 }, 7.6);
  },
},

// ───────────────────────────── 3 · the environment: tools orbit the drawing, then three things are taken away
{
  id: 'machine', title: 'The setup', dur: 9.0, theme: 'light',
  vo: 'So we built DrawingSense. One drawing, eight tools. No shell. No code. Just spatial reasoning.',
  build(root, tl) {
    const CX = 960, CY = 560;
    const ring = div(root, 'abs', 'inset:0;');
    const pv = planView(ring, { x: CX - 260, y: CY - 220, w: 520, h: 440, view: BLD });
    tl.fromTo(pv.box, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.9, ease: 'expo.out' }, 0);

    // “So we built DrawingSense.”
    const ttl = div(root, 'abs disp', `left:${CX}px;top:${CY}px;font-size:96px;color:${INK};background:#fff;padding:20px 48px;border-radius:24px;box-shadow:0 24px 80px rgba(17,17,19,.18);white-space:nowrap;`, 'Drawing<span class="o">Sense</span>');
    gsap.set(ttl, { xPercent: -50, yPercent: -50 });
    tl.fromTo(ttl, { opacity: 0, scale: 0.8 }, { opacity: 1, scale: 1, duration: 0.5, ease: 'back.out(1.8)' }, 0.7);
    tl.to(ttl, { opacity: 0, scale: 1.1, duration: 0.35 }, 2.1);
    const svg = svgEl('svg', { width: 1920, height: 1080, style: 'position:absolute;left:0;top:0;' }, ring);
    const tools = ['view_region', 'estimate_scale', 'read_room_labels', 'segment_rooms', 'measure_area', 'preview_schematic', 'get_task', 'submit_schematic'];
    tools.forEach((name, i) => {
      const a = -Math.PI / 2 + i * 2 * Math.PI / tools.length;
      const x = CX + Math.cos(a) * 720, y = CY + Math.sin(a) * 390;
      const ex = CX + Math.cos(a) * 270, ey = CY + Math.sin(a) * 240; // line starts at the plan's edge
      const ln = svgEl('line', { x1: ex, y1: ey, x2: x, y2: y, stroke: '#C9C4B8', 'stroke-width': 3, 'stroke-dasharray': '10 8' }, svg);
      const len = Math.hypot(x - ex, y - ey);
      const dot = svgEl('circle', { cx: ex, cy: ey, r: 9, fill: ORANGE, opacity: 0 }, svg);
      const t0 = 2.2 + i * 0.2;
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
    tl.to(ring, { opacity: 0.12, duration: 0.4 }, 4.4);
    const items = [['$ bash', 4.6], ['import numpy', 5.5], ['answer_key.json', 6.1]];
    items.forEach(([txt, t], i) => {
      const y = 330 + i * 150;
      const chip = div(root, 'abs mono', `left:${CX}px;top:${y}px;font-size:68px;font-weight:600;color:${INK};padding:18px 40px;border-radius:20px;background:#fff;box-shadow:0 14px 40px rgba(17,17,19,.12);white-space:nowrap;opacity:0;`, txt);
      const strike = div(root, 'abs', `left:${CX - 330}px;top:${y + 68}px;width:660px;height:10px;border-radius:5px;background:#E5302A;transform-origin:left center;`);
      gsap.set(strike, { scaleX: 0 });
      gsap.set(chip, { xPercent: -50 });
      tl.fromTo(chip, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.4, ease: 'expo.out', immediateRender: false }, t);
      tl.to(strike, { scaleX: 1, duration: 0.3, ease: 'power3.out' }, t + 0.35);
    });
    const fin = div(root, 'abs serif o', 'left:0;right:0;top:800px;text-align:center;font-size:100px;opacity:0;', 'Just spatial reasoning.');
    tl.fromTo(fin, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.7, ease: 'expo.out', immediateRender: false }, 6.8);
  },
},

// ───────────────────────────── 3b · how it is scored: the reward rubric as one 100 % bar
{
  id: 'rubric', title: 'Scoring', dur: 8.4, theme: 'dark',
  vo: 'Walls and rooms count twenty-five percent each, doors and windows fifteen, fixtures and areas ten, with a speed multiplier.',
  build(root, tl) {
    const h = div(root, 'abs disp', 'left:120px;top:130px;font-size:96px;width:1700px;', 'Scored on <span class="serif o">geometry.</span>');
    wipe(tl, h, 0.2, 0.8);
    const parts = [
      ['Walls', 25, BLUE, 'Mask F1 at 15 / 30 / 60 cm'],
      ['Rooms', 25, '#7A4DFF', 'Polygon IoU 0.5–0.9, half credit if the label is wrong'],
      ['Doors', 15, GREEN, 'Midpoint distance: full ≤ 20 cm, 0 at 1 m'],
      ['Windows', 15, '#12A3A3', 'Same as doors'],
      ['Fixtures', 10, ORANGE, 'Same type, full ≤ 25 cm, 0 at 1.5 m'],
      ['Areas', 10, '#C2415C', 'Within 5 % full, 0 at 30 % error'],
    ];
    const X0 = 120, W = 1680, Y = 400, H = 170;
    let x = X0;
    div(root, 'abs', `left:${X0}px;top:${Y}px;width:${W}px;height:${H}px;border-radius:20px;background:#161618;`);
    parts.forEach(([name, w, color, how], i) => {
      const pw = W * w / 100;
      const seg = div(root, 'abs', `left:${x}px;top:${Y}px;width:${pw - 6}px;height:${H}px;border-radius:16px;background:${color};overflow:hidden;transform-origin:left center;`,
        `<div style="padding:18px 22px;"><div style="font-size:30px;font-weight:700;letter-spacing:-0.02em;">${name}</div><div class="score" style="font-size:78px;margin-top:4px;">${w}%</div></div>`);
      const at = [0.1, 0.5, 2.1, 2.5, 4.1, 4.5][i];
      tl.fromTo(seg, { scaleX: 0, opacity: 0 }, { scaleX: 1, opacity: 1, duration: 0.55, ease: 'expo.out' }, at);
      x += pw;
    });
    const sp = div(root, 'abs pill', 'left:120px;top:850px;font-size:30px;padding:16px 30px;', 'Speed <span class="o">×0.90–1.00</span>');
    tl.fromTo(sp, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: 'back.out(1.6)', immediateRender: false }, 5.2);
  },
},

// ───────────────────────────── 4 · side-by-side replay (the money shot)
{
  id: 'demo', title: 'Replay', dur: 11.8, warp: 2.066, theme: 'light',
  vo: 'Watch Gemini work. It zooms, second-guesses its scale, then draws every room by hand. Our plain computer-vision solver traces the walls. Point five one against point zero four.',
  build(root, tl) {
    const W = 860, H = 640, Y = 100;
    const tagL = div(root, 'abs tag', `left:80px;top:52px;color:${INK};`, `<i style="background:${ORANGE}"></i>Gemini 3.1 Pro`);
    const tagR = div(root, 'abs tag', `left:980px;top:52px;color:${INK};`, `<i style="background:${BLUE}"></i>Our reference`);
    const L = planView(root, { x: 80, y: Y, w: W, h: H, view: FULL });
    const Rv = planView(root, { x: 980, y: Y, w: W, h: H, view: FULL });
    fadeIn(tl, [tagL, tagR, L.box, Rv.box], 0, 0.5);

    // ---- right: the reference
    tl.to(Rv.svg, { attr: { viewBox: vb(BLD) }, duration: 1.4, ease: 'power3.inOut' }, 1.2);
    const rs = D.ref.schematic;
    Rv.g('walls').setAttribute('opacity', 1); // flat colour where wall boxes overlap
    const rr = drawRooms(Rv.g('rooms'), rs.rooms, BLUE, { fill: 0.14, width: 5 });
    drawIn(tl, rr, 3.0, { dur: 0.7, stagger: 0.1 });
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
    typeText(tl, line1, '“1:100 → 0.0169 m/px”', scaleAt + 0.2, { cps: 40 });
    const line2 = div(th, '', `color:${ORANGE};margin-top:6px;`, '');
    typeText(tl, line2, '“Wait, check the scale bar.”', scaleAt + 1.3, { cps: 40 });
    tl.to(th, { opacity: 0, duration: 0.3 }, scaleAt + 3.6);

    const th2 = div(root, 'abs thought', `left:120px;top:${Y + 330}px;opacity:0;`, who);
    const l3 = div(th2, '', '', '');
    tl.fromTo(th2, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.3 }, tEnd - 1.2);
    typeText(tl, l3, '“I’ll draw the rooms by hand.”', tEnd - 1.0, { cps: 50 });
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
  id: 'gap', title: 'The gap', dur: 6.9, theme: 'dark',
  vo: 'Across fifteen unseen plans, Gemini scores point three four. Our solver: point five nine.',
  build(root, tl) {
    const h = div(root, 'abs disp', 'left:120px;top:170px;font-size:104px;width:1700px;', 'Our solver beats<br>the <span class="serif o">frontier.</span>');
    wipe(tl, h, 0.3, 0.9);
    const rows = [
      ['Our reference', R('reference').reward, BLUE, ''],
      ['Gemini 3.1 Pro', R('agent: gemini-3.1-pro-preview').reward, ORANGE, ''],
    ];
    const MAXW = 1120;
    rows.forEach((r, i) => {
      const y = 520 + i * 160;
      div(root, 'abs', `left:120px;top:${y + 4}px;width:520px;font-size:34px;font-weight:600;color:#F4F2EE;`, r[0]);
      if (r[3]) div(root, 'abs mono', `left:120px;top:${y + 50}px;font-size:20px;color:#8C8C93;`, r[3]);
      div(root, 'abs', `left:660px;top:${y}px;width:${MAXW}px;height:76px;border-radius:12px;background:#161618;`);
      const bar = div(root, 'abs', `left:660px;top:${y}px;width:${Math.max(8, r[1] * MAXW)}px;height:76px;border-radius:12px;background:${r[2]};transform-origin:left center;`);
      const val = div(root, 'abs score', `left:${680 + Math.max(8, r[1] * MAXW)}px;top:${y + 8}px;font-size:60px;color:#F4F2EE;`, '');
      tl.fromTo(bar, { scaleX: 0 }, { scaleX: 1, duration: 1.1, ease: 'expo.out' }, 1.8 + i * 0.7);
      countUp(tl, val, r[1], 1.8 + i * 0.7, { dur: 1.1, decimals: 3 });
      r.el = bar;
    });
  },
},

// ───────────────────────────── 6 · why Gemini fails: all eight failure modes on one board, each with a tiny animation of how it goes wrong
{
  id: 'errors', title: 'Why it fails', dur: 10.6, theme: 'dark',
  vo: 'Eight ways it fails. Two matter most: it quits early, and it skips the walls. Then wrong scale, missed doors, timeouts, and more.',
  build(root, tl) {
    const RED = '#E5302A', DIM = '#8C8C93';
    // card(x, y, w, h, title, stat, important) -> the card element
    const card = (x, y, w, h, title, stat, hot, at) => {
      const c = div(root, 'abs', `left:${x}px;top:${y}px;width:${w}px;height:${h}px;border-radius:26px;background:#161618;box-shadow:inset 0 0 0 ${hot ? 4 : 1.5}px ${hot ? ORANGE : '#2A2A2E'};overflow:hidden;`);
      div(c, 'abs disp', `left:${hot ? 34 : 20}px;top:${hot ? 26 : 18}px;font-size:${hot ? 52 : 29}px;width:${w - 60}px;line-height:1.0;color:${hot ? '#fff' : '#F4F2EE'};`, title);
      div(c, 'abs mono', `left:${hot ? 34 : 20}px;bottom:${hot ? 24 : 16}px;width:${w - (hot ? 68 : 40)}px;font-size:${hot ? 30 : 22}px;line-height:1.3;color:${hot ? '#F4F2EE' : DIM};`, stat);
      if (hot) div(c, 'abs mono', `right:26px;top:30px;font-size:20px;font-weight:600;padding:6px 14px;border-radius:999px;background:${ORANGE};color:#111;`, 'MOST IMPORTANT');
      tl.fromTo(c, { opacity: 0, y: 40, scale: 0.94 }, { opacity: 1, y: 0, scale: 1, duration: 0.5, ease: 'expo.out' }, at);
      return c;
    };
    const dot = (p, x, y, r, color, extra = '') => div(p, 'abs', `left:${x - r}px;top:${y - r}px;width:${2 * r}px;height:${2 * r}px;border-radius:50%;background:${color};${extra}`);
    const T = { quit: 2.2, walls: 3.4, small: 5.0 };

    // ---------- 1 · quits early
    const c1 = card(50, 50, 900, 440, 'Quits early', 'Gives up after a few calls.<br>4 of 8 scored 0.', true, T.quit);
    const calls = [];
    for (let i = 0; i < 4; i++) calls.push(div(c1, 'abs mono', `left:${34 + i * 96}px;top:128px;width:84px;height:56px;border-radius:14px;border:2px solid #3A3A40;font-size:20px;display:flex;align-items:center;justify-content:center;color:${DIM};`, i < 3 ? `call ${i + 1}` : 'submit'));
    calls.forEach((e, i) => tl.to(e, { backgroundColor: i < 3 ? '#3A2A22' : RED, borderColor: i < 3 ? ORANGE : RED, color: '#fff', duration: 0.2 }, T.quit + 0.6 + i * 0.3));
    const empty = div(c1, 'abs mono', `left:34px;top:210px;width:380px;height:130px;border-radius:14px;border:3px dashed ${RED};display:flex;align-items:center;justify-content:center;font-size:24px;color:${RED};opacity:0;`, 'empty schematic');
    tl.fromTo(empty, { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1, duration: 0.35, ease: 'back.out(2)' }, T.quit + 1.6);
    for (let i = 0; i < 8; i++) {
      const bad = i < 4, x = 470 + (i % 4) * 100, y = 130 + Math.floor(i / 4) * 120;
      const sq = div(c1, 'abs mono', `left:${x}px;top:${y}px;width:88px;height:100px;border-radius:14px;background:#26262b;font-size:18px;display:flex;align-items:center;justify-content:center;color:#F4F2EE;`, '…');
      tl.fromTo(sq, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.25, ease: 'back.out(2)' }, T.quit + 0.5 + i * 0.07);
      tl.call(() => { sq.textContent = bad ? '0.000' : 'ok'; sq.style.background = bad ? RED : '#1FA463'; }, null, T.quit + 1.7 + i * 0.08);
      tl.call(() => { sq.textContent = '…'; sq.style.background = '#26262b'; }, null, 0);
    }

    // ---------- 2 · skips walls
    const c2 = card(970, 50, 900, 440, 'Skips walls', 'Rooms, but no walls.<br>24 of 40 episodes.', true, T.walls);
    const pv = planView(c2, { x: 34, y: 92, w: 400, h: 190, view: BLD, bg: '#fff' });
    pv.box.style.borderRadius = '14px';
    const rr = drawRooms(pv.g('rooms'), D.agent.schematic.rooms, ORANGE, { fill: 0.16, width: 6 });
    drawIn(tl, rr, T.walls + 0.5, { dur: 0.5, stagger: 0.06 });
    const miss = D.gt.walls.map(w => svgEl('path', { d: polyPath(w), fill: 'none', stroke: RED, 'stroke-width': 10, 'stroke-dasharray': '22 14', opacity: 0 }, pv.g('miss')));
    tl.fromTo(miss, { opacity: 0 }, { opacity: 0.95, duration: 0.3, yoyo: true, repeat: 3 }, T.walls + 1.6);
    const mt = div(c2, 'abs mono', `left:34px;top:288px;font-size:20px;color:${RED};opacity:0;`, '✗ walls missing');
    tl.set(mt, { opacity: 1 }, T.walls + 1.7);
    [['with walls', 0.56, GREEN], ['no walls', 0.29, ORANGE]].forEach(([lab, v, col], i) => {
      const bx = 520 + i * 170;
      const bar = div(c2, 'abs', `left:${bx}px;top:${290 - v / 0.6 * 190}px;width:130px;height:${v / 0.6 * 190}px;border-radius:12px 12px 0 0;background:${col};transform-origin:bottom;`);
      div(c2, 'abs mono', `left:${bx - 10}px;top:294px;width:150px;text-align:center;font-size:18px;color:${DIM};`, lab);
      const val = div(c2, 'abs score', `left:${bx}px;top:${244 - v / 0.6 * 190}px;width:130px;text-align:center;font-size:46px;`, '');
      tl.fromTo(bar, { scaleY: 0 }, { scaleY: 1, duration: 0.7, ease: 'expo.out' }, T.walls + 1.0 + i * 0.4);
      countUp(tl, val, v, T.walls + 1.0 + i * 0.4, { dur: 0.7, decimals: 2 });
      tl.fromTo(val, { opacity: 0 }, { opacity: 1, duration: 0.2, immediateRender: false }, T.walls + 1.0 + i * 0.4);
    });

    // ---------- the six smaller ones
    const SW = 291, SY = 490, SH = 450;
    const sx = i => 50 + i * (SW + 14);
    const smalls = [
      ['Misses doors and windows', 'Finds ¼ of them.'],
      ['Wrong scale', '15 of 40 off by >10%.'],
      ['Large plans collapse', 'More rooms, less score.'],
      ['Timeouts', '5 of 45 never submit.'],
      ['Corrupted output', '149 turns without a tool call.'],
      ['High variance', 'Same plan, three runs.'],
    ];
    const S = smalls.map((s, i) => card(sx(i), SY, SW, SH, s[0], s[1], false, T.small + i * 0.45));
    const base = i => T.small + i * 0.45 + 0.3;

    // 3 doors and windows: real (green) vs. found by eye (orange), most of them off target
    {
      const c = S[0], real = [[60, 150], [140, 120], [215, 160], [90, 230], [180, 250], [235, 225], [50, 300], [150, 310]];
      real.forEach(([x, y], i) => { const d = dot(c, x, y + 5, 11, 'transparent', `border:4px solid ${GREEN};`); tl.fromTo(d, { opacity: 0, scale: 0 }, { opacity: 1, scale: 1, duration: 0.25, ease: 'back.out(2)' }, base(0) + i * 0.08); });
      const eye = [[60, 150], [215, 165], [120, 190], [30, 250], [200, 205], [260, 290], [110, 270], [170, 330], [75, 345], [245, 160]];
      eye.forEach(([x, y], i) => { const d = dot(c, x + (i > 1 ? 14 : 0), y + 5, 9, ORANGE); tl.fromTo(d, { opacity: 0, scale: 0 }, { opacity: 1, scale: 1, duration: 0.2, ease: 'back.out(2)' }, base(0) + 0.9 + i * 0.1); });
    }
    // 4 wrong scale: the same room, drawn 15 % too big
    {
      const c = S[1];
      const g = div(c, 'abs', `left:70px;top:170px;width:150px;height:110px;border:5px solid ${GREEN};border-radius:6px;`);
      const o = div(c, 'abs', `left:70px;top:170px;width:150px;height:110px;border:5px dashed ${ORANGE};border-radius:6px;background:rgba(255,91,31,.12);`);
      tl.fromTo(g, { opacity: 0 }, { opacity: 1, duration: 0.3 }, base(1));
      tl.fromTo(o, { opacity: 0, scale: 1 }, { opacity: 1, scale: 1.45, duration: 0.8, ease: 'elastic.out(1,0.5)' }, base(1) + 0.5);
      const rt = div(c, 'abs score o', 'left:20px;top:330px;font-size:44px;', '×1.41');
      tl.fromTo(rt, { opacity: 0 }, { opacity: 1, duration: 0.3 }, base(1) + 1.2);
    }
    // 5 large plans: the score falls as the plan grows
    {
      const c = S[2];
      [['≤20', 0.44, GREEN], ['>20', 0.22, ORANGE], ['116', 0.01, RED]].forEach(([lab, v, col], i) => {
        const h = Math.max(6, v / 0.5 * 190), bx = 28 + i * 86;
        const b = div(c, 'abs', `left:${bx}px;top:${330 - h}px;width:70px;height:${h}px;border-radius:10px 10px 0 0;background:${col};transform-origin:bottom;`);
        div(c, 'abs mono', `left:${bx - 6}px;top:340px;width:82px;text-align:center;font-size:16px;color:${DIM};`, lab);
        const val = div(c, 'abs mono', `left:${bx - 6}px;top:${330 - h - 28}px;width:82px;text-align:center;font-size:20px;color:#F4F2EE;`, v.toFixed(2));
        tl.fromTo(b, { scaleY: 0 }, { scaleY: 1, duration: 0.6, ease: 'expo.out' }, base(2) + i * 0.35);
        tl.fromTo(val, { opacity: 0 }, { opacity: 1, duration: 0.2 }, base(2) + i * 0.35 + 0.4);
      });
    }
    // 6 timeouts: the clock runs out, nothing is submitted
    {
      const c = S[3];
      const face = div(c, 'abs', `left:70px;top:150px;width:150px;height:150px;border-radius:50%;border:6px solid #F4F2EE;`);
      const hand = div(face, 'abs', `left:66px;top:18px;width:6px;height:58px;border-radius:3px;background:${ORANGE};transform-origin:50% 100%;`);
      tl.fromTo(hand, { rotation: 0 }, { rotation: 720, duration: 1.4, ease: 'power1.in' }, base(3));
      const x = div(c, 'abs disp', `left:0;right:0;top:320px;text-align:center;font-size:56px;color:${RED};opacity:0;`, '✗ no submit');
      tl.fromTo(x, { opacity: 0, scale: 2 }, { opacity: 1, scale: 1, duration: 0.25, ease: 'power4.in' }, base(3) + 1.4);
    }
    // 7 corrupted output: a tool call dissolves into noise
    {
      const c = S[4], lines = div(c, 'abs mono', `left:20px;top:150px;width:${SW - 40}px;font-size:18px;line-height:1.5;color:#F4F2EE;word-break:break-all;`, '');
      const good = 'call segment_rooms(seeds=[…])', bad = 'MALFORMED_FUNCTION_CALL', junk = '▓▒░#@%&§¤¶≈∆Ωµ';
      const o = { p: 0 };
      tl.fromTo(o, { p: 0 }, { p: 1, duration: 1.6, ease: 'none', immediateRender: false, onUpdate: () => {
        const n = Math.round(o.p * 40), seed = Math.floor(o.p * 60);
        let s = o.p < 0.35 ? good : '';
        if (o.p >= 0.35) for (let i = 0; i < 90; i++) s += junk[(i * 7 + seed * 3 + i * i) % junk.length];
        if (o.p > 0.8) s = bad;
        lines.style.color = o.p > 0.8 ? RED : '#F4F2EE';
        lines.textContent = s;
      } }, base(4));
    }
    // 8 high variance: three runs, same plan
    {
      const c = S[5];
      [[0.0, 'run 1'], [0.41, 'run 2'], [0.55, 'run 3']].forEach(([v, lab], i) => {
        const h = Math.max(6, v / 0.6 * 190), bx = 28 + i * 86;
        const b = div(c, 'abs', `left:${bx}px;top:${330 - h}px;width:70px;height:${h}px;border-radius:10px 10px 0 0;background:${ORANGE};transform-origin:bottom;`);
        div(c, 'abs mono', `left:${bx - 6}px;top:340px;width:82px;text-align:center;font-size:16px;color:${DIM};`, lab);
        const val = div(c, 'abs mono', `left:${bx - 6}px;top:${330 - h - 28}px;width:82px;text-align:center;font-size:20px;color:#F4F2EE;`, v.toFixed(2));
        tl.fromTo(b, { scaleY: 0 }, { scaleY: 1, duration: 0.5, ease: 'back.out(1.6)' }, base(5) + i * 0.3);
        tl.fromTo(val, { opacity: 0 }, { opacity: 1, duration: 0.2 }, base(5) + i * 0.3 + 0.3);
      });
    }
  },
},

// ───────────────────────────── 7 · exploits: six cheats at once, all score ~nothing
{
  id: 'cheat', title: 'Cheat (score)', dur: 4.8, theme: 'dark',
  vo: 'We tested many possible exploits. None scored above point one.',
  build(root, tl) {
    const ex = D.exploits, [x0, y0, x1, y1] = D.bbox, W = x1 - x0, H = y1 - y0;
    const panels = [
      ['One giant room', ex['one giant room'], g => svgEl('rect', { x: x0, y: y0, width: W, height: H, fill: ORANGE, 'fill-opacity': 0.35, stroke: ORANGE, 'stroke-width': 12 }, g)],
      ['Wall around the building', ex['wall = whole building box'], g => svgEl('rect', { x: x0, y: y0, width: W, height: H, fill: 'none', stroke: ORANGE, 'stroke-width': 26 }, g)],
      ['961 doors and windows', ex['door/window/fixture spam (961 each)'], g => { const a = []; for (let i = 0; i < 25; i++) for (let j = 0; j < 25; j++) a.push(svgEl('circle', { cx: x0 + W * i / 24, cy: y0 + H * j / 24, r: 11, fill: ORANGE }, g)); return a; }],
      ['A grid of rooms', ex['grid of rooms over the building (as many cells as rooms)'], g => { const a = []; for (let i = 0; i <= 5; i++) a.push(svgEl('line', { x1: x0 + W * i / 5, y1: y0, x2: x0 + W * i / 5, y2: y1, stroke: ORANGE, 'stroke-width': 8 }, g)); for (let j = 0; j <= 4; j++) a.push(svgEl('line', { x1: x0, y1: y0 + H * j / 4, x2: x1, y2: y0 + H * j / 4, stroke: ORANGE, 'stroke-width': 8 }, g)); return a; }],
      ['A thick ring wall', ex['thick ring wall around the building'], g => svgEl('rect', { x: x0 + 40, y: y0 + 40, width: W - 80, height: H - 80, fill: 'none', stroke: ORANGE, 'stroke-width': 90, 'stroke-opacity': 0.8 }, g)],
      ['Every fixture, stacked', ex['every fixture type stacked on every true fixture'], g => { const a = []; (D.gt.fixtures.length ? D.gt.fixtures : [{ x: x0 + W / 2, y: y0 + H / 2 }]).forEach(f => { for (let r = 1; r <= 6; r++) a.push(svgEl('circle', { cx: f.x, cy: f.y, r: 16 * r, fill: 'none', stroke: ORANGE, 'stroke-width': 8 }, g)); }); return a; }],
    ];
    const PW = 580, PH = 340;
    panels.forEach(([name, score, draw], i) => {
      const x = 60 + (i % 3) * 620, y = 50 + Math.floor(i / 3) * 430;
      const pv = planView(root, { x, y, w: PW, h: PH, view: BLD });
      const els = [].concat(draw(pv.g('cheat')));
      const cap = div(root, 'abs', `left:${x}px;top:${y + PH + 10}px;width:${PW}px;font-size:28px;font-weight:600;color:#F4F2EE;`, name);
      const sc = div(root, 'abs score o', `left:${x + PW - 250}px;top:${y + 14}px;width:230px;text-align:right;font-size:64px;text-shadow:0 2px 12px rgba(255,255,255,.9);opacity:0;`, '');
      const t = 0.3 + i * 0.35;
      tl.fromTo([pv.box, cap], { opacity: 0, y: 30, scale: 0.95 }, { opacity: 1, y: 0, scale: 1, duration: 0.4, ease: 'expo.out' }, t);
      tl.fromTo(els, { opacity: 0 }, { opacity: 1, duration: 0.3, stagger: els.length > 1 ? { amount: 0.4, from: 'random' } : 0, immediateRender: false }, t + 0.35);
      countUp(tl, sc, score, t + 0.5, { dur: 0.5, decimals: 3, from: 1 });
      tl.set(sc, { opacity: 1 }, t + 0.5);
    });
    const best = Math.max(...panels.map(p => p[1]));
    const foot = div(root, 'abs disp', 'left:0;right:0;top:870px;text-align:center;font-size:56px;opacity:0;', `Best exploit: <span class="o">${best.toFixed(3)}</span>`);
    tl.fromTo(foot, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.5, ease: 'expo.out', immediateRender: false }, 3.6);
  },
},

// ───────────────────────────── 8 · reproducible: a real terminal session
{
  id: 'repro', title: 'Reproducible', dur: 5.7, warp: 2.131, theme: 'dark',
  vo: 'And it’s reproducible. Harbor, OpenCode, MCP, and one command for every number.',
  build(root, tl) {
    const win = div(root, 'abs', 'left:180px;top:130px;width:1560px;height:800px;border-radius:22px;background:#0A0A0B;box-shadow:0 0 0 1.5px #2A2A2E,0 40px 120px rgba(0,0,0,.6);overflow:hidden;');
    tl.fromTo(win, { opacity: 0, y: 60, scale: 0.96 }, { opacity: 1, y: 0, scale: 1, duration: 0.7, ease: 'expo.out' }, 0);
    const bar = div(win, 'abs', 'left:0;right:0;top:0;height:56px;background:#18181B;display:flex;align-items:center;gap:10px;padding:0 22px;');
    ['#FF5F57', '#FEBC2E', '#28C840'].forEach(c => div(bar, '', `width:16px;height:16px;border-radius:50%;background:${c};`));
    div(bar, 'mono', 'margin-left:20px;font-size:18px;color:#8C8C93;', 'drawingsense — harbor');
    const body = div(win, 'abs mono', 'left:40px;top:84px;right:40px;font-size:29px;line-height:1.7;color:#D4D4D8;white-space:pre;');
    const L = (cls, color) => div(body, '', `color:${color || '#D4D4D8'};min-height:1.7em;${cls || ''}`);
    const rows = [
      ['$ harbor run -a opencode', 0.9, 1.6, '#F4F2EE'],
      ['  verifier ✓', 3.2, 0.6, '#1FA463'],
    ];
    rows.forEach(([txt, at, dur, col]) => {
      const el = L('', col);
      typeText(tl, el, txt, at, { cps: txt.length / dur });
    });
    const rew = L('', ORANGE);                       // the score is just another terminal line, same size as the rest
    typeText(tl, rew, 'reward  0.616', 4.2, { cps: 13 });
    const cmd = L('', '#F4F2EE'); cmd.style.marginTop = '14px';
    typeText(tl, cmd, '$ python -m blueprint_env.evaluate', 6.0, { cps: 28 });
  },
},

// ───────────────────────────── 9 · we also trained a small model: its loss went down (logs/modal_poc2.log)
{
  id: 'train', title: 'Training', dur: 5.9, theme: 'dark',
  vo: 'We trained two models. First, a proof of concept on a large LLM, and its loss went down.',
  build(root, tl) {
    const loss = [0.6886, 0.636, 0.5907, 0.5786, 0.5482, 0.5570, 0.5370, 0.5450, 0.5257, 0.515, 0.4578, 0.5178, 0.4793, 0.4682, 0.5095, 0.4496, 0.4403, 0.4248, 0.4799, 0.4207, 0.4358];
    const CX = 200, CY = 150, CW = 1100, CH = 700;
    const svg = svgEl('svg', { width: CW + 40, height: CH + 40, style: `position:absolute;left:${CX - 20}px;top:${CY - 20}px;overflow:visible;` }, root);
    [0, 0.5, 1].forEach(f => svgEl('line', { x1: 20, y1: 20 + f * CH, x2: 20 + CW, y2: 20 + f * CH, stroke: '#2A2A2E', 'stroke-width': 2 }, svg));
    const X = i => 20 + i / (loss.length - 1) * CW, Y = v => 20 + (1 - (v - 0.35) / (0.75 - 0.35)) * CH;
    const path = svgEl('path', { d: 'M' + loss.map((v, i) => `${X(i)} ${Y(v)}`).join('L'), fill: 'none', stroke: GREEN, 'stroke-width': 10, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, svg);
    const len = path.getTotalLength(); path.style.strokeDasharray = len; path.style.strokeDashoffset = len;
    const dot = svgEl('circle', { r: 16, fill: GREEN, cx: X(0), cy: Y(loss[0]) }, svg);
    const o = { p: 0 };
    tl.fromTo(o, { p: 0 }, { p: 1, duration: 3.1, ease: 'power1.inOut', immediateRender: false, onUpdate: () => {
      path.style.strokeDashoffset = len * (1 - o.p);
      const pt = path.getPointAtLength(len * o.p); dot.setAttribute('cx', pt.x); dot.setAttribute('cy', pt.y);
    } }, 1.3);
    const m1 = div(root, 'abs pill', 'left:200px;top:60px;font-size:28px;padding:14px 28px;', 'Model 1 · proof of concept · large LLM');
    tl.fromTo(m1, { opacity: 0, y: -20 }, { opacity: 1, y: 0, duration: 0.5, ease: 'expo.out' }, 1.3);
    const lv = div(root, 'abs score', `left:1400px;top:340px;font-size:190px;color:${GREEN};`, '');
    countUp(tl, lv, loss[loss.length - 1], 1.3, { dur: 3.1, decimals: 2, from: loss[0] });
    tl.fromTo(lv, { opacity: 0 }, { opacity: 1, duration: 0.3 }, 1.3);
    const cap = div(root, 'abs serif o', 'left:1400px;top:560px;font-size:80px;opacity:0;', 'loss went down');
    tl.fromTo(cap, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.6, ease: 'expo.out', immediateRender: false }, 4.4);
  },
},

// ───────────────────────────── 9b · the bigger picture: the same skill, Stoa's construction-drawing challenge
{
  id: 'stoa', title: 'Stoa', dur: 7.0, theme: 'light',
  vo: 'Second, a very small model, for Stoa’s challenge: verifiable answers about construction drawings.',
  build(root, tl) {
    const BX = 940, BY = 90, BW = 900, BH = 900;
    const pv = planView(root, { x: BX, y: BY, w: BW, h: BH, view: BLD });
    tl.fromTo(pv.box, { opacity: 0, x: 80 }, { opacity: 1, x: 0, duration: 0.7, ease: 'expo.out' }, 0);
    // chat on the left
    const pill = div(root, 'abs pill', 'left:110px;top:150px;font-size:26px;', 'Model 2 · very small · Stoa');
    tl.fromTo(pill, { opacity: 0, y: -20 }, { opacity: 1, y: 0, duration: 0.5, ease: 'expo.out' }, 0.7);
    const q = div(root, 'abs', `left:110px;top:300px;width:720px;padding:26px 34px;border-radius:30px 30px 8px 30px;background:${BLUE};color:#fff;font-size:44px;font-weight:600;letter-spacing:-0.02em;opacity:0;`, '');
    tl.fromTo(q, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.3, immediateRender: false }, 2.0);
    typeText(tl, q, 'Where is the stairwell?', 2.1, { cps: 22 });
    const a = div(root, 'abs', `left:110px;top:470px;width:720px;padding:26px 34px;border-radius:30px 30px 30px 8px;background:#fff;box-shadow:0 14px 44px rgba(17,17,19,.12);font-size:40px;font-weight:600;letter-spacing:-0.02em;opacity:0;`,
      `Vano scala 4.11 <span style="color:${GREEN};">✓</span>`);
    tl.fromTo(a, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.4, ease: 'back.out(1.6)', immediateRender: false }, 3.7);
    // highlight the answer on the plan
    const room = D.gt.rooms[11];
    const hl = drawRooms(pv.g('answer'), [room], ORANGE, { fill: 0.28, width: 12 });
    drawIn(tl, hl, 3.8, { dur: 0.7, stagger: 0 });
    tl.fromTo(hl, { opacity: 0.4 }, { opacity: 1, duration: 0.4, yoyo: true, repeat: 3, ease: 'sine.inOut' }, 4.6);
  },
},

// ───────────────────────────── 9 · close: the reference solver draws the schematic while the line is wiped in
{
  id: 'end', title: 'End card', dur: 3.8, warp: 2.25, theme: 'dark',
  vo: 'Agents can see the drawing. Now let’s teach them to measure it.',
  build(root, tl) {
    const pv = planView(root, { x: 960, y: 0, w: 960, h: 1080, view: BLD });
    pv.box.style.borderRadius = '0';
    tl.fromTo(pv.box, { opacity: 0 }, { opacity: 1, duration: 0.6 }, 0);
    const rs = D.ref.schematic;
    pv.g('walls').setAttribute('opacity', 1);
    const rr = drawRooms(pv.g('rooms'), rs.rooms, BLUE, { fill: 0.14, width: 5 });
    drawIn(tl, rr, 2.4, { dur: 0.7, stagger: 0.08 });
    popIn(tl, drawSegs(pv.g('doors'), rs.doors, GREEN, 10), 3.6, { stagger: 0.03, y: 0, scale: 0.4 });

    const a = div(root, 'abs disp', 'left:90px;top:300px;font-size:92px;width:820px;', 'Agents can see<br>the drawing.');
    const b = div(root, 'abs disp', 'left:90px;top:520px;font-size:92px;width:820px;', 'Now let’s teach<br>them to <span class="serif o">measure</span> it.');
    wipe(tl, a, 0.6); wipe(tl, b, 2.2);
    const logo = div(root, 'abs disp', 'left:90px;top:230px;font-size:76px;width:820px;opacity:0;', 'Drawing<span class="o">Sense</span>');
    tl.to([a, b], { opacity: 0, x: -60, duration: 0.5, ease: 'power2.in' }, 5.2);
    tl.fromTo(logo, { opacity: 0, x: 60 }, { opacity: 1, x: 0, duration: 0.7, ease: 'expo.out', immediateRender: false }, 5.8);
    const team = div(root, 'abs label', 'left:94px;top:420px;font-size:26px;width:800px;', 'DrawingSense · Junction 2026 · Break the Agent');
    fadeIn(tl, team, 6.6);
    const cmd = div(root, 'abs mono', 'left:94px;top:520px;font-size:30px;color:#F4F2EE;', '');
    typeText(tl, cmd, '$ python -m blueprint_env.evaluate', 7.0, { cps: 30 });
  },
},

];
