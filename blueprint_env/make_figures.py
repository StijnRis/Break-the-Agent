"""Presentation figures (PNG, 16:9-friendly) from results/summary.json and the saved runs.

    python -m blueprint_env.evaluate && python -m blueprint_env.make_figures

Writes presentation/*.png. Colours: our reference = blue, frontier agent = orange, baselines = grey.
"""
from __future__ import annotations

import glob
import json
import os
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from PIL import Image  # noqa: E402

from .render import overlay  # noqa: E402

OUT = "presentation"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, GREY, GREY_L = "#2a78d6", "#eb6834", "#8c8b86", "#c3c2b7"
COMPS = ["walls", "rooms", "doors", "windows", "fixtures", "areas"]
AGENT = "agent: gemini-3.1-pro-preview"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "text.color": INK, "figure.facecolor": SURFACE,
                     "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "axes.spines.top": False,
                     "axes.spines.right": False})


def _save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, name), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", os.path.join(OUT, name))


def _title(ax, title, sub):
    ax.set_title(title, loc="left", fontsize=18, fontweight="bold", color=INK, pad=28)
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=12, color=INK2, va="bottom")


def gap(S):
    rows = S["rows"]
    order = [("ceiling (ground-truth replay)", "Ceiling (answer key replayed)", GREY_L),
             ("reference (CV solver, no ground truth)", "Our reference solver (no answer key)", BLUE),
             (AGENT, "Gemini 3.1 Pro (frontier agent)", ORANGE),
             ("agent: stop-early-gemini-3-flash-4calls", "Agent that stops early (4 tool calls)", GREY),
             ("do nothing", "Do nothing", GREY)]
    order = [o for o in order if o[0] in rows]
    fig, ax = plt.subplots(figsize=(12, 5.2))
    for i, (k, label, c) in enumerate(order):
        v = rows[k]["reward_mean"]
        y = len(order) - 1 - i
        ax.barh(y, max(v, 0.004), height=0.56, color=c, edgecolor=SURFACE, linewidth=2)
        runs = rows[k].get("per_run_means") or []
        if len(runs) > 1:
            ax.plot(runs, [y] * len(runs), "o", ms=8, color=INK, mfc=SURFACE, mew=1.6, zorder=3)
        ax.text(max([v] + runs) + 0.02, y, f"{v:.2f}", va="center", fontsize=14, fontweight="bold", color=INK)
    ax.set_yticks(range(len(order)), [o[1] for o in reversed(order)], fontsize=13)
    ax.set_xlim(0, 1.08); ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.xaxis.grid(True, color=GRID); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    ax.set_xlabel("reward (0 – 1), mean over the 15 test plans")
    n = rows.get(AGENT, {}).get("n_episodes", 0)
    _title(ax, "The gap: the frontier agent reaches less than half of our reference",
           f"Same drawings, same reward. Open circles = mean of each of the agent's 3 repeated runs ({n} episodes).")
    _save(fig, "1_gap.png")


def components(S):
    rows = S["rows"]
    ref, ag = rows["reference (CV solver, no ground truth)"]["components"], rows.get(AGENT, {}).get("components")
    if not ag:
        return
    fig, ax = plt.subplots(figsize=(12, 5.2))
    w = 0.38
    xs = range(len(COMPS))
    for dx, d, c, lab in ((-w / 2, ref, BLUE, "Our reference solver"), (w / 2, ag, ORANGE, "Gemini 3.1 Pro")):
        bars = ax.bar([x + dx for x in xs], [d[k] for k in COMPS], width=w - 0.02, color=c, label=lab,
                      edgecolor=SURFACE, linewidth=2)
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.015, f"{b.get_height():.2f}", ha="center",
                    fontsize=11, color=INK2)
    weights = {"walls": 25, "rooms": 25, "doors": 15, "windows": 15, "fixtures": 10, "areas": 10}
    ax.set_xticks(list(xs), [f"{k}\n({weights[k]} %)" for k in COMPS])
    ax.set_ylim(0, 1.05); ax.yaxis.grid(True, color=GRID); ax.set_axisbelow(True)
    ax.set_ylabel("component score (F1 / share correct)")
    ax.legend(frameon=False, loc="upper right", fontsize=12)
    _title(ax, "Where the agent loses points", "Score per reward component (weight in brackets). Areas need the right scale AND the right outline.")
    _save(fig, "2_components.png")


