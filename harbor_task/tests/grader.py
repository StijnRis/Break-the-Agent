import json
import math
import subprocess
import sys
from pathlib import Path

from score_metric import score

answer_path = Path("/tmp/answer.json")
gt = json.loads(Path("/grader/ground_truth.json").read_text(encoding="utf-8"))
try:
    submitted = json.loads(answer_path.read_text(encoding="utf-8")) if answer_path.exists() else None
    result = score(gt, submitted, (2480, 1753))
    reward = float(result.get("reward", 0.0))
    if not math.isfinite(reward):
        reward = 0.0
    reward = min(1.0, max(0.0, reward))
except Exception as exc:
    print(f"Could not score submission: {type(exc).__name__}: {exc}", file=sys.stderr)
    reward = 0.0
Path("/logs/verifier").mkdir(parents=True, exist_ok=True)
Path("/logs/verifier/reward.txt").write_text(f"{reward:.6f}\n", encoding="utf-8")
try:
    subprocess.run(
        ["python", "/grader/render_result.py", "/tmp/answer.json", "/grader/drawing.png",
         "/logs/verifier/comparison.png", "--reward", "/logs/verifier/reward.txt"],
        check=True,
    )
    subprocess.run(
        ["python", "/grader/render_errors.py", "/tmp/answer.json", "/grader/drawing.png",
         "/grader/ground_truth.json", "/logs/verifier/errors.png"],
        check=True,
    )
    subprocess.run(
        ["python", "/grader/render_review.py", "/tmp/answer.json", "/grader/drawing.png",
         "/grader/ground_truth.json", "/logs/verifier/review.png"],
        check=True,
    )
except Exception as exc:  # The score must remain available if reporting fails.
    print(f"Could not render comparison: {type(exc).__name__}: {exc}", file=sys.stderr)
print(f"Blueprint schematic score: {reward:.6f}")
