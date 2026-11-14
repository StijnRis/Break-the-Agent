"""Draw a schematic (pixel frame) over the drawing — used both as an agent tool and for the report."""
from __future__ import annotations

from PIL import Image, ImageDraw

COLORS = {"walls": (40, 90, 220), "rooms": (230, 120, 0), "doors": (0, 170, 60), "windows": (0, 190, 210),
          "fixtures": (200, 0, 160)}


def overlay(drawing_path: str, sch: dict, fade: float = 0.55, crop=None, labels=True) -> Image.Image:
    base = Image.open(drawing_path).convert("RGB")
    base = Image.blend(base, Image.new("RGB", base.size, (255, 255, 255)), fade)
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for w in sch.get("walls", []) or []:
        try:
            if isinstance(w, dict):  # centre line + thickness
                d.line([tuple(w["p1"]), tuple(w["p2"])], fill=COLORS["walls"] + (170,),
                       width=max(2, int(w.get("thickness_px", 6))))
            elif len(w) >= 3:
                d.polygon([tuple(p) for p in w], fill=COLORS["walls"] + (130,), outline=COLORS["walls"] + (255,))
        except Exception:
            pass
    for r in sch.get("rooms", []) or []:
        try:
            pts = [tuple(p) for p in r["polygon"]]
            d.polygon(pts, fill=COLORS["rooms"] + (45,), outline=COLORS["rooms"] + (255,), width=3)
            if labels:
                cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
                d.text((cx - 12, cy - 6), f"{r.get('id') or ''} {r.get('name') or ''}", fill=(150, 60, 0, 255))
        except Exception:
            pass
    for k in ("doors", "windows"):
        for o in sch.get(k, []) or []:
            try:
                d.line([tuple(o["p1"]), tuple(o["p2"])], fill=COLORS[k] + (255,), width=6)
            except Exception:
                pass
    for f in sch.get("fixtures", []) or []:
        try:
            x, y = f["x"], f["y"]
            d.ellipse([x - 7, y - 7, x + 7, y + 7], outline=COLORS["fixtures"] + (255,), width=3)
            if labels:
                d.text((x + 8, y - 6), str(f.get("type", ""))[:10], fill=COLORS["fixtures"] + (255,))
        except Exception:
            pass
    out = Image.alpha_composite(base.convert("RGBA"), lay).convert("RGB")
    if crop:
        out = out.crop(tuple(int(v) for v in crop))
    return out
