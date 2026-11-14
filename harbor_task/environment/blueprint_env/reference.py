"""Scripted reference solver: classic computer vision only, never reads the ground truth.

It sees exactly what the agent sees (the masked drawing) and builds the schematic in code:
scale from the legend scale bar, walls from thick straight ink, rooms from free space split at
door-sized passages, doors where two rooms touch, windows/doors from gaps in the outer wall,
fixtures by matching against the symbols drawn in the drawing's own legend.

usage: python -m blueprint_env.reference [task_id,...] [--root tasks]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as st

import numpy as np
from PIL import Image

from . import cv
from .score import score


def solve(img) -> dict:
    ink, walls, h, v = cv.masks(img)
    texts = cv.ocr(img)
    ppm = cv.printed_scale(texts) or cv.scale_bar(img) or cv.ppm_for(100)
    fp0 = cv.footprint(walls, ppm, ink)
    ys, xs = np.nonzero(fp0)
    region = (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else None
    labels = cv.room_labels(texts, region)
    rooms, lab, fp = cv.auto_rooms(img, ppm, walls, seeds=[n["xy"] for n in labels] or None, ink=ink)
    doors = cv.doors_from_labels(lab, ppm, walls)
    wins, ext_doors = cv.envelope_openings(walls, fp, ink, ppm)
    out_rooms = []
    for r in rooms:
        n = labels[r["label_id"] - 1] if labels else {"id": None, "name": None}
        out_rooms.append({"id": n["id"], "name": n["name"], "polygon": r["polygon"]})
    return {
        "m_per_px": 1.0 / ppm,
        "walls": cv.wall_rects(h, v),
        "rooms": out_rooms,
        "doors": doors + ext_doors,
        "windows": wins,
        "fixtures": cv.fixtures(ink, walls, fp, ppm),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks", nargs="?", default="")
    ap.add_argument("--root", default="tasks")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    ids = a.tasks.split(",") if a.tasks else sorted(d for d in os.listdir(a.root) if os.path.isdir(os.path.join(a.root, d)))
    rows = []
    for t in ids:
        td = os.path.join(a.root, t)
        img = Image.open(os.path.join(td, "drawing.png")).convert("RGB")
        gt = json.load(open(os.path.join(td, "ground_truth.json"), encoding="utf8"))
        sch = solve(img)
        res = score(gt, sch, img.size)
        rows.append(res)
        if a.out:
            os.makedirs(os.path.join(a.out, t), exist_ok=True)
            json.dump({"result": res, "schematic": sch}, open(os.path.join(a.out, t, "episode.json"), "w"), indent=1)
        print(f"{t:34s} {res['reward']:.3f} {res['components']} scale x{res['details']['scale_ratio']}", flush=True)
    if rows:
        comps = {k: round(st.mean(r["components"][k] for r in rows), 3) for k in rows[0]["components"]}
        print(f"MEAN {st.mean(r['reward'] for r in rows):.3f} {comps}")


if __name__ == "__main__":
    main()
