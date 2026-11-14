"""Reward: how correctly the agent's formal schematic reproduces the drawing.

Everything is matched one-to-one (Hungarian) against the DXF ground truth, distances are judged in
real metres (using the TRUE scale, so placement is measured independently of calibration), and each
class gets an F1 score, so both missing objects and spammed objects cost reward.

    walls     0.25  tolerant mask F1 (0.15 m tolerance)
    rooms     0.25  polygon IoU match, soft credit IoU 0.5 -> 0.9, half credit if label wrong
    doors     0.15  opening midpoint within 0.4 m
    windows   0.15  midpoint within 0.4 m
    fixtures  0.10  same type, centre within 0.5 m
    areas     0.10  fraction of GT rooms whose matched polygon area, computed with the AGENT's own
                    scale (m_per_px), is within 5 %  -> rewards calibration only together with rooms
    speed           multiplier on earned geometry credit: 1.00 through 5 minutes, declining to 0.90
                    at the 8-minute deadline
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation
from scipy.optimize import linear_sum_assignment
from shapely.geometry import Polygon

# Geometry remains the task reward.  Speed scales that earned reward by 0.90--1.00,
# so a fast empty or junk submission never earns credit on its own.
WEIGHTS = {"walls": 0.25, "rooms": 0.25, "doors": 0.15, "windows": 0.15, "fixtures": 0.10, "areas": 0.10}
MAX_ITEMS = 2000
SPEED_FULL_CREDIT_SECONDS = 5 * 60
SPEED_ZERO_CREDIT_SECONDS = 8 * 60


def _f1(tp: float, n_pred: int, n_gt: int) -> float:
    if n_pred + n_gt == 0:
        return 1.0
    return 2.0 * tp / (n_pred + n_gt)


def _num(v):
    v = float(v)
    if not math.isfinite(v):
        raise ValueError
    return v


def _pt(p):
    return (_num(p[0]), _num(p[1]))


def _poly(pts):
    try:
        pg = Polygon([_pt(p) for p in pts])
        pg = pg if pg.is_valid else pg.buffer(0)
        return pg if (not pg.is_empty and pg.area > 0) else None
    except Exception:
        return None


def _norm(s):
    """Label comparison ignores case, accents/umlauts and extra spaces ('Pièce' == 'piece', 'Küche' == 'Kuche')."""
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return " ".join(s.lower().split())


# ---------------------------------------------------------------- walls
def _wall_masks(gt, pred_walls, size, mpp, ds=2):
    W, H = size[0] // ds, size[1] // ds
    g = Image.new("1", (W, H), 0); dg = ImageDraw.Draw(g)
    for w in gt["walls"]:
        dg.polygon([(x / ds, y / ds) for x, y in w], fill=1)
    p = Image.new("1", (W, H), 0); dp = ImageDraw.Draw(p)
    max_t = 1.0 / mpp  # cap wall thickness at 1 m
    n = 0
    for w in pred_walls[:MAX_ITEMS]:
        try:
            if isinstance(w, dict):
                a, b = _pt(w["p1"]), _pt(w["p2"])
                t = min(max(_num(w.get("thickness_px", 0.2 / mpp)), 1.0), max_t)
                dp.line([(a[0] / ds, a[1] / ds), (b[0] / ds, b[1] / ds)], fill=1, width=max(1, int(round(t / ds))))
            else:
                pts = [_pt(q) for q in w][:MAX_ITEMS]
                if len(pts) >= 3:
                    dp.polygon([(x / ds, y / ds) for x, y in pts], fill=1)
            n += 1
        except Exception:
            continue
    return np.asarray(g, bool), np.asarray(p, bool)


def score_walls(gt, pred, size):
    mpp = gt["m_per_px"]
    G, P = _wall_masks(gt, pred.get("walls") or [], size, mpp)
    if P.sum() == 0:
        return 0.0, {"precision": 0.0, "recall": 0.0}
    r = max(1, int(round(0.15 / mpp / 2)))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disk = xx ** 2 + yy ** 2 <= r * r
    prec = (P & binary_dilation(G, disk)).sum() / P.sum()
    rec = (G & binary_dilation(P, disk)).sum() / max(G.sum(), 1)
    f = 0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec)
    return float(f), {"precision": round(float(prec), 3), "recall": round(float(rec), 3)}


# ---------------------------------------------------------------- rooms + areas
def score_rooms(gt, pred):
    gp = [_poly(r["polygon"]) for r in gt["rooms"]]
    prs = []
    for r in (pred.get("rooms") or [])[:MAX_ITEMS]:
        try:
            pg = _poly(r["polygon"])
            if pg is not None:
                prs.append((r, pg))
        except Exception:
            continue
    if not prs:
        return 0.0, 0.0, {"matched": 0, "n_pred": 0, "n_gt": len(gp), "matches": []}
    iou = np.zeros((len(gp), len(prs)))
    for i, g in enumerate(gp):
        for j, (_, p) in enumerate(prs):
            if g.intersects(p):
                inter = g.intersection(p).area
                iou[i, j] = inter / (g.area + p.area - inter)
    ri, ci = linear_sum_assignment(-iou)
    credit = 0.0; area_ok = 0; matched = 0; matches = []
    try:
        mpp_agent = _num(pred.get("m_per_px", 0))
    except Exception:
        mpp_agent = 0.0
    for i, j in zip(ri, ci):
        if iou[i, j] < 0.5:
            continue
        matched += 1
        r, p = prs[j]
        g = gt["rooms"][i]
        name_ok = (g["name"] is None) or (_norm(r.get("name")) == _norm(g["name"]))
        c = min(1.0, (iou[i, j] - 0.5) / 0.4) * (1.0 if name_ok else 0.5)
        credit += c
        agent_area = p.area * mpp_agent ** 2
        a_ok = g["area_m2"] > 0 and abs(agent_area / g["area_m2"] - 1) <= 0.05
        area_ok += a_ok
        matches.append({"gt": g["id"], "iou": round(float(iou[i, j]), 3), "name_ok": bool(name_ok),
                        "gt_area": g["area_m2"], "agent_area": round(agent_area, 2), "area_ok": bool(a_ok)})
    rooms = _f1(credit, len(prs), len(gp))
    areas = area_ok / max(len(gp), 1)
    return rooms, areas, {"matched": matched, "n_pred": len(prs), "n_gt": len(gp), "matches": matches}


# ---------------------------------------------------------------- point-like objects
def _match_points(gpts, ppts, tol_px):
    if not gpts or not ppts:
        return 0
    D = np.array([[math.dist(g, p) for p in ppts] for g in gpts])
    ri, ci = linear_sum_assignment(D)
    return int(sum(D[i, j] <= tol_px for i, j in zip(ri, ci)))


def _mids(items):
    out = []
    for o in (items or [])[:MAX_ITEMS]:
        try:
            a, b = _pt(o["p1"]), _pt(o["p2"])
            out.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
        except Exception:
            continue
    return out


def score_segments(gt, pred, key, tol_m=0.4):
    g = _mids(gt[key]); p = _mids(pred.get(key))
    tp = _match_points(g, p, tol_m / gt["m_per_px"])
    return _f1(tp, len(p), len(g)), {"tp": tp, "n_pred": len(p), "n_gt": len(g)}


def score_fixtures(gt, pred, tol_m=0.5):
    tol = tol_m / gt["m_per_px"]
    preds = []
    for f in (pred.get("fixtures") or [])[:MAX_ITEMS]:
        try:
            preds.append((_norm(f["type"]), _pt((f["x"], f["y"]))))
        except Exception:
            continue
    tp = 0; per = {}
    for t in sorted({f["type"] for f in gt["fixtures"]} | {t for t, _ in preds}):
        gg = [(f["x"], f["y"]) for f in gt["fixtures"] if f["type"] == t]
        pp = [p for tt, p in preds if tt == t]
        k = _match_points(gg, pp, tol)
        tp += k; per[t] = {"tp": k, "n_pred": len(pp), "n_gt": len(gg)}
    return _f1(tp, len(preds), len(gt["fixtures"])), {"tp": tp, "n_pred": len(preds),
                                                      "n_gt": len(gt["fixtures"]), "per_type": per}


# ---------------------------------------------------------------- total
def speed_credit(elapsed_seconds: float | None) -> float:
    """Return bounded time credit; omitted timings are offline/replay evaluations."""
    if elapsed_seconds is None:
        return 1.0
    try:
        seconds = max(0.0, float(elapsed_seconds))
    except (TypeError, ValueError):
        return 0.0
    if seconds <= SPEED_FULL_CREDIT_SECONDS:
        return 1.0
    if seconds >= SPEED_ZERO_CREDIT_SECONDS:
        return 0.0
    return (SPEED_ZERO_CREDIT_SECONDS - seconds) / (SPEED_ZERO_CREDIT_SECONDS - SPEED_FULL_CREDIT_SECONDS)


def score(gt: dict, pred: dict | None, size, elapsed_seconds: float | None = None) -> dict:
    if not isinstance(pred, dict):
        pred = {}
    comp, det = {}, {}
    comp["walls"], det["walls"] = score_walls(gt, pred, size)
    comp["rooms"], comp["areas"], det["rooms"] = score_rooms(gt, pred)
    comp["doors"], det["doors"] = score_segments(gt, pred, "doors")
    comp["windows"], det["windows"] = score_segments(gt, pred, "windows")
    comp["fixtures"], det["fixtures"] = score_fixtures(gt, pred)
    comp["speed"] = speed_credit(elapsed_seconds)
    try:
        sc = _num(pred.get("m_per_px", 0)) / gt["m_per_px"]
    except Exception:
        sc = 0.0
    det["scale_ratio"] = round(sc, 4)
    det["elapsed_seconds"] = None if elapsed_seconds is None else round(float(elapsed_seconds), 3)
    quality = sum(WEIGHTS[k] * comp[k] for k in WEIGHTS)
    total = quality * (0.90 + 0.10 * comp["speed"])
    return {"reward": round(total, 4), "components": {k: round(v, 4) for k, v in comp.items()}, "details": det}
