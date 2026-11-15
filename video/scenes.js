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

// ───────────────────────────── 1 · walk in (filmed)
{
  id: 'walkin', title: 'Walk in', dur: 12, clip: 'walkin.mp4', clipAudio: true,
  shot: 'Handheld: follow through a door to a table. Drop the printed A3 plan on it. Look up and say the line to camera.',
  vo: 'This is a construction drawing. Every renovation, every permit, every insurance claim starts with someone reading one. We wanted to know: can the best AI agents read it?',
  build(root, tl) {
    const sh = shade(root);
    const h = div(root, 'abs disp', 'left:120px;bottom:130px;font-size:132px;color:#fff;width:1500px;', 'Can an agent read<br>a floor plan?');
    fadeIn(tl, sh, 7.2, 0.6);
    slam(tl, h, 7.6, { stagger: 0.09 });
    const l = div(root, 'abs label', 'left:124px;bottom:90px;color:rgba(255,255,255,.7);', 'Blueprint → Schematic · Junction 2026');
    fadeIn(tl, l, 8.6);
  },
},

// ───────────────────────────── 2 · measure by hand (filmed)
{
  id: 'measure', title: 'By hand', dur: 13, clip: 'measure.mp4',
  shot: 'Close-ups: finger taps the printed “1:100” · ruler across one room · pencil tracing an interior wall on tracing paper.',
  vo: 'To read it, you have to see the walls, find the scale, and measure every room. That’s spatial reasoning. There’s no answer to look up.',
  build(root, tl) {
    shade(root);
    const words = ['See.', 'Calibrate.', 'Measure.'];
    words.forEach((w, i) => {
      const e = div(root, 'abs disp', `left:120px;bottom:${130 + (2 - i) * 120}px;font-size:120px;color:#fff;`, i === 2 ? `<span class="serif" style="letter-spacing:-0.02em;">${w}</span>` : w);
      tl.fromTo(e, { opacity: 0, x: -40 }, { opacity: 1, x: 0, duration: 0.6, ease: 'expo.out' }, 1.5 + i * 2.8);
    });
  },
},

// ───────────────────────────── 3 · the environment
{
  id: 'machine', title: 'The setup', dur: 10, theme: 'light',
  vo: 'We gave Gemini 3.1 Pro the same drawing and eight tools: zoom, OCR, room segmentation, area measurement. In our benchmark that’s all it gets. No shell. No code. Just its eyes and its judgement.',
  build(root, tl) {
    const pv = planView(root, { x: 1000, y: 120, w: 800, h: 840, view: BLD });
    tl.fromTo(pv.box, { opacity: 0, scale: 1.12, rotation: 3 }, { opacity: 1, scale: 1, rotation: 0, duration: 1.4, ease: 'expo.out' }, 0);
    div(root, 'abs label', 'left:120px;top:140px;', 'The environment');
    const h = div(root, 'abs disp', 'left:120px;top:200px;font-size:104px;width:820px;color:#111113;', 'One drawing.<br>Eight tools.<br><span class="serif o">Thirty calls.</span>');
    slam(tl, h, 0.4, { stagger: 0.1 });
    const tools = ['view_region', 'estimate_scale', 'read_room_labels', 'segment_rooms', 'measure_area', 'preview_schematic', 'get_task', 'submit_schematic'];
    const wrap = div(root, 'abs', 'left:120px;top:600px;width:820px;display:flex;flex-wrap:wrap;gap:14px;');
    const pills = tools.map(t => div(wrap, 'pill', 'font-size:24px;', t));
    popIn(tl, pills, 2.6, { stagger: 0.12 });

    // the "no code" statement slides up over everything
    const band = div(root, 'abs', `inset:0;background:${INK};display:flex;flex-direction:column;justify-content:center;padding:0 120px;gap:30px;`);
    const a = div(band, 'disp', 'font-size:118px;color:#F4F2EE;', 'No shell. No code.<br>No answer key.');
    const b = div(band, 'disp', 'font-size:118px;', '<span class="serif o">Just spatial reasoning.</span>');
    tl.fromTo(band, { yPercent: 100 }, { yPercent: 0, duration: 0.7, ease: 'expo.inOut' }, 6.0);
    slam(tl, a, 6.6, { stagger: 0.08 });
    tl.fromTo(b, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.6, ease: 'expo.out' }, 8.0);
  },
},

