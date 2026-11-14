"""Single-turn policy I/O for fine-tuning a small vision-language model (Qwen3-VL).

The model sees the masked drawing once and writes the whole schematic as compact JSON with
coordinates as integers in 0..1000 relative to the image (Qwen-VL's native convention):

  {"m_per_px":0.03387,
   "walls":[[[x,y],...],...],                         wall outlines (simplified)
   "rooms":[{"id":"2.01","name":"Zimmer","polygon":[[x,y],...]},...],
   "doors":[[x1,y1,x2,y2],...], "windows":[[x1,y1,x2,y2],...],
   "fixtures":{"wc":[[x,y],...],"washbasin":[...],...}}

to_text(): ground truth (pixels) -> target text.   from_text(): model reply -> schematic in pixels
for score.py. parse_json() rescues replies cut off by the token limit (adapted from policy_io.py in
github.com/AistisV/reinforcement-testing, MIT, (c) 2026 Aistis Verkauskas and the Junction 2026 team).
"""
from __future__ import annotations

import json
import math
import re

from shapely.geometry import Polygon

FIXTURES = ("wc", "washbasin", "bathtub", "shower", "kitchen")
ALIASES = {"toilet": "wc", "toilets": "wc", "sink": "washbasin", "lavabo": "washbasin", "bath": "bathtub",
           "tub": "bathtub", "stove": "kitchen", "hob": "kitchen", "cooker": "kitchen"}

PROMPT = """Digitise this construction floor plan into ONE compact JSON schematic. Output only the JSON.
Coordinates are integers in 0..1000 relative to the image: [0,0] top-left, [1000,1000] bottom-right
(the image is {W}x{H} px). m_per_px is metres per ORIGINAL pixel, read from the printed scale or scale bar.
{{"m_per_px":<number>,
 "walls":[[[x,y],...],...],                 outline polygon of every wall piece
 "rooms":[{{"id":"2.01","name":"Zimmer","polygon":[[x,y],...]}},...],   every numbered room: inner face of its walls,
                                            id and name exactly as printed (name null if none)
 "doors":[[x1,y1,x2,y2],...],               door opening across the wall, jamb to jamb
 "windows":[[x1,y1,x2,y2],...],             one segment along each window
 "fixtures":{{"wc":[[x,y],...],"washbasin":[...],"bathtub":[...],"shower":[...],"kitchen":[...]}}}}"""


def prompt_for(W, H):
    return PROMPT.format(W=W, H=H)


MODEL_MAX_SIDE = 2048   # ~3.5k image tokens for Qwen3-VL; coordinates are relative, so resizing is harmless


def model_image(img, max_side=MODEL_MAX_SIDE):
    """The exact image the policy sees, in training and at inference."""
    img = img.convert("RGB")
    s = max_side / max(img.size)
    return img.resize((round(img.width * s), round(img.height * s)), 3) if s < 1 else img


def _simplify(poly, tol):
    try:
        p = Polygon(poly).buffer(0)
        if p.geom_type == "MultiPolygon":
            p = max(p.geoms, key=lambda g: g.area)
        p = p.simplify(tol)
        if p.is_empty or p.area <= 0:
            return None
        return [list(c) for c in list(p.exterior.coords)[:-1]]
    except Exception:
        return None


