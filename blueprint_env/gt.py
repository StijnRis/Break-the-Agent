"""Ground-truth extraction: Swiss Dwellings DXF -> formal schematic (metres, DXF frame),
plus registration of the DXF frame onto the PNG drawing (pixel frame)."""
from __future__ import annotations

import math
import re

import ezdxf
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

AREA_RE = re.compile(r"^\s*[\d.,]+\s*m")
NUM_RE = re.compile(r"^\s*\d+\.\d+\s*$")


def _pts(e):
    return [(float(x), float(y)) for x, y in e.get_points("xy")]


def classify_fixture(rect: Polygon, parts: list) -> str:
    """parts: list of ('circle', r) / ('poly', npts). Signatures verified visually against the legend."""
    circles = [r for k, r in parts if k == "circle"]
    polys = [n for k, n in parts if k == "poly"]
    w, h = sorted(_rect_dims(rect))
    if len([r for r in circles if r > 0.06]) >= 3:
        return "kitchen"
    if sum(1 for n in polys if n == 2) >= 5:
        return "stairs"
    if any(n >= 60 for n in polys):
        return "bathtub"
    if any(40 <= n < 60 for n in polys):
        return "washbasin" if circles else "wc"
    if circles:
        return "shower"
    # plain rectangles (appliances, cupboards, shafts) are drawn as empty boxes, unlike the legend's
    # washing-machine symbol (box + circle), so they are not scored as fixtures
    return "other"


def _rect_dims(poly: Polygon):
    m = poly.minimum_rotated_rectangle
    c = list(m.exterior.coords)
    return (LineString(c[0:2]).length, LineString(c[1:3]).length)


def extract(dxf_path: str) -> dict:
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    walls = [Polygon(_pts(e)).buffer(0) for e in msp.query('LWPOLYLINE[layer=="WALL"]') if len(_pts(e)) >= 3]
    wall_union = unary_union(walls)

    # rooms
    texts = [(e.dxf.text.strip(), Point(e.dxf.insert[0], e.dxf.insert[1]), float(e.dxf.height))
             for e in msp.query('TEXT[layer=="ROOM_TEXT"]')]
    rooms = []
    for e in msp.query('LWPOLYLINE[layer=="ROOM_OUTLINE"]'):
        p = _pts(e)
        if len(p) < 3:
            continue
        poly = Polygon(p).buffer(0)
        if poly.area < 0.8:
            continue
        inside = [t for t in texts if poly.contains(t[1])]
        rid = next((t for t, _, _ in inside if NUM_RE.match(t)), None)
        name = next((t for t, _, _ in inside if not NUM_RE.match(t) and not AREA_RE.match(t)
                     and not t.lower().startswith(("whg", "app", "unit", "wohnung"))), None)
        rooms.append({"id": rid, "name": name, "polygon": [list(c) for c in poly.exterior.coords[:-1]],
                      "area": poly.area})

    # doors: swing ARC centred on the hinge; the 2-point DOOR line is the open leaf. The opening
    # (jamb to jamb, in the wall) runs from the hinge to the arc end-point that is NOT the leaf tip.
    leaves = [_pts(e) for e in msp.query('LWPOLYLINE[layer=="DOOR"]') if len(_pts(e)) == 2 and not e.closed]
    doors = []
    for a in msp.query('ARC[layer=="DOOR"]'):
        c = (float(a.dxf.center[0]), float(a.dxf.center[1])); r = float(a.dxf.radius)
        ends = [(c[0] + r * math.cos(math.radians(t)), c[1] + r * math.sin(math.radians(t)))
                for t in (a.dxf.start_angle, a.dxf.end_angle)]
        tips = [q for L in leaves for q in L if min(math.dist(L[0], c), math.dist(L[1], c)) < 0.05]
        if tips:
            tip = max(tips, key=lambda q: math.dist(q, c))
            far = max(ends, key=lambda q: math.dist(q, tip))
        else:
            far = ends[0]
        doors.append({"p1": list(c), "p2": list(far)})

    # windows: closed rectangle -> centre line along its long axis
    windows = []
    for e in msp.query('LWPOLYLINE[layer=="WINDOW"]'):
        p = _pts(e)
        if not e.closed or len(p) < 4:
            continue
        a, b, c, d = p[:4]
        if math.dist(a, b) >= math.dist(b, c):
            p1 = ((a[0] + d[0]) / 2, (a[1] + d[1]) / 2); p2 = ((b[0] + c[0]) / 2, (b[1] + c[1]) / 2)
        else:
            p1 = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); p2 = ((c[0] + d[0]) / 2, (c[1] + d[1]) / 2)
        windows.append({"p1": list(p1), "p2": list(p2)})

    # fixtures: closed rectangle + contained parts
    rects = [e for e in msp.query('LWPOLYLINE[layer=="FIXTURE"]') if e.closed and len(_pts(e)) >= 4]
    others = [e for e in msp.query('*[layer=="FIXTURE"]') if not (e.dxftype() == "LWPOLYLINE" and e.closed)]
    fixtures = []
    for r in rects:
        pg = Polygon(_pts(r))
        zone = pg.buffer(0.03)
        parts = []
        for o in others:
            if o.dxftype() == "CIRCLE":
                if zone.contains(Point(o.dxf.center[0], o.dxf.center[1])):
                    parts.append(("circle", float(o.dxf.radius)))
            elif o.dxftype() == "LWPOLYLINE":
                q = _pts(o)
                if len(q) >= 2 and zone.contains(LineString(q)):
                    parts.append(("poly", len(q)))
        t = classify_fixture(pg, parts)
        if t in ("stairs", "other"):
            continue  # stairs / lift boxes are not sanitary or kitchen fixtures
        c = pg.centroid
        fixtures.append({"type": t, "x": c.x, "y": c.y})

    return {"walls": [[list(c) for c in w.exterior.coords[:-1]] for w in
                      (wall_union.geoms if hasattr(wall_union, "geoms") else [wall_union])],
            "rooms": rooms, "doors": doors, "windows": windows, "fixtures": fixtures,
            "_wall_union": wall_union, "_texts": texts}


