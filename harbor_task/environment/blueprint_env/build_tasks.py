"""Build task folder: for every Swiss floor -> masked observation PNG + ground-truth schematic in pixel frame.

usage: python -m blueprint_env.build_tasks <swiss_dwellings dir> [out dir]
"""
from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageDraw

from .gt import AREA_RE, extract, register, to_px


MIN_WALL_INK = 0.15   # well-registered plans have 0.2-0.6 of the GT wall area drawn dark; misregistered ones ~0.05


def check_alignment(png, walls):
    """Fraction of the ground-truth wall area that is drawn dark in the PNG (registration sanity check)."""
    import numpy as np
    a = np.asarray(Image.open(png).convert("L"))
    m = Image.new("1", (a.shape[1], a.shape[0]), 0); d = ImageDraw.Draw(m)
    for w in walls:
        if len(w) >= 3:
            d.polygon([tuple(p) for p in w], fill=1)
    m = np.asarray(m)
    return round(float((a[m] < 128).mean()) if m.sum() else 0.0, 3)


def valid_tasks(root):
    """Task ids whose ground truth passed the alignment check (index.json written by build_tasks)."""
    idx = json.load(open(os.path.join(root, "index.json")))
    return [r["task"] for r in idx if r.get("valid", r.get("wall_ink", 1.0) >= MIN_WALL_INK) and "error" not in r]


def build_one(dxf: str, png: str, out_dir: str) -> dict:
    g = extract(dxf)
    printed = None
    try:  # the printed '1:N' in the title block; the registration is constrained to it
        from .cv import ocr, SCALE_RE
        for t, *_ in ocr(Image.open(png)):
            m = SCALE_RE.search(t)
            if m:
                printed = int(m.group(1)); break
    except Exception:
        pass
    reg = register(png, g["_wall_union"], [printed] if printed else None)
    reg["printed_scale"] = printed
    im = Image.open(png).convert("RGB")
    dr = ImageDraw.Draw(im)
    # mask the printed net areas: they would let the agent read areas instead of measuring
    for text, pt, h in g["_texts"]:
        if AREA_RE.match(text):
            cx, cy = to_px(reg, pt.x, pt.y)
            hw = len(text) * h * 0.36 * reg["ppm"] + 3; hh = h * 0.75 * reg["ppm"] + 2
            dr.rectangle([cx - hw, cy - hh, cx + hw, cy + hh], fill=(255, 255, 255))

    P = lambda p: [round(v, 1) for v in to_px(reg, *p)]
    gt = {
        "m_per_px": 1.0 / reg["ppm"],
        "registration": reg,
        "walls": [[P(c) for c in w] for w in g["walls"]],
        "rooms": [{"id": r["id"], "name": r["name"], "polygon": [P(c) for c in r["polygon"]],
                   "area_m2": round(r["area"], 2)} for r in g["rooms"]],
        "doors": [{"p1": P(d["p1"]), "p2": P(d["p2"])} for d in g["doors"]],
        "windows": [{"p1": P(w["p1"]), "p2": P(w["p2"])} for w in g["windows"]],
        "fixtures": [{"type": f["type"], "x": P((f["x"], f["y"]))[0], "y": P((f["x"], f["y"]))[1]}
                     for f in g["fixtures"]],
    }
    name = os.path.splitext(os.path.basename(dxf))[0]
    td = os.path.join(out_dir, name)
    wall_ink = check_alignment(png, gt["walls"])
    os.makedirs(td, exist_ok=True)
    im.save(os.path.join(td, "drawing.png"))
    with open(os.path.join(td, "ground_truth.json"), "w", encoding="utf8") as f:
        json.dump(gt, f, ensure_ascii=False)
    return {"task": name, "match": reg["match"], "scale_1_to": round(150 / 25.4 * 1000 / reg["ppm"]),
            "rooms": len(gt["rooms"]), "doors": len(gt["doors"]), "windows": len(gt["windows"]),
            "fixtures": len(gt["fixtures"]), "printed_scale": reg.get("printed_scale"), "wall_ink": wall_ink,
            "valid": wall_ink >= MIN_WALL_INK}


def _one(args):
    dxf, png, out = args
    name = os.path.splitext(os.path.basename(dxf))[0]
    if os.path.exists(os.path.join(out, name, "ground_truth.json")) and os.path.exists(os.path.join(out, name, "info.json")):
        return json.load(open(os.path.join(out, name, "info.json")))
    try:
        r = build_one(dxf, png, out)
        json.dump(r, open(os.path.join(out, name, "info.json"), "w"))
        return r
    except Exception as e:  # noqa: BLE001  (a few DXFs are malformed: skip them)
        return {"task": name, "error": f"{type(e).__name__}: {e}"[:300]}


def main():
    import argparse
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out", nargs="?", default="tasks")
    ap.add_argument("--procs", type=int, default=1)
    a = ap.parse_args()
    jobs = [(os.path.join(a.src, f), os.path.join(a.src, f[:-4] + ".png"), a.out) for f in sorted(os.listdir(a.src))
            if f.endswith(".dxf") and os.path.exists(os.path.join(a.src, f[:-4] + ".png"))]
    os.makedirs(a.out, exist_ok=True)
    rows = []
    with Pool(a.procs) as pool:
        for r in pool.imap_unordered(_one, jobs):
            print(r, flush=True)
            rows.append(r)
    rows.sort(key=lambda r: r["task"])
    with open(os.path.join(a.out, "index.json"), "w") as fh:
        json.dump(rows, fh, indent=1)


if __name__ == "__main__":
    main()