def per_plan(S, runs_dir="runs"):
    tasks = S["tasks"]
    ref = {t: json.load(open(f"{runs_dir}/reference-cv/{t}/episode.json"))["result"]["reward"] for t in tasks
           if os.path.exists(f"{runs_dir}/reference-cv/{t}/episode.json")}
    ag = {}
    for f in glob.glob(f"{runs_dir}/gemini-3.1-pro-preview/*/run*/episode.json"):
        t = f.replace("\\", "/").split("/")[-3]
        ag.setdefault(t, []).append(json.load(open(f, encoding="utf8"))["result"]["reward"])
    tasks = sorted((t for t in tasks if t in ref and t in ag), key=lambda t: ref[t])
    if not tasks:
        return
    fig, ax = plt.subplots(figsize=(12, 6.2))
    for i, t in enumerate(tasks):
        lo = min(ag[t] + [ref[t]]); hi = max(ag[t] + [ref[t]])
        ax.plot([lo, hi], [i, i], color=GRID, lw=2, zorder=1)
        ax.plot(ag[t], [i] * len(ag[t]), "o", ms=8, color=ORANGE, mec=SURFACE, mew=1.5, zorder=3,
                label="Gemini 3.1 Pro (each run)" if i == 0 else None)
        ax.plot(ref[t], i, "D", ms=9, color=BLUE, mec=SURFACE, mew=1.5, zorder=3, label="Our reference" if i == 0 else None)
    ax.set_yticks(range(len(tasks)), [t.split("_")[0] for t in tasks], fontsize=11)
    ax.set_xlim(0, 1); ax.xaxis.grid(True, color=GRID); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    ax.set_xlabel("reward")
    wins = sum(max(ag[t]) < ref[t] for t in tasks)
    ax.legend(frameon=False, loc="lower right", fontsize=12)
    _title(ax, f"Consistent: the reference beats every agent run on {wins} of {len(tasks)} plans",
           "One row per test drawing; each orange dot is one of the agent's repeated runs.")
    _save(fig, "3_per_plan.png")


def exploits(S):
    ex = dict(S["exploits"])
    ex["do nothing"] = 0.0
    if "agent: stop-early-gemini-3-flash-4calls" in S["rows"]:
        ex["agent stops early (4 tool calls)"] = S["rows"]["agent: stop-early-gemini-3-flash-4calls"]["reward_mean"]
    items = sorted(ex.items(), key=lambda kv: kv[1])
    ref = S["rows"]["reference (CV solver, no ground truth)"]["reward_mean"]
    fig, ax = plt.subplots(figsize=(12, 6.4))
    for i, (k, v) in enumerate(items):
        honest = v > 0.5     # these attacks start from the TRUE geometry and only corrupt part of it
        ax.barh(i, max(v, 0.004), height=0.6, color=GREY_L if honest else GREY, edgecolor=SURFACE, linewidth=2)
        ax.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=11, color=INK)
    ax.axvline(1.0, color=INK2, lw=1.2, ls="--"); ax.text(0.99, len(items) - 0.4, "perfect answer = 1.00", ha="right", fontsize=11, color=INK2)
    ax.axvline(ref, color=BLUE, lw=2); ax.text(ref + 0.01, -0.9, f"our reference {ref:.2f}", color=BLUE, fontsize=11)
    ax.set_yticks(range(len(items)), [k for k, _ in items], fontsize=11)
    ax.set_xlim(0, 1.05); ax.set_ylim(-1.3, len(items) - 0.2)
    ax.xaxis.grid(True, color=GRID); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    ax.set_xlabel("reward")
    _title(ax, "Reward hacking does not pay", "Shortcuts score near 0; corrupting a perfect answer always scores below the perfect answer.")
    _save(fig, "4_exploits.png")


def _example(t, ag_r, ag_s, name, headline, runs_dir="runs", root="tasks"):
    gt = json.load(open(f"{root}/{t}/ground_truth.json", encoding="utf8"))
    ref = json.load(open(f"{runs_dir}/reference-cv/{t}/episode.json"))
    xs = [p[0] for w in gt["walls"] for p in w]; ys = [p[1] for w in gt["walls"] for p in w]
    pad = 40; box = (max(0, min(xs) - pad), max(0, min(ys) - pad), max(xs) + pad, max(ys) + pad)
    draw = os.path.join(root, t, "drawing.png")
    panels = [("The drawing (agent's input)", Image.open(draw).convert("RGB").crop(box)),
              ("Ground truth (from the CAD file)", overlay(draw, gt, crop=box, labels=False)),
              (f"Our reference — reward {ref['result']['reward']:.2f}", overlay(draw, ref["schematic"], crop=box, labels=False)),
              (f"Gemini 3.1 Pro — reward {ag_r:.2f}", overlay(draw, ag_s, crop=box, labels=False))]
    aspect = (box[3] - box[1]) / (box[2] - box[0])
    fig, axs = plt.subplots(1, 4, figsize=(20, min(7.0, 4.6 * aspect + 1.2)), layout="constrained")
    for ax, (title, im) in zip(axs, panels):
        ax.imshow(im); ax.set_title(title, fontsize=14, loc="left", color=INK); ax.axis("off")
    fig.suptitle(f"{headline} ({t.split('_')[0]}): blue = walls, orange = rooms, green = doors, cyan = windows, pink = fixtures",
                 x=0.01, ha="left", fontsize=13, color=INK2)
    _save(fig, name)


