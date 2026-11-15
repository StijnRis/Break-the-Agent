"""Learned detector for doors, windows and fixtures (YOLO11s, trained on Modal: models/yolo_swiss.pt).

Classes: door, window, toilet, washbasin, bathtub, shower, stove, sink. Used by the reference solver
(`python -m blueprint_env.reference --yolo`) in place of the hand-written symbol matching, so the
"stronger reference run" has a trained perception part. It only ever sees the masked drawing.
"""
from __future__ import annotations

import os

_MODEL = None
PATH = os.environ.get("YOLO_WEIGHTS", os.path.join(os.path.dirname(__file__), "..", "models", "yolo_swiss.pt"))
FIXTURE = {"toilet": "wc", "washbasin": "washbasin", "bathtub": "bathtub", "shower": "shower", "stove": "kitchen"}


def detect(img, conf=0.25, imgsz=1280):
    """img: PIL RGB. Returns (doors, windows, fixtures) in pixel coordinates of img."""
    global _MODEL
    if _MODEL is None:
        from ultralytics import YOLO
        _MODEL = YOLO(PATH)
    r = _MODEL.predict(img, conf=conf, imgsz=imgsz, verbose=False)[0]
    doors, wins, fixt = [], [], []
    for (x1, y1, x2, y2), c, name in zip(r.boxes.xyxy.tolist(), r.boxes.conf.tolist(),
                                        (r.names[int(k)] for k in r.boxes.cls.tolist())):
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        if name in ("door", "window"):
            # an opening segment through the box centre along its long side
            if (x2 - x1) >= (y2 - y1):
                seg = {"p1": [float(x1), float(cy)], "p2": [float(x2), float(cy)]}
            else:
                seg = {"p1": [float(cx), float(y1)], "p2": [float(cx), float(y2)]}
            (doors if name == "door" else wins).append(seg)
        elif name in FIXTURE:
            fixt.append({"type": FIXTURE[name], "x": float(cx), "y": float(cy)})
    return doors, wins, fixt
