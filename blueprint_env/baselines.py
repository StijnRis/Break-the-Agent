"""Reward sanity checks: reference (GT), noisy GT, do-nothing, stop-early and exploit attempts."""
from __future__ import annotations

import copy
import json
import os
import random
import sys

from PIL import Image

from .score import score


def _bbox(gt):
    xs = [p[0] for w in gt["walls"] for p in w]; ys = [p[1] for w in gt["walls"] for p in w]
    return min(xs), min(ys), max(xs), max(ys)


def _grid_rooms(x0, y0, x1, y1, n):
    import math
    c = max(1, round(math.sqrt(n * (x1 - x0) / max(y1 - y0, 1))))
    r = max(1, math.ceil(n / c))
    w, h = (x1 - x0) / c, (y1 - y0) / r
    return [{"id": None, "name": None, "polygon": [[x0 + i * w, y0 + j * h], [x0 + (i + 1) * w, y0 + j * h],
                                                   [x0 + (i + 1) * w, y0 + (j + 1) * h], [x0 + i * w, y0 + (j + 1) * h]]}
            for j in range(r) for i in range(c)][:n]


def _most_common_name(gt):
    import collections
    c = collections.Counter(r["name"] for r in gt["rooms"] if r["name"])
    return c.most_common(1)[0][0] if c else None


def gt_as_pred(gt):
    p = copy.deepcopy(gt)
    p["walls"] = gt["walls"]
    return p


def jitter(gt, m, rng):
    s = m / gt["m_per_px"]
    J = lambda v: v + rng.uniform(-s, s)
    p = copy.deepcopy(gt)
    p["walls"] = [[[J(x), J(y)] for x, y in w] for w in gt["walls"]]
    dx = lambda: rng.uniform(-s, s)
    for r in p["rooms"]:
        ox, oy = dx(), dx()
        r["polygon"] = [[x + ox, y + oy] for x, y in r["polygon"]]
    for k in ("doors", "windows"):
        for o in p[k]:
            ox, oy = dx(), dx()
            o["p1"] = [o["p1"][0] + ox, o["p1"][1] + oy]; o["p2"] = [o["p2"][0] + ox, o["p2"][1] + oy]
    for f in p["fixtures"]:
        f["x"] += dx(); f["y"] += dx()
    p["m_per_px"] = gt["m_per_px"] * rng.uniform(0.99, 1.01)
    return p


def stop_early(gt, frac):
    p = {"m_per_px": gt["m_per_px"]}
    for k in ("walls", "rooms", "doors", "windows", "fixtures"):
        p[k] = gt[k][: int(len(gt[k]) * frac)]
    return p


def exploits(gt, rng):
    x0, y0, x1, y1 = _bbox(gt)
    box = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
    mpp = gt["m_per_px"]
    grid = [[x0 + (x1 - x0) * i / 30, y0 + (y1 - y0) * j / 30] for i in range(31) for j in range(31)]
    return {
        "scale only": {"m_per_px": mpp},
        "wall = whole building box": {"m_per_px": mpp, "walls": [box]},
        "one giant room": {"m_per_px": mpp, "rooms": [{"id": "1", "name": "Zimmer", "polygon": box}]},
        "door/window/fixture spam (961 each)": {
            "m_per_px": mpp,
            "doors": [{"p1": g, "p2": [g[0] + 25, g[1]]} for g in grid],
            "windows": [{"p1": g, "p2": [g[0] + 25, g[1]]} for g in grid],
            "fixtures": [{"type": t, "x": g[0], "y": g[1]} for g in grid for t in ("wc", "washbasin", "kitchen")],
        },
        "grid of rooms over the building (as many cells as rooms)": {
            "m_per_px": mpp, "rooms": _grid_rooms(x0, y0, x1, y1, max(1, len(gt["rooms"])))},
        "thick ring wall around the building": {
            "m_per_px": mpp, "walls": [{"p1": a, "p2": b, "thickness_px": 1.0 / mpp} for a, b in
                                       zip(box, box[1:] + box[:1])]},
        "every fixture type stacked on every true fixture": {
            "m_per_px": mpp, "fixtures": [{"type": t, "x": f["x"], "y": f["y"]} for f in gt["fixtures"]
                                          for t in ("wc", "washbasin", "bathtub", "shower", "kitchen")]},
        "true room outlines, every name set to the most common label": {
            **gt_as_pred(gt), "rooms": [{**r, "name": _most_common_name(gt)} for r in gt["rooms"]]},
        "rooms duplicated x3": {**gt_as_pred(gt), "rooms": gt["rooms"] * 3},
        "right geometry, scale x1.3": {**gt_as_pred(gt), "m_per_px": mpp * 1.3},
        "malformed junk": {"m_per_px": "nan", "walls": [[1, 2]], "rooms": [{"polygon": [[0, 0]]}],
                           "doors": [{"p1": "x"}], "fixtures": [{"x": None}]},
    }


def run(task_dirs):
    rng = random.Random(0)
    rows = {}
    for td in task_dirs:
        gt = json.load(open(os.path.join(td, "ground_truth.json"), encoding="utf8"))
        size = Image.open(os.path.join(td, "drawing.png")).size
        cases = {"reference (ground truth)": gt_as_pred(gt),
                 "GT + 5 cm noise": jitter(gt, 0.05, rng),
                 "GT + 20 cm noise": jitter(gt, 0.20, rng),
                 "do nothing": {},
                 "stop early (25 %)": stop_early(gt, 0.25),
                 "stop early (50 %)": stop_early(gt, 0.5)}
        cases.update(exploits(gt, rng))
        for k, p in cases.items():
            rows.setdefault(k, []).append(score(gt, p, size)["reward"])
    return {k: round(sum(v) / len(v), 3) for k, v in rows.items()}


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "tasks"
    from .build_tasks import valid_tasks
    ids = sys.argv[2].split(",") if len(sys.argv) > 2 else valid_tasks(root)
    res = run([os.path.join(root, i) for i in ids])
    for k, v in res.items():
        print(f"{v:6.3f}  {k}")
    json.dump(res, open(os.path.join(root, "baselines.json"), "w"), indent=1)
