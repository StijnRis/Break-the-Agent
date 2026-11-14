"""Render an agent submission next to its source drawing.

The verifier calls this after it has scored each Harbor trial.  It uses only
the public drawing and the agent's submitted JSON; surveyed ground truth never
appears in the image.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


COLORS = {
    "walls": (40, 90, 220),
    "rooms": (230, 120, 0),
    "doors": (0, 170, 60),
    "windows": (0, 190, 210),
    "fixtures": (200, 0, 160),
}


def geometry_bounds(schematic: dict, size: tuple[int, int]) -> tuple[int, int, int, int]:
    points: list[tuple[float, float]] = []
    for wall in schematic.get("walls", []) or []:
        if isinstance(wall, dict):
            points.extend((wall.get("p1", []), wall.get("p2", [])))
        elif isinstance(wall, list):
            points.extend(wall)
    for room in schematic.get("rooms", []) or []:
        points.extend(room.get("polygon", []))
    for name in ("doors", "windows"):
        for item in schematic.get(name, []) or []:
            points.extend((item.get("p1", []), item.get("p2", [])))
    for item in schematic.get("fixtures", []) or []:
        points.append((item.get("x"), item.get("y")))
    valid = [(float(x), float(y)) for x, y in points if x is not None and y is not None]
    if not valid:
        return (0, 0, *size)
    pad = 50
    x0 = max(0, int(min(x for x, _ in valid) - pad))
    y0 = max(0, int(min(y for _, y in valid) - pad))
    x1 = min(size[0], int(max(x for x, _ in valid) + pad))
    y1 = min(size[1], int(max(y for _, y in valid) + pad))
    return (x0, y0, x1, y1)


def render_overlay(source: Image.Image, schematic: dict) -> Image.Image:
    base = Image.blend(source.convert("RGB"), Image.new("RGB", source.size, "white"), 0.55)
    layer = Image.new("RGBA", source.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for wall in schematic.get("walls", []) or []:
        if isinstance(wall, dict) and wall.get("p1") and wall.get("p2"):
            draw.line([tuple(wall["p1"]), tuple(wall["p2"])], fill=COLORS["walls"] + (180,),
                      width=max(2, int(wall.get("thickness_px", 6))))
    for room in schematic.get("rooms", []) or []:
        points = [tuple(point) for point in room.get("polygon", [])]
        if len(points) >= 3:
            draw.polygon(points, fill=COLORS["rooms"] + (38,), outline=COLORS["rooms"] + (255,), width=3)
    for name in ("doors", "windows"):
        for item in schematic.get(name, []) or []:
            if item.get("p1") and item.get("p2"):
                draw.line([tuple(item["p1"]), tuple(item["p2"])], fill=COLORS[name] + (255,), width=6)
    for item in schematic.get("fixtures", []) or []:
        if item.get("x") is not None and item.get("y") is not None:
            x, y = item["x"], item["y"]
            draw.ellipse((x - 7, y - 7, x + 7, y + 7), outline=COLORS["fixtures"] + (255,), width=3)
    return Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")


def render_schematic(size: tuple[int, int], schematic: dict) -> Image.Image:
    """Render only the submitted JSON, without using the source drawing."""
    canvas = Image.new("RGB", size, "white")
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for wall in schematic.get("walls", []) or []:
        if isinstance(wall, dict) and wall.get("p1") and wall.get("p2"):
            draw.line([tuple(wall["p1"]), tuple(wall["p2"])], fill=COLORS["walls"] + (210,),
                      width=max(2, int(wall.get("thickness_px", 6))))
        elif isinstance(wall, list) and len(wall) >= 3:
            draw.polygon([tuple(point) for point in wall], fill=COLORS["walls"] + (130,),
                         outline=COLORS["walls"] + (255,))
    for room in schematic.get("rooms", []) or []:
        points = [tuple(point) for point in room.get("polygon", [])]
        if len(points) >= 3:
            draw.polygon(points, fill=COLORS["rooms"] + (45,), outline=COLORS["rooms"] + (255,), width=3)
            cx = sum(point[0] for point in points) / len(points)
            cy = sum(point[1] for point in points) / len(points)
            draw.text((cx - 18, cy - 6), f"{room.get('id') or ''} {room.get('name') or ''}", fill=(150, 60, 0, 255))
    for name in ("doors", "windows"):
        for item in schematic.get(name, []) or []:
            if item.get("p1") and item.get("p2"):
                draw.line([tuple(item["p1"]), tuple(item["p2"])], fill=COLORS[name] + (255,), width=6)
    for item in schematic.get("fixtures", []) or []:
        if item.get("x") is not None and item.get("y") is not None:
            x, y = item["x"], item["y"]
            draw.ellipse((x - 7, y - 7, x + 7, y + 7), outline=COLORS["fixtures"] + (255,), width=3)
    return Image.alpha_composite(canvas.convert("RGBA"), layer).convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Harbor submission comparison image")
    parser.add_argument("submission", type=Path)
    parser.add_argument("drawing", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--reward", type=Path)
    args = parser.parse_args()

    schematic = json.loads(args.submission.read_text(encoding="utf-8")) if args.submission.exists() else {}
    source = Image.open(args.drawing).convert("RGB")
    box = geometry_bounds(schematic, source.size)
    reference = source.crop(box)
    submission = render_schematic(source.size, schematic).crop(box)

    max_height = 1280
    if reference.height > max_height:
        scale = max_height / reference.height
        new_size = (round(reference.width * scale), max_height)
        reference = reference.resize(new_size, Image.Resampling.LANCZOS)
        submission = submission.resize(new_size, Image.Resampling.LANCZOS)
    margin, header, footer, gap = 28, 76, 112, 20
    canvas = Image.new("RGB", (reference.width * 2 + margin * 2 + gap, reference.height + header + footer), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 18), "Harbor trial: source drawing vs submitted schematic", fill=(20, 20, 20))
    draw.text((margin, header - 25), "Reference drawing (agent input)", fill=(20, 20, 20))
    draw.text((margin + reference.width + gap, header - 25), "Agent-submitted schematic", fill=(20, 20, 20))
    canvas.paste(reference, (margin, header))
    canvas.paste(submission, (margin + reference.width + gap, header))

    score = "not available"
    if args.reward and args.reward.exists():
        score = args.reward.read_text(encoding="utf-8").strip()
    counts = ", ".join(f"{key}: {len(schematic.get(key) or [])}" for key in
                       ("walls", "rooms", "doors", "windows", "fixtures"))
    y = header + reference.height + 18
    draw.text((margin, y), f"Score: {score}    |    {counts}", fill=(20, 20, 20))
    y += 28
    legend = "  ".join(f"{name}: {color}" for name, color in COLORS.items())
    draw.text((margin, y), f"Overlay colors — {legend}", fill=(65, 65, 65))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output)


if __name__ == "__main__":
    main()
