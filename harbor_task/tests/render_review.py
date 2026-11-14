"""Create one side-by-side review image for a completed Harbor trial."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

from render_errors import draw_errors
from render_result import geometry_bounds, render_schematic
from score_metric import score


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a three-panel Harbor review image")
    parser.add_argument("submission", type=Path)
    parser.add_argument("drawing", type=Path)
    parser.add_argument("ground_truth", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    prediction = json.loads(args.submission.read_text(encoding="utf-8")) if args.submission.exists() else {}
    truth = json.loads(args.ground_truth.read_text(encoding="utf-8"))
    source = Image.open(args.drawing).convert("RGB")
    box = geometry_bounds(truth, source.size)
    panels = [
        source.crop(box),
        render_schematic(source.size, prediction).crop(box),
        draw_errors(source, truth, prediction).crop(box),
    ]
    max_height = 1150
    if panels[0].height > max_height:
        scale = max_height / panels[0].height
        new_size = (round(panels[0].width * scale), max_height)
        panels = [panel.resize(new_size, Image.Resampling.LANCZOS) for panel in panels]

    margin, gap, header, footer = 28, 18, 76, 126
    width = panels[0].width * 3 + margin * 2 + gap * 2
    canvas = Image.new("RGB", (width, panels[0].height + header + footer), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 18), "Harbor review: source reference, AI submission, and scored differences", fill=(20, 20, 20))
    labels = ["1. Reference drawing", "2. AI-generated schematic", "3. Differences from surveyed reference"]
    for index, (label, panel) in enumerate(zip(labels, panels)):
        x = margin + index * (panel.width + gap)
        draw.text((x, header - 25), label, fill=(20, 20, 20))
        canvas.paste(panel, (x, header))

    result = score(truth, prediction, source.size)
    y = header + panels[0].height + 18
    draw.text((margin, y), "Panel 3 only marks errors: red = missing surveyed detail; green = extra or misplaced submission detail.", fill=(20, 20, 20))
    y += 26
    parts = "  ".join(f"{name} {value:.2f}" for name, value in result["components"].items())
    draw.text((margin, y), f"Score {result['reward']:.4f}  |  {parts}", fill=(20, 20, 20))
    y += 26
    details = result["details"]
    draw.text((margin, y), f"Doors: {details['doors']['tp']}/{details['doors']['n_gt']} matched; "
                             f"windows: {details['windows']['tp']}/{details['windows']['n_gt']} matched; "
                             f"fixtures: {details['fixtures']['tp']}/{details['fixtures']['n_gt']} matched.",
              fill=(65, 65, 65))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output)


if __name__ == "__main__":
    main()
