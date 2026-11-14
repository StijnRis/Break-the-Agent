"""Render report.html from report_data.json + overlay images (all inlined)."""
from __future__ import annotations

import base64
import json
import statistics as st

D = json.load(open("report_data.json"))
PRO, FLASH = "gemini-3.1-pro-preview", "gemini-3-flash-preview"
EPS = D["episodes"]
AGG = D["agg"]
TASKS = {
    "site980_bldg2055_floor9178": ("Italian, 1:100", 10),
    "site936_bldg1976_floor8706": ("German, 1:100", 14),
    "site11704_bldg18258_floor48967": ("1:100", 17),
    "site303_bldg598_floor2434": ("1:100", 18),
    "site279_bldg514_floor2041": ("1:100", 20),
    "site4038_bldg6362_floor26166": ("Italian, 1:100", 28),
}
COMPS = ["walls", "rooms", "doors", "windows", "fixtures", "areas"]
W = {"walls": 25, "rooms": 25, "doors": 15, "windows": 15, "fixtures": 10, "areas": 10}


def img(p):
    return "data:image/jpeg;base64," + base64.b64encode(open(p, "rb").read()).decode()


def short(t):
    return t.split("_")[0].replace("site", "Site ") + " · " + t.split("_")[2].replace("floor", "floor ")


# ---------------------------------------------------------------- dot plot (SVG)
order = sorted(TASKS, key=lambda t: TASKS[t][1])
rowh, top, left, right = 46, 34, 190, 30
Wd = 760; H = top + rowh * len(order) + 34
X = lambda v: left + v * (Wd - left - right)
svg = [f'<svg viewBox="0 0 {Wd} {H}" role="img" aria-label="Reward per floor plan: Gemini runs versus reference">']
for v in [0, .2, .4, .6, .8, 1.0]:
    svg.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{top-10}" y2="{H-30}" class="grid"/>')
    svg.append(f'<text x="{X(v):.1f}" y="{H-12}" class="tick" text-anchor="middle">{v:.1f}</text>')
for i, t in enumerate(order):
    y = top + i * rowh + rowh / 2
    svg.append(f'<text x="{left-14}" y="{y-3:.1f}" class="rowlab" text-anchor="end">{short(t)}</text>')
    svg.append(f'<text x="{left-14}" y="{y+12:.1f}" class="rowsub" text-anchor="end">{TASKS[t][1]} rooms</text>')
    svg.append(f'<line x1="{X(0)}" x2="{X(1)}" y1="{y:.1f}" y2="{y:.1f}" class="lane"/>')
    pr = [e["reward"] for e in EPS if e["task"] == t and e["model"] == PRO]
    fl = [e["reward"] for e in EPS if e["task"] == t and e["model"] == FLASH]
    svg.append(f'<line x1="{X(min(pr)):.1f}" x2="{X(max(pr)):.1f}" y1="{y:.1f}" y2="{y:.1f}" class="range"/>')
    for v in pr:
        svg.append(f'<circle cx="{X(v):.1f}" cy="{y:.1f}" r="6" class="pro"><title>Pro {v:.3f}</title></circle>')
    for v in fl:
        svg.append(f'<rect x="{X(v)-5:.1f}" y="{y-5:.1f}" width="10" height="10" transform="rotate(45 {X(v):.1f} {y:.1f})" class="flash"><title>Flash {v:.3f}</title></rect>')
    svg.append(f'<path d="M{X(1)-7:.1f},{y-7:.1f} L{X(1)+7:.1f},{y+7:.1f} M{X(1)+7:.1f},{y-7:.1f} L{X(1)-7:.1f},{y+7:.1f}" class="ref"/>')
svg.append(f'<text x="{X(1):.1f}" y="{top-16}" class="annot" text-anchor="middle">reference</text>')
svg.append("</svg>")
DOT = "\n".join(svg)

# ---------------------------------------------------------------- component table
crow = []
for c in COMPS:
    p, f = AGG[PRO]["components"][c], AGG[FLASH]["components"][c]
    crow.append(f'<tr><th scope="row">{c}</th><td class="num">{W[c]}</td>'
                f'<td><div class="bar"><span style="width:{p*100:.0f}%"></span></div></td><td class="num">{p:.2f}</td>'
                f'<td class="num muted">{f:.2f}</td><td class="num">1.00</td></tr>')
CTABLE = "\n".join(crow)

# ---------------------------------------------------------------- baselines
B = D["baselines"]
blabels = [
    ("reference (ground truth)", "Reference: surveyed DXF geometry", "ref"),
    ("GT + 5 cm noise", "Reference, every vertex jittered ±5 cm", "ok"),
    ("GT + 20 cm noise", "Reference, jittered ±20 cm", "ok"),
    ("stop early (50 %)", "Stop early: first half of every element list", "mid"),
    ("stop early (25 %)", "Stop early: first quarter", "mid"),
    ("rooms duplicated x3", "Exploit: every room submitted three times", "mid"),
    ("right geometry, scale x1.3", "Exploit: perfect tracing, wrong scale", "mid"),
    ("wall = whole building box", "Exploit: one wall polygon over the whole building", "bad"),
    ("door/window/fixture spam (961 each)", "Exploit: 961 doors, windows and fixtures on a grid", "bad"),
    ("one giant room", "Exploit: one room covering the building", "bad"),
    ("scale only", "Exploit: only the scale, nothing traced", "bad"),
    ("do nothing", "Do nothing: empty submission", "bad"),
    ("malformed junk", "Malformed JSON values, NaN scale", "bad"),
]
brows = "\n".join(
    f'<tr class="{k}"><td>{lab}</td><td><div class="bar thin"><span style="width:{B[key]*100:.0f}%"></span></div></td>'
    f'<td class="num">{B[key]:.3f}</td></tr>' for key, lab, k in blabels)

pro_mean, pro_sd = AGG[PRO]["reward_mean"], AGG[PRO]["reward_sd"]
fl_mean = AGG[FLASH]["reward_mean"]
pro_best = max(e["reward"] for e in EPS if e["model"] == PRO)
tok_in = st.mean(e["tokens"]["in"] for e in EPS if e["model"] == PRO)
secs = st.mean(e["seconds"] for e in EPS if e["model"] == PRO)

I = D["imgs"]
html = open("blueprint_env/report_template.html", encoding="utf8").read()
for k, v in {
    "{{DOT}}": DOT, "{{CTABLE}}": CTABLE, "{{BROWS}}": brows,
    "{{PRO_MEAN}}": f"{pro_mean:.2f}", "{{PRO_SD}}": f"{pro_sd:.2f}", "{{FL_MEAN}}": f"{fl_mean:.2f}",
    "{{PRO_BEST}}": f"{pro_best:.2f}", "{{TOK_IN}}": f"{tok_in/1000:.0f}k", "{{SECS}}": f"{secs/60:.1f}",
    "{{SCALE_PRO}}": f"{AGG[PRO]['scale_err']*100:.0f}", "{{SCALE_FL}}": f"{AGG[FLASH]['scale_err']*100:.0f}",
    "{{IMG_936_GT}}": img(I["site936_bldg1976_floor8706_gt"]), "{{IMG_936_AG}}": img(I["site936_bldg1976_floor8706_agent"]),
    "{{IMG_4038_GT}}": img(I["site4038_bldg6362_floor26166_gt"]), "{{IMG_4038_AG}}": img(I["site4038_bldg6362_floor26166_agent"]),
}.items():
    html = html.replace(k, v)
open("report.html", "w", encoding="utf8").write(html)
print("ok", len(html))
