"""Make a visual error report by comparing a submission with surveyed geometry.

This runs only in the separate verifier after the agent has finished.  Red is
surveyed geometry and green is the agent submission; yellow means the two
overlap.  The file is an evaluation artifact, never available to the agent.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation
from scipy.optimize import linear_sum_assignment

from render_result import geometry_bounds
from score_metric import _wall_masks, score


GT = (225, 45, 45, 170)
PRED = (0, 165, 75, 170)


def paint_mask(layer: Image.Image, mask: np.ndarray, color: tuple[int, int, int, int], size: tuple[int, int]) -> None:
    image = Image.fromarray((mask.astype(np.uint8) * 255), mode="L").resize(size, Image.Resampling.NEAREST)
    solid = Image.new("RGBA", size, color)
    layer.paste(solid, mask=image)


def midpoint(item: dict) -> tuple[float, float] | None:
    try:
        a, b = item["p1"], item["p2"]
        return ((float(a[0]) + float(b[0])) / 2, (float(a[1]) + float(b[1])) / 2)
    except (KeyError, TypeError, ValueError, IndexError):
        return None


def matched_indices(reference: list[tuple[float, float]], submitted: list[tuple[float, float]], tolerance: float) -> tuple[set[int], set[int]]:
    if not reference or not submitted:
        return set(), set()
    distances = np.array([[math.dist(a, b) for b in submitted] for a in reference])
    rows, cols = linear_sum_assignment(distances)
    pairs = [(r, c) for r, c in zip(rows, cols) if distances[r, c] <= tolerance]
    return {r for r, _ in pairs}, {c for _, c in pairs}


def draw_unmatched_segments(draw: ImageDraw.ImageDraw, truth: dict, prediction: dict, key: str, tolerance: float) -> None:
    gt_items = [item for item in truth.get(key, []) if midpoint(item) is not None]
    pred_items = [item for item in prediction.get(key, []) if midpoint(item) is not None]
    gt_match, pred_match = matched_indices([midpoint(item) for item in gt_items], [midpoint(item) for item in pred_items], tolerance)
    for i, item in enumerate(gt_items):
        if i not in gt_match:
            draw.line([tuple(item["p1"]), tuple(item["p2"])], fill=GT, width=8)
    for i, item in enumerate(pred_items):
        if i not in pred_match:
            draw.line([tuple(item["p1"]), tuple(item["p2"])], fill=PRED, width=8)


def draw_unmatched_fixtures(draw: ImageDraw.ImageDraw, truth: dict, prediction: dict, tolerance: float) -> None:
    for kind in {item["type"] for item in truth.get("fixtures", [])} | {item.get("type") for item in prediction.get("fixtures", [])}:
        gt_items = [item for item in truth.get("fixtures", []) if item["type"] == kind]
        pred_items = [item for item in prediction.get("fixtures", []) if item.get("type") == kind]
        gt_match, pred_match = matched_indices([(item["x"], item["y"]) for item in gt_items],
                                                [(item["x"], item["y"]) for item in pred_items], tolerance)
        for i, item in enumerate(gt_items):
            if i not in gt_match:
                x, y = item["x"], item["y"]
                draw.ellipse((x - 10, y - 10, x + 10, y + 10), outline=GT, width=5)
        for i, item in enumerate(pred_items):
            if i not in pred_match:
                x, y = item["x"], item["y"]
                draw.ellipse((x - 10, y - 10, x + 10, y + 10), outline=PRED, width=5)


def draw_errors(source: Image.Image, truth: dict, prediction: dict) -> Image.Image:
    """Show only geometry that fails the same tolerance used by the reward."""
    layer = Image.blend(source, Image.new("RGB", source.size, "white"), 0.35).convert("RGBA")
    gt_mask, pred_mask = _wall_masks(truth, prediction.get("walls") or [], source.size, truth["m_per_px"])
    radius = max(1, int(round(0.15 / truth["m_per_px"] / 2)))
    yy, xx = np.mgrid[-radius:radius + 1, -radius:radius + 1]
    disk = xx ** 2 + yy ** 2 <= radius * radius
    paint_mask(layer, gt_mask & ~binary_dilation(pred_mask, disk), GT, source.size)
    paint_mask(layer, pred_mask & ~binary_dilation(gt_mask, disk), PRED, source.size)
    draw = ImageDraw.Draw(layer)
    draw_unmatched_segments(draw, truth, prediction, "doors", 0.4 / truth["m_per_px"])
    draw_unmatched_segments(draw, truth, prediction, "windows", 0.4 / truth["m_per_px"])
    draw_unmatched_fixtures(draw, truth, prediction, 0.5 / truth["m_per_px"])
    return layer.convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Harbor visual error report")
    parser.add_argument("submission", type=Path)
    parser.add_argument("drawing", type=Path)
    parser.add_argument("ground_truth", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    prediction = json.loads(args.submission.read_text(encoding="utf-8")) if args.submission.exists() else {}
    truth = json.loads(args.ground_truth.read_text(encoding="utf-8"))
    source = Image.open(args.drawing).convert("RGB")
    box = geometry_bounds(truth, source.size)
    reference = source.crop(box)
    diagnostic = draw_errors(source, truth, prediction).crop(box)

    max_height = 1280
    if reference.height > max_height:
        scale = max_height / reference.height
        new_size = (round(reference.width * scale), max_height)
        reference = reference.resize(new_size, Image.Resampling.LANCZOS)
        diagnostic = diagnostic.resize(new_size, Image.Resampling.LANCZOS)
    result = score(truth, prediction, source.size)
    parts = "  ".join(f"{name} {value:.2f}" for name, value in result["components"].items())
    margin, header, footer, gap = 28, 76, 126, 20
    canvas = Image.new("RGB", (reference.width * 2 + margin * 2 + gap, reference.height + header + footer), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 18), "Harbor diagnostic: where the submission differs from the surveyed reference", fill=(20, 20, 20))
    draw.text((margin, header - 25), "Source drawing", fill=(20, 20, 20))
    draw.text((margin + reference.width + gap, header - 25), "Error overlay", fill=(20, 20, 20))
    canvas.paste(reference, (margin, header))
    canvas.paste(diagnostic, (margin + reference.width + gap, header))
    y = header + reference.height + 18
    draw.text((margin, y), "Only errors are marked: red = missing surveyed detail; green = extra or misplaced submission detail.", fill=(20, 20, 20))
    y += 26
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