// ───────────────────────────── 4 · side-by-side replay (the money shot)
{
  id: 'demo', title: 'Replay', dur: 25, theme: 'light',
  vo: 'Watch it work. Zoom. Zoom. Zoom. It even works out the right scale, then second-guesses itself. Then it draws every room by hand: loose boxes, no interior walls. Our plain computer-vision solver traces the walls, snaps rooms to the lines, and finishes in eight seconds. Point five one against point zero four.',
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
    const done = div(root, 'abs pill', 'left:1000px;top:770px;font-size:22px;', 'done · 8 s');
    popIn(tl, done, 8.2);

    // ---- left: Gemini, replayed from its real tool trace
    const box = svgEl('rect', { x: 0, y: 0, width: 10, height: 10, fill: ORANGE, 'fill-opacity': 0.08, stroke: ORANGE, 'stroke-width': 10, rx: 6, opacity: 0 }, L.g('zoom'));
    const counter = div(root, 'abs mono', `left:96px;top:${Y + H - 56}px;font-size:22px;color:#fff;background:${INK};padding:8px 14px;border-radius:999px;opacity:0;`, '');
    const STEP = 0.95, T0 = 1.0;
    let k = 0;
    D.agent.trace.forEach((c, i) => {
      const at = T0 + i * STEP;
      tl.call(() => { counter.textContent = `call ${i + 1} / 30 · ${c.tool}`; }, null, at);
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
  id: 'gap', title: 'The gap', dur: 15, theme: 'dark',
  vo: 'Across fifteen plans it has never seen, three full runs each: Gemini scores point three four. Our solver, point five nine. Here’s the kicker: stop our solver halfway, and it still beats the frontier agent. And the gap is stable. Three runs, within one hundredth of each other.',
  build(root, tl) {
    div(root, 'abs label', 'left:120px;top:110px;', '15 unseen plans · 3 runs each · reward 0 → 1');
    const h = div(root, 'abs disp', 'left:120px;top:170px;font-size:104px;width:1700px;', 'Half our solver beats<br>the <span class="serif o">frontier.</span>');
    slam(tl, h, 0.3, { stagger: 0.08 });
    const rows = [
      ['Our reference', R('reference').reward, BLUE, 'deterministic'],
      ['Our reference, stopped at 50 %', R('stop early (50').reward, '#5A5A62', ''],
      ['Gemini 3.1 Pro', R('agent: gemini-3.1').reward, ORANGE, R('agent: gemini-3.1').runs.map(v => v.toFixed(3)).join(' · ')],
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

// ───────────────────────────── 6a · reaction (filmed)
{
  id: 'ruler', title: 'Reaction', dur: 3, clip: 'ruler.mp4',
  shot: 'Hold the ruler up to camera. Shrug, or shake your head.',
  vo: 'So what goes wrong?',
},

// ───────────────────────────── 6b · why it fails
{
  id: 'scale', title: 'Why it fails', dur: 12, theme: 'light',
  vo: 'Here’s the wild part. It computed the right scale from “one to one hundred”: zero point zero one six nine. Then it eyeballed the scale bar, got zero point zero one seven four, and used that instead. Every area, six percent off. It also skips interior walls and ignores its own room tool. It can see. It can’t measure.',
  build(root, tl) {
    div(root, 'abs label', 'left:120px;top:110px;', `Gemini 3.1 Pro · plan ${D.task.split('_')[0]}`);
    const h = div(root, 'abs disp', `left:120px;top:170px;font-size:104px;width:1700px;color:${INK};`, 'It did the math.<br><span class="serif o">Then ignored it.</span>');
    slam(tl, h, 0.2, { stagger: 0.08 });
    const truth = D.gt.m_per_px, used = D.agent.schematic.m_per_px;
    const c1 = div(root, 'abs card', 'left:120px;top:480px;width:820px;display:flex;flex-direction:column;gap:14px;',
      `<span class="label">from “1:100 on A3”</span><span class="score" style="font-size:96px;">0.016935</span><span class="mono" style="font-size:24px;color:${GREEN};">✓ matches the survey: ${truth.toFixed(6)} m/px</span>`);
    const c2 = div(root, 'abs card', `left:980px;top:480px;width:820px;display:flex;flex-direction:column;gap:14px;box-shadow:inset 0 0 0 3px ${ORANGE};`,
      `<span class="label">from the scale bar, by eye</span><span class="score o" style="font-size:96px;">${used.toFixed(6)}</span><span class="mono" style="font-size:24px;color:${ORANGE};">✗ +${((used / truth - 1) * 100).toFixed(1)} % · the one it submitted</span>`);
    popIn(tl, c1, 2.0);
    popIn(tl, c2, 4.2);
    const res = div(root, 'abs', `left:120px;top:760px;width:1680px;font-size:40px;font-weight:600;letter-spacing:-0.02em;color:${INK};`,
      `Every area <span class="o">+${((used / truth) ** 2 * 100 - 100).toFixed(1)} %</span> → outside the 5 % tolerance → <span class="o">1 of ${D.gt.rooms.length}</span> room areas right.`);
    fadeIn(tl, res, 6.4, 0.5);
    const pills = ['0 interior walls', 'rooms drawn by hand', '1 in 5 runs never submits'].map((t, i) =>
      div(root, 'abs pill', `left:${120 + i * 520}px;top:860px;`, t));
    popIn(tl, pills, 8.4, { stagger: 0.25 });
  },
},

// ───────────────────────────── 7a · try to cheat (filmed)
{
  id: 'marker', title: 'Cheat (paper)', dur: 7, clip: 'marker.mp4',
  shot: 'Fat marker: scribble ONE giant box over the whole printed plan. Then stab dots all over it.',
  vo: 'So can you cheat?',
},

// ───────────────────────────── 7b · exploits score nothing
{
  id: 'cheat', title: 'Cheat (score)', dur: 8, theme: 'dark',
  vo: 'One giant room: zero. A thousand doors: zero point zero one. A wall around the whole building: zero point zero seven. The best cheat scores less than a quarter of honest work. Doing nothing scores zero.',
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

// ───────────────────────────── 8a · walk out (filmed)
{
  id: 'walkout', title: 'Walk out', dur: 6, clip: 'walkout.mp4',
  shot: 'Roll up the plan, walk back out through the door. Door closes.',
  vo: 'One command reproduces every number, and it runs in Harbor over MCP.',
},

// ───────────────────────────── 8b · end card
{
  id: 'end', title: 'End card', dur: 9, theme: 'dark',
  vo: 'Blueprint to Schematic. Agents can see the drawing. Now let’s teach them to measure it.',
  build(root, tl) {
    const a = div(root, 'abs disp', 'left:120px;top:300px;font-size:120px;width:1700px;', 'Agents can see the drawing.');
    const b = div(root, 'abs disp', 'left:120px;top:440px;font-size:120px;width:1700px;', 'Now let’s teach them to <span class="serif o">measure</span> it.');
    slam(tl, a, 0.3, { stagger: 0.07 });
    slam(tl, b, 1.6, { stagger: 0.07 });
    tl.to([a, b], { opacity: 0, y: -30, duration: 0.5, ease: 'power2.in' }, 4.4);
    const logo = div(root, 'abs disp', 'left:120px;top:340px;font-size:124px;', 'Blueprint <span class="o">→</span> Schematic');
    tl.fromTo(logo, { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.7, ease: 'expo.out' }, 4.9);
    const cmd = div(root, 'abs mono', 'left:124px;top:540px;font-size:34px;color:#F4F2EE;', '');
    typeText(tl, cmd, '$ python -m blueprint_env.evaluate', 5.6, { cps: 30 });
    const team = div(root, 'abs label', 'left:124px;top:640px;font-size:26px;', '[Team name] · Junction 2026 · Break the Agent');
    fadeIn(tl, team, 7.0);
  },
},
];