def overlays(S, runs_dir="runs", root="tasks"):
    ag = {}
    for f in glob.glob(f"{runs_dir}/gemini-3.1-pro-preview/*/run*/episode.json"):
        d = json.load(open(f, encoding="utf8"))
        t = f.replace("\\", "/").split("/")[-3]
        if d.get("schematic"):
            ag.setdefault(t, []).append((d["result"]["reward"], d["schematic"]))
    cands = [t for t in S["tasks"] if t in ag and os.path.exists(f"{runs_dir}/reference-cv/{t}/episode.json")]
    if not cands:
        return
    ref = {t: json.load(open(f"{runs_dir}/reference-cv/{t}/episode.json"))["result"]["reward"] for t in cands}
    med = {t: sorted(ag[t], key=lambda x: x[0])[len(ag[t]) // 2] for t in cands}
    best = {t: max(ag[t], key=lambda x: x[0]) for t in cands}
    worst = {t: min(ag[t], key=lambda x: x[0]) for t in cands}
    mean = st.mean(r for v in ag.values() for r, _ in v)
    used = set()

    def pick(key, choose):
        left = [t for t in cands if t not in used] or cands
        t = choose(left, key=key); used.add(t); return t

    # 1) typical: the plan where the agent's median run is closest to its overall mean
    t = pick(lambda t: abs(med[t][0] - mean), min)
    _example(t, *med[t], "5_example.png", "A typical test drawing", runs_dir, root)
    # 2) the agent's best run overall
    t = pick(lambda t: best[t][0], max)
    _example(t, *best[t], "5b_example_agent_best.png", "The agent's best run", runs_dir, root)
    # 3) the agent's worst run overall
    t = pick(lambda t: worst[t][0], min)
    _example(t, *worst[t], "5c_example_agent_worst.png", "The agent's worst run", runs_dir, root)
    # 4) largest gap between our reference and the agent's median run
    t = pick(lambda t: ref[t] - med[t][0], max)
    _example(t, *med[t], "5d_example_biggest_gap.png", "Largest gap to our reference (agent's median run)", runs_dir, root)


def loop():
    fig, ax = plt.subplots(figsize=(14, 5.2)); ax.axis("off"); ax.set_xlim(0, 14); ax.set_ylim(0, 5.2)

    def box(x, y, w, h, title, body, c):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15", fc=SURFACE, ec=c, lw=2.2))
        ax.text(x + 0.2, y + h - 0.35, title, fontsize=14, fontweight="bold", color=INK, va="top")
        ax.text(x + 0.2, y + h - 0.85, body, fontsize=11.5, color=INK2, va="top", linespacing=1.45)

    def arrow(x0, y0, x1, y1, label=""):
        ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.8, mutation_scale=18))
        if label:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.15, label, ha="center", fontsize=11, color=INK2)

    box(0.2, 1.1, 3.0, 3.2, "Observation", "construction drawing\n2480 × 1753 px\nprinted areas masked\nscale bar + legend kept", GREY)
    box(4.4, 1.1, 3.3, 3.2, "Agent (MCP tools)", "view_region  (zoom + rulers)\nsegment_rooms  (CV helper)\nmeasure_area\npreview_schematic\n≤ 30 tool calls", ORANGE)
    box(8.9, 1.1, 2.4, 3.2, "Schematic", "walls\nrooms + labels\ndoors, windows\nfixtures\nscale (m / px)", BLUE)
    box(12.0, 1.1, 1.9, 3.2, "Reward", "0 – 1\n6 one-to-one\nF1 scores vs\nthe CAD file", GREY)
    arrow(3.25, 2.7, 4.35, 2.7, "image")
    arrow(7.75, 2.7, 8.85, 2.7, "submit")
    arrow(11.35, 2.7, 11.95, 2.7)
    ax.annotate("", (5.2, 1.05), (6.9, 1.05), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.4, connectionstyle="arc3,rad=-0.9"))
    ax.text(6.05, 0.15, "tool results (crops, overlays, areas)", ha="center", fontsize=11, color=INK2)
    ax.text(0.2, 4.95, "The environment: read a construction drawing, produce a machine-readable schematic",
            fontsize=18, fontweight="bold", color=INK)
    _save(fig, "0_environment.png")


def main():
    S = json.load(open("results/summary.json"))
    loop(); gap(S); components(S); per_plan(S); exploits(S); overlays(S)


if __name__ == "__main__":
    main()
