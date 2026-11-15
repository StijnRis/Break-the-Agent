"""The environment: one episode = one floor-plan drawing. Shared by the MCP server (judges' harness),
the Gemini runner (agent.py) and the evaluation script, so every agent sees the same tools and rules.

The ground truth is loaded only when the episode is scored (after submit / at the end), never
while the agent is acting.
"""
from __future__ import annotations

import json
import math
import os
import time

from PIL import Image, ImageDraw

from .render import overlay
from .score import score

MAX_CALLS = 30
MAX_SECONDS = 8 * 60
VIEW_MAX = 1280

INSTRUCTIONS = """You are a construction-drawing digitiser. You get a raster floor plan (one storey of a Swiss
apartment building) and must produce a FORMAL SCHEMATIC of it: a machine-readable model that downstream
code will use to compute room areas, counts of doors / windows / sanitary fixtures, adjacency, etc.

All coordinates are in PIXELS of the original drawing image (origin top-left, x right, y down).
The image is {W} x {H} px. Printed room areas have been removed from the drawing on purpose: you must
derive geometry yourself. The drawing contains a scale bar, a printed scale (title block) and a legend.

Schematic JSON format:
{{
  "m_per_px": <metres per pixel, derived from the scale bar / printed scale>,
  "walls":   [ {{"p1":[x,y], "p2":[x,y], "thickness_px": t}}, ... ]   wall centre-line segments
              (a wall may also be given as a polygon [[x,y],...] of its outline),
  "rooms":   [ {{"id":"2.01", "name":"Zimmer", "polygon":[[x,y],...]}}, ... ]  every numbered room;
               polygon = the room's interior floor outline (inside face of walls); name = printed label
               exactly as written (null if there is none),
  "doors":   [ {{"p1":[x,y], "p2":[x,y]}}, ... ]   the door OPENING across the wall, jamb to jamb
               (a double door counts as two doors: one segment per leaf),
  "windows": [ {{"p1":[x,y], "p2":[x,y]}}, ... ]   one segment along each window in the wall,
  "fixtures":[ {{"type": t, "x":x, "y":y}}, ... ]  centre of each symbol; t in
               wc | washbasin | bathtub | shower | kitchen (one per kitchen counter with the 4-circle hob symbol)
}}

How you are scored: each class is matched one-to-one against a surveyed ground truth, with graded
credit that falls off smoothly with distance (walls: partial credit out to ~60 cm, full near 15 cm;
rooms by polygon overlap + correct label; doors/windows by midpoint distance, full credit within
20 cm fading to zero at 1 m; fixtures by type and position, full within 25 cm fading to zero at
1.5 m; room areas computed with YOUR m_per_px, full credit within 5 % fading to zero at 30 %).
Missing elements and spurious elements both lower the score. Only the schematic passed to submit_schematic counts;
if you never submit, the score is 0. Speed can reduce earned credit by up to 10%: submit within
5 minutes for full credit; the multiplier declines linearly to 0.90 at the 8-minute deadline.

Tools: get_task (instructions and overview), view_region (zoom with pixel rulers), estimate_scale (derive
scale from the printed ratio or scale bar), read_room_labels (OCR room numbers, names and their pixel
locations, optionally in a crop), segment_rooms (give a seed point inside each room and your m_per_px to
get proposed outlines split at walls and door openings), measure_area (area in m2 at a given scale),
preview_schematic (overlay your draft for visual review), and submit_schematic (final answer; ends the
episode). You have at most {T} tool calls."""


