"""Supervised rows: masked drawing -> compact target schematic (policy.to_text).

    python -m blueprint_env.make_sft --root tasks --plans plans.json --key sft --out sft.jsonl

Test plans (split.json "test") are always excluded.
"""
from __future__ import annotations

import argparse
import json
import os

from PIL import Image

from .policy import prompt_for, to_text

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_plans():
    return set(json.load(open(os.path.join(HERE, "split.json")))["test"])


def row(task, image_path, W, H, text, **extra):
    return {"task": task, "image": image_path, **extra,
            "messages": [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt_for(W, H)}]},
                         {"role": "assistant", "content": [{"type": "text", "text": text}]}]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="tasks")
    ap.add_argument("--plans", default="", help="JSON file with plan lists; default: every task under --root")
    ap.add_argument("--key", default="sft")
    ap.add_argument("--max-chars", type=int, default=16000, help="skip very large floors")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="sft.jsonl")
    a = ap.parse_args()
    plans = json.load(open(a.plans))[a.key] if a.plans else sorted(
        d for d in os.listdir(a.root) if os.path.isdir(os.path.join(a.root, d)))
    test = test_plans()
    if os.path.exists(os.path.join(a.root, "index.json")):       # drop plans whose ground truth failed the alignment check
        from .build_tasks import valid_tasks
        ok = set(valid_tasks(a.root)); plans = [p for p in plans if p in ok]
    rows, skipped = [], 0
    for p in plans:
        td = os.path.join(a.root, p)
        if p in test or not os.path.exists(os.path.join(td, "ground_truth.json")):
            skipped += 1; continue
        gt = json.load(open(os.path.join(td, "ground_truth.json"), encoding="utf8"))
        img = os.path.abspath(os.path.join(td, "drawing.png"))
        W, H = Image.open(img).size
        t = to_text(gt, W, H)
        if len(t) > a.max_chars:
            skipped += 1; continue
        rows.append(row(p, img, W, H, t))
        if a.limit and len(rows) >= a.limit:
            break
    with open(a.out, "w", encoding="utf8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    L = [len(r["messages"][1]["content"][0]["text"]) for r in rows]
    print(f"{len(rows)} rows -> {a.out} | skipped {skipped} | target chars avg {sum(L) / max(len(L), 1):,.0f} max {max(L or [0]):,}")


if __name__ == "__main__":
    main()
