"""Export the data the demo video animates: one plan, its ground truth, the
reference and Gemini schematics, Gemini's tool trace, and the summary numbers.

    python video/build_data.py [--task site1047_bldg2154_floor9740] [--run run1]

Writes video/data.js (window.DATA = {...}) and video/media/plan.jpg.
"""
import argparse
import json
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def r1(v):
    return round(float(v), 1)


def poly(pts):
    return [[r1(x), r1(y)] for x, y in pts]


def walls(ws):
    out = []
    for w in ws or []:
        if isinstance(w, dict) and "p1" in w:
            out.append({"p1": [r1(c) for c in w["p1"]], "p2": [r1(c) for c in w["p2"]], "t": w.get("thickness_px", 10)})
        else:
            out.append(poly(w))
    return out


def schematic(s):
    s = s or {}
    seg = lambda xs: [{"p1": [r1(c) for c in d["p1"]], "p2": [r1(c) for c in d["p2"]]} for d in xs or []]
    return {
        "m_per_px": s.get("m_per_px"),
        "walls": walls(s.get("walls")),
        "rooms": [{"id": r.get("id"), "name": r.get("name"), "polygon": poly(r["polygon"])} for r in s.get("rooms") or [] if r.get("polygon")],
        "doors": seg(s.get("doors")),
        "windows": seg(s.get("windows")),
        "fixtures": [{"type": f.get("type"), "x": r1(f["x"]), "y": r1(f["y"])} for f in s.get("fixtures") or []],
    }


def clean(text):
    """Keep the readable sentences of a reasoning snippet."""
    lines = [l.strip() for l in (text or "").splitlines()]
    lines = [l for l in lines if len(l) > 12 and not re.fullmatch(r"[\W\w]{0,12}>|.*\.png\).*", l)]
    return lines[:4]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="site1047_bldg2154_floor9740")
    ap.add_argument("--run", default="run1")
    ap.add_argument("--agent", default="gemini-3.1-pro-preview")
    a = ap.parse_args()

    tdir = ROOT / "tasks" / a.task
    gt = load(tdir / "ground_truth.json")
    ref = load(ROOT / "runs" / "reference-cv" / a.task / "episode.json")
    ag = load(ROOT / "runs" / a.agent / a.task / a.run / "episode.json")
    summary = load(ROOT / "results" / "summary.json")

    img = Image.open(tdir / "drawing.png").convert("RGB")
    W, H = img.size
    (OUT / "media").mkdir(exist_ok=True)
    img.resize((W * 2 // 3, H * 2 // 3), Image.LANCZOS).save(OUT / "media" / "plan.jpg", quality=88)

    # building bounding box from the ground-truth rooms, for framing
    xs = [p[0] for r in gt["rooms"] for p in r["polygon"]]
    ys = [p[1] for r in gt["rooms"] for p in r["polygon"]]
    bbox = [min(xs), min(ys), max(xs), max(ys)]

    trace = []
    seen = set()
    for t in ag["trace"]:
        thought = [l for l in clean(t.get("text")) if l not in seen]
        seen.update(thought)
        trace.append({"tool": t.get("tool"), "args": {k: v for k, v in (t.get("args") or {}).items() if k in ("x0", "y0", "x1", "y1", "seeds", "m_per_px")}, "thought": thought})

    rows = summary["rows"]
    data = {
        "task": a.task,
        "size": [W, H],
        "bbox": [r1(v) for v in bbox],
        "gt": schematic(gt),
        "ref": {"reward": ref["result"]["reward"], "components": ref["result"].get("components"), "schematic": schematic(ref["schematic"])},
        "agent": {"model": a.agent, "reward": ag["result"]["reward"], "seconds": ag["result"]["seconds"],
                  "components": ag["result"].get("components"), "schematic": schematic(ag["schematic"]), "trace": trace},
        "summary": {k: {"reward": v["reward_mean"], "runs": v.get("per_run_means"), "components": v.get("components")} for k, v in rows.items()},
        "exploits": summary.get("exploits", {}),
    }
    (OUT / "data.js").write_text("window.DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"wrote video/data.js ({(OUT / 'data.js').stat().st_size // 1024} KB) and video/media/plan.jpg")


if __name__ == "__main__":
    main()