def rulers(img: Image.Image, x0, y0, x1, y1) -> Image.Image:
    """Scale a crop to fit VIEW_MAX and add pixel-coordinate rulers along the edges."""
    w, h = img.size
    s = min(VIEW_MAX / max(w, h), 4.0)
    img = img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
    M = 40
    out = Image.new("RGB", (img.width + M, img.height + M), "white")
    out.paste(img, (M, M))
    d = ImageDraw.Draw(out)
    span = max(x1 - x0, y1 - y0)
    step = next((st for st in (10, 20, 25, 50, 100, 200, 250, 500) if span / st <= 14), 500)
    for gx in range(int(x0 // step * step), int(x1) + 1, step):
        if gx < x0:
            continue
        px = M + (gx - x0) * s
        d.line([(px, M - 6), (px, out.height)], fill=(255, 0, 0) if gx % (step * 2) == 0 else (255, 160, 160), width=1)
        d.text((px + 2, 4), str(gx), fill=(200, 0, 0))
    for gy in range(int(y0 // step * step), int(y1) + 1, step):
        if gy < y0:
            continue
        py = M + (gy - y0) * s
        d.line([(M - 6, py), (out.width, py)], fill=(255, 0, 0) if gy % (step * 2) == 0 else (255, 160, 160), width=1)
        d.text((2, py + 2), str(gy), fill=(200, 0, 0))
    return out


def _loads(v):
    return json.loads(v) if isinstance(v, str) else v


class Episode:
    """Tool calls return (text, PIL image or None). Errors are returned as text, never raised."""

    def __init__(self, task_dir: str, gt_path: str | None = None, max_calls: int = MAX_CALLS):
        self.dir = task_dir
        self.task = os.path.basename(os.path.normpath(task_dir))
        self.drawing = os.path.join(task_dir, "drawing.png")
        self.img = Image.open(self.drawing).convert("RGB")
        self.gt_path = gt_path or os.path.join(task_dir, "ground_truth.json")
        self.max_calls = max_calls
        self.calls = 0
        self.started_at = time.monotonic()
        self.submitted = None
        self.last_preview = None
        self.trace = []

    @property
    def done(self):
        return self.submitted is not None

    def instructions(self) -> str:
        W, H = self.img.size
        return INSTRUCTIONS.format(W=W, H=H, T=self.max_calls)

    def _clip(self, a):
        W, H = self.img.size
        x0, y0, x1, y1 = (float(a.get(k) if a.get(k) is not None else d)
                          for k, d in (("x0", 0), ("y0", 0), ("x1", W), ("y1", H)))
        x0, x1 = sorted((max(0, min(W, x0)), max(0, min(W, x1))))
        y0, y1 = sorted((max(0, min(H, y0)), max(0, min(H, y1))))
        if x1 - x0 < 8 or y1 - y0 < 8:
            raise ValueError("region too small")
        return x0, y0, x1, y1

    def call(self, name: str, args: dict):
        if self.done:
            return "episode is over: the schematic was already submitted", None
        self.calls += 1
        if self.elapsed_seconds >= MAX_SECONDS and name != "submit_schematic":
            return "time budget exhausted: only submit_schematic is accepted now", None
        left = self.max_calls - self.calls
        if left < 0 and name != "submit_schematic":
            return "tool budget exhausted: only submit_schematic is accepted now", None
        try:
            text, img = self._call(name, args or {})
        except Exception as e:  # noqa: BLE001
            text, img = f"ERROR: {type(e).__name__}: {e}", None
        a = {k: (f"<{len(v)} chars>" if isinstance(v, str) and len(v) > 200 else v) for k, v in (args or {}).items()}
        self.trace.append({"call": self.calls, "tool": name, "args": a, "result": text[:500]})
        if not self.done and 0 <= left <= 3:
            text += f"\n[{left} tool calls left - submit your schematic with submit_schematic soon]"
        return text, img

    def _call(self, name, a):
        if name == "estimate_scale":
            from . import cv
            texts = cv.ocr(self.img)
            printed = cv.printed_scale(texts)
            bar = cv.scale_bar(self.img)
            ppm = printed or bar
            return json.dumps({"pixels_per_metre": round(ppm, 4) if ppm else None,
                               "m_per_px": round(1.0 / ppm, 8) if ppm else None,
                               "source": "printed scale" if printed else ("scale bar" if bar else None)}), None
        if name == "read_room_labels":
            from . import cv
            texts = cv.ocr(self.img)
            region = None
            if any(a.get(k) is not None for k in ("x0", "y0", "x1", "y1")):
                region = self._clip(a)
            labels = cv.room_labels(texts, region)
            result = [{"id": r["id"], "name": r["name"], "x": round(r["xy"][0], 1),
                       "y": round(r["xy"][1], 1)} for r in labels]
            return json.dumps(result, ensure_ascii=False), None
        if name == "view_region":
            x0, y0, x1, y1 = self._clip(a)
            return f"crop ({x0:.0f},{y0:.0f})-({x1:.0f},{y1:.0f})", rulers(self.img.crop((x0, y0, x1, y1)), x0, y0, x1, y1)
        if name == "measure_area":
            poly = _loads(a["polygon"]); mpp = float(a["m_per_px"])
            if len(poly) < 3 or not (mpp > 0 and math.isfinite(mpp)):
                raise ValueError("need >= 3 points and m_per_px > 0")
            px = abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]))) / 2
            return json.dumps({"area_px": round(px, 1), "area_m2": round(px * mpp * mpp, 3)}), None
        if name == "segment_rooms":
            from . import cv
            seeds = [[float(v) for v in s[:2]] for s in _loads(a["seeds"]) if isinstance(s, (list, tuple)) and len(s) >= 2][:150]
            if not seeds:
                raise ValueError('give seeds as [[x, y], ...]')
            mpp = a.get("m_per_px")
            if mpp:                       # scale known: building footprint + one region per seed
                ppm = 1.0 / float(mpp)
                ink, walls, _, _ = cv.masks(self.img)
                rooms, _, _ = cv.auto_rooms(self.img, ppm, walls, seeds=seeds, ink=ink)
                by = {r["label_id"]: r for r in rooms}
                res = [{"polygon": [[round(x, 1), round(y, 1)] for x, y in by[i + 1]["polygon"]], "area_px": by[i + 1]["area_px"],
                        "closed": True} if i + 1 in by else {"polygon": [], "area_px": 0.0, "closed": False}
                       for i in range(len(seeds))]
            else:
                res = cv.segment_rooms(self.img, seeds)
            ov = overlay(self.drawing, {"rooms": [{"id": str(i), "name": "", "polygon": r["polygon"]} for i, r in enumerate(res) if r["polygon"]]})
            ov.thumbnail((VIEW_MAX, VIEW_MAX))
            return json.dumps([{"seed": i, "polygon": r["polygon"], "area_px": round(r["area_px"]),
                                "closed": r["closed"]} for i, r in enumerate(res)]) + \
                "\nRegions can be wrong (open plan, missing walls): check the overlay and correct polygons yourself.", ov
        if name in ("preview_schematic", "submit_schematic"):
            sch = _loads(a["schematic_json"] if "schematic_json" in a else a["schematic"])
            if not isinstance(sch, dict):
                raise ValueError("schematic must be a JSON object")
            counts = {k: len(sch.get(k) or []) for k in ("walls", "rooms", "doors", "windows", "fixtures")}
            if name == "submit_schematic":
                self.submitted = sch
                return f"submitted: {counts}. The episode is over.", None
            self.last_preview = sch
            x0, y0, x1, y1 = self._clip(a)
            ov = overlay(self.drawing, sch, crop=(x0, y0, x1, y1))
            return f"preview counts {counts}, m_per_px={sch.get('m_per_px')}", rulers(ov, x0, y0, x1, y1)
        return f"unknown tool {name}", None

    @property
    def elapsed_seconds(self) -> float:
        return time.monotonic() - self.started_at

    def result(self, elapsed_seconds: float | None = None) -> dict:
        """Score the submitted schematic (an episode without a submission scores as empty = 0)."""
        gt = json.load(open(self.gt_path, encoding="utf8"))
        elapsed = self.elapsed_seconds if elapsed_seconds is None else elapsed_seconds
        res = score(gt, self.submitted, self.img.size, elapsed)
        return {"task": self.task, "submitted": self.submitted is not None, "tool_calls": self.calls, **res}