def to_text(gt: dict, W: int, H: int, wall_tol_px=2.0) -> str:
    """Ground-truth schematic (pixels) -> the compact target text."""
    nx = lambda x: int(round(x * 1000 / W)); ny = lambda y: int(round(y * 1000 / H))
    P = lambda pts: [[nx(x), ny(y)] for x, y in pts]
    walls = [P(w) for w in (_simplify(w, wall_tol_px) for w in gt["walls"]) if w and len(w) >= 3]
    rooms = []
    for r in gt["rooms"]:
        poly = _simplify(r["polygon"], 1.0)
        if poly:
            rooms.append({"id": r.get("id"), "name": r.get("name"), "polygon": P(poly)})
    rooms.sort(key=lambda r: (min(p[1] for p in r["polygon"]) // 25, min(p[0] for p in r["polygon"])))
    seg = lambda o: [nx(o["p1"][0]), ny(o["p1"][1]), nx(o["p2"][0]), ny(o["p2"][1])]
    key = lambda s: (min(s[1], s[3]) // 25, min(s[0], s[2]))
    fx = {}
    for f in sorted(gt["fixtures"], key=lambda f: (f["y"], f["x"])):
        fx.setdefault(f["type"], []).append([nx(f["x"]), ny(f["y"])])
    out = {"m_per_px": round(gt["m_per_px"], 6), "walls": walls, "rooms": rooms,
           "doors": sorted((seg(d) for d in gt["doors"]), key=key),
           "windows": sorted((seg(w) for w in gt["windows"]), key=key), "fixtures": fx}
    return json.dumps(out, ensure_ascii=False, separators=(",", ":"))


def parse_json(text):
    """JSON object from a model reply; if cut off, keep everything up to the last complete element."""
    t = re.sub(r"```(?:json)?", "", text or "")
    i = t.find("{")
    if i < 0:
        return {}
    t = t[i:]
    try:
        v = json.loads(t)
        return v if isinstance(v, dict) else {}
    except Exception:
        pass
    stack, in_str, esc, cuts = [], False, False, []
    for k, ch in enumerate(t):
        if in_str:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': in_str = False
            continue
        if ch == '"': in_str = True
        elif ch in "{[": stack.append(ch)
        elif ch in "}]":
            if not stack: break
            stack.pop()
            cuts.append((k + 1, list(stack)))
            if not stack: break
    for pos, stk in reversed(cuts[-80:]):
        try:
            v = json.loads(t[:pos] + "".join("}" if c == "{" else "]" for c in reversed(stk)))
            return v if isinstance(v, dict) else {}
        except Exception:
            continue
    return {}


def _f(v):
    try:
        v = float(v)
        return v if math.isfinite(v) else None
    except Exception:
        return None


def from_text(text: str, W: int, H: int) -> dict:
    """Model reply -> schematic in original pixels (score.py format). Never raises."""
    s = parse_json(text)
    px = lambda p: [p[0] * W / 1000, p[1] * H / 1000]

    def pts(v):
        out = []
        for p in v if isinstance(v, list) else []:
            if isinstance(p, (list, tuple)) and len(p) >= 2 and _f(p[0]) is not None and _f(p[1]) is not None:
                out.append(px([_f(p[0]), _f(p[1])]))
        return out

    def segs(v):
        out = []
        for q in v if isinstance(v, list) else []:
            if isinstance(q, (list, tuple)) and len(q) >= 4 and all(_f(c) is not None for c in q[:4]):
                out.append({"p1": px([_f(q[0]), _f(q[1])]), "p2": px([_f(q[2]), _f(q[3])])})
        return out

    rooms = []
    for r in s.get("rooms") if isinstance(s.get("rooms"), list) else []:
        if isinstance(r, dict):
            poly = pts(r.get("polygon"))
            if len(poly) >= 3:
                rooms.append({"id": r.get("id"), "name": r.get("name"), "polygon": poly})
    fixtures = []
    fx = s.get("fixtures")
    if isinstance(fx, dict):
        for t, v in fx.items():
            t = ALIASES.get(str(t).lower(), str(t).lower())
            fixtures += [{"type": t, "x": p[0], "y": p[1]} for p in pts(v)]
    return {"m_per_px": _f(s.get("m_per_px")) or 0.0,
            "walls": [w for w in (pts(w) for w in (s.get("walls") if isinstance(s.get("walls"), list) else [])) if len(w) >= 3],
            "rooms": rooms, "doors": segs(s.get("doors")), "windows": segs(s.get("windows")), "fixtures": fixtures}
