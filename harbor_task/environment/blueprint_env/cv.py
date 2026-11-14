"""Classic computer vision on the drawing (no learning, no ground truth).

Used by the scripted reference solver (reference.py) and, for room segmentation, as an agent tool.
segment_rooms / _masks are adapted from cv_rooms.py in github.com/AistisV/reinforcement-testing
(MIT licence, (c) 2026 Aistis Verkauskas and the Junction 2026 team).
"""
from __future__ import annotations

import math

import cv2
import numpy as np
from skimage.segmentation import watershed

DPI = 150.0
STD_SCALES = (20, 25, 50, 100, 200, 250, 500)


def ppm_for(n: int) -> float:
    """pixels per metre of a 1:n drawing rendered at DPI."""
    return DPI / 0.0254 / n


def _rgb(img):
    return np.asarray(img.convert("RGB") if hasattr(img, "convert") else img)


def masks(img, T=3):
    """ink (any non-white stroke except the red apartment line) and walls (thick straight bands)."""
    rgb = _rgb(img)
    r, g, b = [rgb[..., i].astype(int) for i in range(3)]
    gray = (r + g + b) / 3
    red = (r - g > 60) & (r - b > 60)
    ink = ((gray < 200) & ~red).astype(np.uint8)
    L = max(11, int(round(min(rgb.shape[:2]) / 110)))
    thick = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((T, T), np.uint8))
    h = cv2.morphologyEx(thick, cv2.MORPH_OPEN, np.ones((1, L), np.uint8))
    v = cv2.morphologyEx(thick, cv2.MORPH_OPEN, np.ones((L, 1), np.uint8))
    walls = cv2.morphologyEx(h | v, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    return ink, walls, h, v


# ---------------------------------------------------------------- scale
def scale_bar(img):
    """Find the legend scale bar (black 0-2 m, white 2-4 m, black 4-10 m) and return px per metre, or None.
    The measured value is snapped to the nearest standard drawing scale if it is within 4 %."""
    rgb = _rgb(img)
    dark = (rgb.mean(2) < 80).astype(np.uint8)
    n, cc, st, _ = cv2.connectedComponentsWithStats(dark, 8)
    bars = [(st[i, 0], st[i, 1], st[i, 2], st[i, 3]) for i in range(1, n)
            if 3 <= st[i, 3] <= 16 and st[i, 2] >= 15 and st[i, 2] >= 4 * st[i, 3]
            and st[i, cv2.CC_STAT_AREA] >= 0.8 * st[i, 2] * st[i, 3]]
    best = None
    for a in bars:
        for b in bars:
            if b[0] <= a[0] or abs((a[1] + a[3] / 2) - (b[1] + b[3] / 2)) > 3:
                continue
            w1, gap, w2 = a[2], b[0] - (a[0] + a[2]), b[2]
            if abs(gap - w1) <= 0.15 * w1 + 2 and abs(w2 - 3 * w1) <= 0.15 * w2 + 2:
                ppm = (b[0] + b[2] - a[0]) / 10.0
                if best is None or a[1] > best[1]:
                    best = (ppm, a[1])
    if best is None:
        return None
    ppm = best[0]
    std = min((ppm_for(s) for s in STD_SCALES), key=lambda p: abs(p / ppm - 1))
    return std if abs(std / ppm - 1) <= 0.04 else ppm


# ---------------------------------------------------------------- walls
def wall_rects(h, v, min_len=6):
    """Wall mask -> axis-aligned rectangles (polygons), from the horizontal and vertical runs."""
    out = []
    for m, horiz in ((h, True), (v, False)):
        n, cc, st, _ = cv2.connectedComponentsWithStats(m, 8)
        for i in range(1, n):
            x, y, w, hh = st[i, :4]
            if max(w, hh) < min_len:
                continue
            # a component can be an L / T: split its box into maximal rectangles via row/col profiles
            sub = (cc[y:y + hh, x:x + w] == i)
            prof = sub.sum(1) if horiz else sub.sum(0)
            # runs of rows (or cols) with similar extent
            start = 0
            for k in range(1, len(prof) + 1):
                if k == len(prof) or abs(int(prof[k]) - int(prof[start])) > 3:
                    seg = sub[start:k] if horiz else sub[:, start:k]
                    ys, xs = np.nonzero(seg)
                    if len(xs):
                        if horiz:
                            x0, x1, y0, y1 = x + xs.min(), x + xs.max() + 1, y + start, y + k
                        else:
                            x0, x1, y0, y1 = x + start, x + k, y + ys.min(), y + ys.max() + 1
                        out.append([[float(x0), float(y0)], [float(x1), float(y0)], [float(x1), float(y1)], [float(x0), float(y1)]])
                    start = k
    return out


# ---------------------------------------------------------------- rooms
def footprint(walls, ppm, ink=None):
    """Building footprint: all strokes (walls, window lines, balcony railings) closed over small gaps,
    keeping only the shapes that contain thick walls (drops the page frame, legend and title block),
    with holes filled. Door openings in the outer wall (~1 m) are closed by the 1.2 m kernel."""
    src = walls if ink is None else (ink | walls)
    H0, W0 = walls.shape
    n0, cc0, st0, _ = cv2.connectedComponentsWithStats(src, 8)
    frame = np.nonzero((st0[:, 2] > 0.85 * W0) & (st0[:, 3] > 0.85 * H0))[0]
    frame = frame[frame > 0]
    if len(frame):                      # page frame / title-block rules: never part of the building
        src = src.copy()
        src[np.isin(cc0, frame)] = 0
    k = max(5, int(round(1.2 * ppm))) | 1
    closed = cv2.morphologyEx(src, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)))
    n, cc, st, _ = cv2.connectedComponentsWithStats(closed, 8)
    wsum = max(int(walls.sum()), 1)
    per = np.bincount(cc[walls > 0].ravel(), minlength=n)
    H, W = walls.shape
    fp = np.zeros_like(walls)
    for i in range(1, n):
        x, y, w, h = st[i, :4]
        if per[i] < 0.03 * wsum or (w > 0.9 * W and h > 0.9 * H):
            continue
        cs, _ = cv2.findContours((cc == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(fp, cs, -1, 1, -1)
    return fp


def auto_rooms(img, ppm, walls=None, door_m=0.45, min_room_m2=0.8, seeds=None, ink=None):
    """Rooms: free space inside the footprint. With seeds (one point per room, e.g. its printed number)
    the watershed grows one region per seed; without, regions are split at door-sized passages.
    Returns (rooms [{label_id, polygon, area_px, seed}], label image, footprint)."""
    if walls is None:
        walls = masks(img)[1]
    fp = footprint(walls, ppm, ink)
    free = ((walls == 0) & (fp > 0)).astype(np.uint8)
    dist = cv2.distanceTransform(free, cv2.DIST_L2, 5)
    markers = np.zeros(walls.shape, np.int32)
    k = 0
    if seeds:
        H, W = walls.shape
        for (x, y) in seeds:
            k += 1
            x, y = min(max(int(round(x)), 0), W - 1), min(max(int(round(y)), 0), H - 1)
            if free[y, x] == 0:
                r = int(0.6 * ppm)
                ys, xs = np.nonzero(free[max(0, y - r):y + r, max(0, x - r):x + r])
                if not len(xs):
                    continue
                j = np.argmin((xs + max(0, x - r) - x) ** 2 + (ys + max(0, y - r) - y) ** 2)
                x, y = xs[j] + max(0, x - r), ys[j] + max(0, y - r)
            cv2.circle(markers, (int(x), int(y)), 2, k, -1)
        markers[free == 0] = 0
    else:
        core = (dist > door_m * ppm).astype(np.uint8)          # passages narrower than 2*door_m are cut
        n, cc, st, _ = cv2.connectedComponentsWithStats(core, 4)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] >= 0.15 * ppm * ppm:
                k += 1
                markers[cc == i] = k
    lab = watershed(-dist, markers, mask=free.astype(bool)) if k else np.zeros(walls.shape, np.int32)
    rooms = []
    for i in range(1, k + 1):
        m = (lab == i).astype(np.uint8)
        a = float(m.sum())
        if a < (0.3 if seeds else min_room_m2) * ppm * ppm:
            lab[lab == i] = 0
            continue
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        c = max(cs, key=cv2.contourArea)
        c = cv2.approxPolyDP(c, 1.5, True).reshape(-1, 2).astype(float)
        if len(c) >= 3:
            rooms.append({"label_id": i, "polygon": c.tolist(), "area_px": a})
    return rooms, lab, fp


def doors_from_labels(lab, ppm, walls):
    """A door opening is where two room regions touch without a wall between them: return each
    contact's two ends (p1, p2) across the passage."""
    H, W = lab.shape
    K, XS, YS = [], [], []
    for dy, dx in ((0, 1), (1, 0)):
        a = lab[:H - dy, :W - dx]; b = lab[dy:, dx:]
        ys, xs = np.nonzero((a > 0) & (b > 0) & (a != b))
        lo = np.minimum(a[ys, xs], b[ys, xs]).astype(np.int64); hi = np.maximum(a[ys, xs], b[ys, xs]).astype(np.int64)
        K.append(lo * 100000 + hi); XS.append(xs); YS.append(ys)
    if not K or not sum(len(k) for k in K):
        return []
    K, XS, YS = np.concatenate(K), np.concatenate(XS), np.concatenate(YS)
    doors = []
    for key in np.unique(K):
        sel = K == key
        px, py = XS[sel], YS[sel]
        x0, y0 = px.min(), py.min()
        # split one contact line into separate openings (two doors between the same rooms)
        img = np.zeros((py.max() - y0 + 3, px.max() - x0 + 3), np.uint8)
        img[py - y0 + 1, px - x0 + 1] = 1
        img = cv2.dilate(img, np.ones((3, 3), np.uint8))
        n, cc, st, _ = cv2.connectedComponentsWithStats(img, 8)
        for i in range(1, n):
            x, y, w, h = st[i, :4]
            x, y, w, h = x + x0 - 1, y + y0 - 1, w - 2, h - 2
            L = max(w, h) / ppm
            if 0.5 <= L <= 2.2:
                if w >= h:
                    doors.append({"p1": [float(x), float(y + h / 2)], "p2": [float(x + w), float(y + h / 2)]})
                else:
                    doors.append({"p1": [float(x + w / 2), float(y)], "p2": [float(x + w / 2), float(y + h)]})
    return doors


def envelope_openings(walls, fp, ink, ppm):
    """Gaps in the outer wall: footprint pixels near the outside edge with no wall. Thin parallel lines
    inside the gap -> window; empty gap -> door. Returns (windows, doors) as p1/p2 segments."""
    t = max(3, int(round(0.45 * ppm)))
    outside = (fp == 0).astype(np.uint8)
    near = cv2.dilate(outside, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * t + 1, 2 * t + 1))) & fp
    gap = (near & (walls == 0)).astype(np.uint8)
    gap = cv2.morphologyEx(gap, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, cc, st, _ = cv2.connectedComponentsWithStats(gap, 8)
    wins, doors = [], []
    for i in range(1, n):
        x, y, w, h = st[i, :4]
        L = max(w, h) / ppm
        if not (0.4 <= L <= 6.0) or min(w, h) / ppm > 0.6:
            continue
        seg = ({"p1": [float(x), float(y + h / 2)], "p2": [float(x + w), float(y + h / 2)]} if w >= h else
               {"p1": [float(x + w / 2), float(y)], "p2": [float(x + w / 2), float(y + h)]})
        inkfrac = ink[y:y + h, x:x + w][cc[y:y + h, x:x + w] == i].mean()
        (wins if inkfrac > 0.08 else doors).append(seg)
    return wins, doors


# ---------------------------------------------------------------- fixtures
def fixtures(ink, walls, fp, ppm):
    """Sanitary / kitchen symbols: closed thin-line rectangles inside the building, classified by size and
    by what is drawn inside them (legend: WC = oval, washbasin = oval + dot, bathtub = long tub,
    shower = square + dot, kitchen = 4 hob circles)."""
    space = ((ink == 0) & (walls == 0) & (fp > 0)).astype(np.uint8)
    n, cc, st, _ = cv2.connectedComponentsWithStats(space, 4)
    m = lambda px: px / ppm
    cands = []
    for i in range(1, n):
        x, y, w, h = st[i, :4]
        a, b = sorted((m(w), m(h)))
        if not (0.3 <= a <= 1.3 and 0.4 <= b <= 2.2):
            continue
        comp = (cc[y:y + h, x:x + w] == i).astype(np.uint8)
        cs, hier = cv2.findContours(comp, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        outer = max(range(len(cs)), key=lambda k: cv2.contourArea(cs[k]))
        if cv2.contourArea(cs[outer]) < 0.8 * w * h:          # not a rectangle
            continue
        ring = np.zeros((h + 6, w + 6), np.uint8)
        cv2.rectangle(ring, (0, 0), (w + 5, h + 5), 1, 3)
        ys, xs = np.nonzero(ring)
        ys, xs = (ys + y - 3).clip(0, walls.shape[0] - 1), (xs + x - 3).clip(0, walls.shape[1] - 1)
        if walls[ys, xs].mean() > 0.5:                          # bounded by walls: a room / shaft, not a symbol
            continue
        holes = [cv2.boundingRect(cs[k]) for k in range(len(cs))
                 if hier is not None and hier[0][k][3] == outer]
        holes = [(m(hw), m(hh)) for _, _, hw, hh in holes]
        cands.append((x, y, w, h, a, b, holes))
    out = []
    for x, y, w, h, a, b, holes in cands:
        if any(x2 <= x and y2 <= y and x + w <= x2 + w2 and y + h <= y2 + h2 and (x2, y2, w2, h2) != (x, y, w, h)
               for x2, y2, w2, h2, *_ in cands):
            continue                                            # inside another symbol (e.g. the oval itself)
        big = [hh for hh in holes if max(hh) >= 0.18]
        dots = [hh for hh in holes if max(hh) < 0.09]
        circles = [hh for hh in holes if 0.09 <= max(hh) < 0.25 and abs(hh[0] - hh[1]) < 0.06]
        stripes = [hh for hh in holes if max(hh) > 0.6]
        if len(stripes) >= 3:
            continue                                            # stairs
        if len(circles) >= 3 or (b >= 1.2 and a <= 0.75 and len(holes) >= 4):
            t = "kitchen"
        elif b >= 1.3:
            t = "bathtub"
        elif a >= 0.7 and b <= 1.3:
            t = "shower"
        elif big:
            t = "washbasin" if dots else "wc"
        else:
            continue
        out.append({"type": t, "x": float(x + w / 2), "y": float(y + h / 2)})
    return out


# ---------------------------------------------------------------- text (OCR)
_OCR = None
NUM_RE = __import__("re").compile(r"^\s*(\d{1,2})[.,](\d{2})\s*$")
SCALE_RE = __import__("re").compile(r"1\s*:\s*(\d{2,4})")
UNIT_RE = __import__("re").compile(r"^\W*(whg|app|apt|ap|unit|wohnung)\b", __import__("re").I)


def ocr(img):
    """[(text, (cx, cy), height_px, confidence)] for every text line (rapidocr, CPU, offline)."""
    global _OCR
    if _OCR is None:
        from rapidocr_onnxruntime import RapidOCR
        _OCR = RapidOCR()
    res, _ = _OCR(_rgb(img))
    out = []
    for box, txt, conf in res or []:
        b = np.array(box, float)
        out.append((str(txt), (float(b[:, 0].mean()), float(b[:, 1].mean())), float(b[:, 1].max() - b[:, 1].min()), float(conf)))
    return out


def printed_scale(texts):
    """px per metre from a printed '1:N' (title block), if N is a standard drawing scale."""
    for t, _, _, _ in texts:
        m = SCALE_RE.search(t)
        if m and int(m.group(1)) in STD_SCALES:
            return ppm_for(int(m.group(1)))
    return None


def room_labels(texts, region=None):
    """Room numbers ('2.01') with the name printed just above them. region: (x0,y0,x1,y1) to keep."""
    nums = []
    for t, (x, y), h, c in texts:
        m = NUM_RE.match(t)
        if m and (region is None or (region[0] <= x <= region[2] and region[1] <= y <= region[3])):
            nums.append({"id": f"{m.group(1)}.{m.group(2)}", "xy": (x, y), "h": h, "name": None})
    words = [(t.strip(" []|"), xy, h) for t, xy, h, c in texts if not NUM_RE.match(t) and not UNIT_RE.match(t)
             and any(ch.isalpha() for ch in t)]
    for n in nums:
        x, y = n["xy"]
        best = None
        for t, (wx, wy), h in words:
            dy = y - wy
            if 0.3 * n["h"] < dy < 2.2 * max(n["h"], h) and abs(wx - x) < 4 * max(n["h"], h) + 0.5 * len(t) * h:
                if best is None or dy < best[0]:
                    best = (dy, t)
        n["name"] = best[1] if best else None
    return nums


# ---------------------------------------------------------------- seeded rooms (agent tool)
def segment_rooms(img, seeds, simplify_px=2.0):
    """One polygon + pixel area per seed point (watershed between walls; splits at door openings)."""
    rgb = _rgb(img)
    H, W = rgb.shape[:2]
    _, walls, _, _ = masks(rgb)
    free = (walls == 0).astype(np.uint8)
    dist = cv2.distanceTransform(free, cv2.DIST_L2, 5)
    markers = np.zeros((H, W), np.int32)
    markers[:3, :] = markers[-3:, :] = 1
    markers[:, :3] = markers[:, -3:] = 1
    for i, (x, y) in enumerate(seeds):
        x, y = min(max(int(round(x)), 0), W - 1), min(max(int(round(y)), 0), H - 1)
        if free[y, x] == 0 or dist[y, x] < 2:
            ys, xs = np.nonzero(dist[max(0, y - 40):y + 40, max(0, x - 40):x + 40] >= 2)
            if len(xs):
                j = np.argmin((xs + max(0, x - 40) - x) ** 2 + (ys + max(0, y - 40) - y) ** 2)
                x, y = xs[j] + max(0, x - 40), ys[j] + max(0, y - 40)
        cv2.circle(markers, (x, y), 2, i + 2, -1)
    lab = watershed(-dist, markers, mask=free.astype(bool))
    out = []
    for i in range(len(seeds)):
        m = (lab == i + 2).astype(np.uint8)
        if m.sum() == 0:
            out.append({"polygon": [], "area_px": 0.0, "closed": False}); continue
        n, cc, st, _ = cv2.connectedComponentsWithStats(m, 8)
        m = (cc == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        c = max(cs, key=cv2.contourArea)
        touches = st[1:, cv2.CC_STAT_LEFT].min() <= 3
        c = cv2.approxPolyDP(c, simplify_px, True).reshape(-1, 2).astype(float)
        out.append({"polygon": [[round(x, 1), round(y, 1)] for x, y in c.tolist()],
                    "area_px": float(m.sum()), "closed": not touches})
    return out


def poly_area(p):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(p, p[1:] + p[:1]))) / 2
