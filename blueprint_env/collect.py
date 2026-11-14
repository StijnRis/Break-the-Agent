"""Aggregate run results and render example overlays for the report.

usage: python -m blueprint_env.collect <out_json> <img_dir>
"""
from __future__ import annotations

import glob
import json
import os
import statistics as st
import sys

from PIL import Image

from .render import overlay

COMPS = ["walls", "rooms", "doors", "windows", "fixtures", "areas"]


def bbox(gt, pad=60):
    xs = [p[0] for w in gt["walls"] for p in w]; ys = [p[1] for w in gt["walls"] for p in w]
    return (max(0, min(xs) - pad), max(0, min(ys) - pad), max(xs) + pad, max(ys) + pad)


def main():
    out_json, img_dir = sys.argv[1], sys.argv[2]
    os.makedirs(img_dir, exist_ok=True)
    eps = []
    for f in glob.glob("runs/*/*/run*/episode.json"):
        d = json.load(open(f, encoding="utf8"))
        r = d["result"]
        tools = [t.get("tool") for t in d["trace"] if t.get("tool")]
        eps.append({"model": r["model"], "task": r["task"], "run": f.split(os.sep)[-2], "reward": r["reward"],
                    "components": r["components"], "details": r["details"], "submitted": r["submitted"],
                    "tool_calls": r["tool_calls"], "seconds": r["seconds"], "tokens": r["tokens"],
                    "n_view": tools.count("view_region"), "n_preview": tools.count("preview_schematic"),
                    "counts": {k: len((d["schematic"] or {}).get(k) or []) for k in COMPS[:5]},
                    "path": f})
    eps.sort(key=lambda e: (e["model"], e["task"], e["run"]))
    # aggregate
    agg = {}
    for m in sorted({e["model"] for e in eps}):
        E = [e for e in eps if e["model"] == m]
        agg[m] = {"n": len(E), "reward_mean": round(st.mean(e["reward"] for e in E), 3),
                  "reward_sd": round(st.pstdev([e["reward"] for e in E]), 3),
                  "components": {c: round(st.mean(e["components"][c] for e in E), 3) for c in COMPS},
                  "scale_err": round(st.mean(abs(e["details"]["scale_ratio"] - 1) for e in E), 3),
                  "submit_rate": round(sum(e["submitted"] for e in E) / len(E), 2),
                  "per_task": {t: [e["reward"] for e in E if e["task"] == t] for t in sorted({e["task"] for e in E})}}
    # overlays: GT and agent for best/worst pro run + one flash
    imgs = {}
    for e in eps:
        if e["model"] != "gemini-3.1-pro-preview" or e["run"] != "run0":
            continue
        td = os.path.join("tasks", e["task"])
        gt = json.load(open(os.path.join(td, "ground_truth.json"), encoding="utf8"))
        sch = json.load(open(e["path"], encoding="utf8"))["schematic"] or {}
        bb = bbox(gt)
        for tag, s in (("gt", gt), ("agent", sch)):
            im = overlay(os.path.join(td, "drawing.png"), s, crop=bb, labels=False)
            im.thumbnail((900, 900))
            p = os.path.join(img_dir, f"{e['task']}_{tag}.jpg")
            im.save(p, quality=72)
            imgs[f"{e['task']}_{tag}"] = p
    json.dump({"episodes": eps, "agg": agg, "imgs": imgs,
               "baselines": json.load(open("tasks/baselines.json"))}, open(out_json, "w"), indent=1)
    for m, a in agg.items():
        print(m, json.dumps(a))


if __name__ == "__main__":
    main()