# ---------------------------------------------------------------- registration
DPI = 150.0


def _raster_walls(wall_union, ppm: float, pad: int = 4):
    minx, miny, maxx, maxy = wall_union.bounds
    W = int((maxx - minx) * ppm) + 2 * pad; H = int((maxy - miny) * ppm) + 2 * pad
    im = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(im)
    geoms = wall_union.geoms if hasattr(wall_union, "geoms") else [wall_union]
    for g in geoms:
        dr.polygon([((x - minx) * ppm + pad, (maxy - y) * ppm + pad) for x, y in g.exterior.coords], fill=255)
        for i in g.interiors:
            dr.polygon([((x - minx) * ppm + pad, (maxy - y) * ppm + pad) for x, y in i.coords], fill=0)
    return np.asarray(im, dtype=np.float32) / 255.0, (minx, maxy, pad)


def _xcorr(img: np.ndarray, tmpl: np.ndarray):
    H, W = img.shape
    F = np.fft.rfft2(img, s=(H, W)) * np.conj(np.fft.rfft2(tmpl, s=(H, W)))
    c = np.fft.irfft2(F, s=(H, W))
    idx = np.unravel_index(np.argmax(c), c.shape)
    return c[idx] / max(tmpl.sum(), 1), idx


def register(png_path: str, wall_union, scales=None) -> dict:
    """Find px = (x - x0) * ppm + ox ; py = (y0 - y) * ppm + oy mapping DXF metres -> PNG pixels.
    scales: candidate 1:N drawing scales (default: all common ones). build_tasks passes the scale
    printed in the title block, which stops the correlation locking onto a wrong scale."""
    im = np.asarray(Image.open(png_path).convert("L"), dtype=np.float32)
    dark = (im < 90).astype(np.float32)
    best = None
    for N in (scales or [50, 75, 100, 125, 150, 200, 250, 300]):
        ppm = DPI / 25.4 * 1000.0 / N
        tm, (minx, maxy, pad) = _raster_walls(wall_union, ppm)
        if tm.shape[0] >= dark.shape[0] or tm.shape[1] >= dark.shape[1]:
            continue
        score, (dy, dx) = _xcorr(dark, tm)
        if best is None or score > best[0]:
            best = (score, ppm, dx, dy, minx, maxy, pad)
    # fine scale refinement
    score, ppm0, *_ = best
    for f in np.linspace(0.97, 1.03, 13):
        ppm = ppm0 * f
        tm, (minx, maxy, pad) = _raster_walls(wall_union, ppm)
        s, (dy, dx) = _xcorr(dark, tm)
        if s > best[0]:
            best = (s, ppm, dx, dy, minx, maxy, pad)
    score, ppm, dx, dy, minx, maxy, pad = best
    return {"ppm": float(ppm), "x0": float(minx), "y0": float(maxy), "ox": int(dx + pad), "oy": int(dy + pad),
            "match": float(score)}


def to_px(reg, x, y):
    return ((x - reg["x0"]) * reg["ppm"] + reg["ox"], (reg["y0"] - y) * reg["ppm"] + reg["oy"])


def to_m(reg, px, py):
    return ((px - reg["ox"]) / reg["ppm"] + reg["x0"], reg["y0"] - (py - reg["oy"]) / reg["ppm"])
