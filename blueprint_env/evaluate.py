"""One command to reproduce every reported number on the fixed test split.

    python -m blueprint_env.evaluate                      # reference, ceiling, baselines, exploits, existing agent runs
    python -m blueprint_env.evaluate --agent gemini-3.1-pro-preview --runs 3   # also (re)run the agent where missing

Rows (all scored by the same score.py against the same ground truth):
  ceiling (ground truth replay)  the answer key itself: shows the reward reaches 1.0
  reference (CV solver)          our scripted solver, no ground truth (reference.py)
  agent runs                     runs/<model>/<task>/run*/episode.json (Gemini runner or MCP harness results)
  do nothing                     empty submission / no submission
  stop early (25 % / 50 %)       the reference solver's schematic cut to its first 25 % / 50 % of every list
  exploits                       baselines.py attacks (spam, giant room, duplicated rooms, wrong scale, junk)
Writes results/summary.json and results/summary.md.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics as st

from PIL import Image

from . import baselines, reference
from .score import score

COMPS = ["walls", "rooms", "doors", "windows", "fixtures", "areas", "speed"]


def _agg(results):
    """results: {task: [reward dicts]} -> mean/sd over runs and tasks, per-run means (for reproducibility)."""
    flat = [r for rs in results.values() for r in rs]
    if not flat:
        return None
    nruns = max(len(v) for v in results.values())
    per_run = []
    for k in range(nruns):
        rk = [v[k]["reward"] for v in results.values() if len(v) > k]
        if rk:
            per_run.append(round(st.mean(rk), 3))
    return {"n_episodes": len(flat), "n_tasks": len(results), "reward_mean": round(st.mean(r["reward"] for r in flat), 3),
            "reward_sd_over_runs": round(st.pstdev(per_run), 3) if len(per_run) > 1 else 0.0, "per_run_means": per_run,
            "components": {c: round(st.mean(float(r["components"][c]) for r in flat), 3) for c in COMPS}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="tasks")
    ap.add_argument("--split", default="split.json")
    ap.add_argument("--key", default="test")
    ap.add_argument("--runs-dir", default="runs")
    ap.add_argument("--agent", default="", help="Gemini model to run where runs are missing (needs GEMINI_API_KEY)")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    tasks = json.load(open(a.split))[a.key]
    rows, exploit_rows = {}, {}

    def add(name, task, res):
        rows.setdefault(name, {}).setdefault(task, []).append(res)

    for t in tasks:
        td = os.path.join(a.root, t)
        gt = json.load(open(os.path.join(td, "ground_truth.json"), encoding="utf8"))
        img = Image.open(os.path.join(td, "drawing.png")).convert("RGB")
        ref_path = os.path.join(a.runs_dir, "reference-cv", t, "episode.json")
        if os.path.exists(ref_path):
            sch = json.load(open(ref_path, encoding="utf8"))["schematic"]
        else:
            sch = reference.solve(img)
            os.makedirs(os.path.dirname(ref_path), exist_ok=True)
            json.dump({"result": score(gt, sch, img.size), "schematic": sch}, open(ref_path, "w"), indent=1)
        add("reference (CV solver, no ground truth)", t, score(gt, sch, img.size))
        add("ceiling (ground-truth replay)", t, score(gt, baselines.gt_as_pred(gt), img.size))
        add("do nothing", t, score(gt, None, img.size))
        for f in (0.25, 0.5):
            cut = {"m_per_px": sch["m_per_px"], **{k: sch[k][: int(len(sch[k]) * f)] for k in COMPS[:5]}}
            add(f"stop early ({int(f * 100)} %)", t, score(gt, cut, img.size))
        for name, p in baselines.exploits(gt, None).items():
            exploit_rows.setdefault(name, []).append(score(gt, p, img.size)["reward"])
        if a.agent:
            from .agent import run_episode
            key = os.environ.get("GEMINI_API_KEY") or dict(l.strip().split("=", 1) for l in open(".env") if "=" in l)["GEMINI_API_KEY"]
            for r in range(a.runs):
                d = os.path.join(a.runs_dir, a.agent, t, f"run{r}")
                if not os.path.exists(os.path.join(d, "episode.json")):
                    print(f"running {a.agent} on {t} run {r}", flush=True)
                    run_episode(td, a.agent, key, d)

    # every agent run found on disk (Gemini runner or MCP harness results)
    for f in sorted(glob.glob(os.path.join(a.runs_dir, "*", "*", "run*", "episode.json"))):
        model, t = f.split(os.sep)[-4], f.split(os.sep)[-3]
        if t in tasks and model != "reference-cv":
            episode = json.load(open(f, encoding="utf8"))
            # Re-score stored schematics so a benchmark always reflects the current reward,
            # including the recorded wall-clock time.
            elapsed = episode.get("result", {}).get("seconds")
            img = Image.open(os.path.join(a.root, t, "drawing.png")).convert("RGB")
            gt = json.load(open(os.path.join(a.root, t, "ground_truth.json"), encoding="utf8"))
            add(f"agent: {model}", t, score(gt, episode.get("schematic"), img.size, elapsed))

    summary = {"split": a.key, "tasks": tasks, "rows": {k: _agg(v) for k, v in rows.items()},
               "exploits": {k: round(st.mean(v), 3) for k, v in exploit_rows.items()}}
    os.makedirs(a.out, exist_ok=True)
    json.dump(summary, open(os.path.join(a.out, "summary.json"), "w"), indent=1)
    lines = [f"Test split: {len(tasks)} plans. Reward in [0, 1]; mean over plans and runs.\n",
             "| run | episodes | reward | sd over runs | " + " | ".join(COMPS) + " |",
             "|---|---|---|---|" + "---|" * len(COMPS)]
    order = sorted(summary["rows"].items(), key=lambda kv: -kv[1]["reward_mean"])
    for k, v in order:
        lines.append(f"| {k} | {v['n_episodes']} | **{v['reward_mean']:.3f}** | {v['reward_sd_over_runs']:.3f} | "
                     + " | ".join(f"{v['components'][c]:.2f}" for c in COMPS) + " |")
    lines += ["", "Exploit attempts (mean reward):", ""] + [f"- {k}: {v:.3f}" for k, v in summary["exploits"].items()]
    md = "\n".join(lines)
    open(os.path.join(a.out, "summary.md"), "w", encoding="utf8").write(md + "\n")
    print(md)


if __name__ == "__main__":
    main()
