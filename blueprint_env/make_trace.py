"""Render a Harbor trial (ATIF trajectory + verifier output) as one self-contained HTML page.

    python -m blueprint_env.make_trace jobs/blueprint-harbor-modal/harbor_task__5z7nxmC
    python -m blueprint_env.make_trace <trial_dir> -o results/harness_trace.html

Everything (data, drawing, verifier images) is inlined, so the page opens offline.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).with_name("trace_template.html")


def jpeg_uri(path: Path, max_w: int, quality: int = 82) -> str | None:
    if not path.exists():
        return None
    try:
        from PIL import Image
    except ImportError:  # fall back to the raw file
        return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def ts(s: str | None) -> float | None:
    return datetime.fromisoformat(s).timestamp() if s else None


def clip(s: str, n: int) -> str:
    s = s or ""
    return s if len(s) <= n else s[:n] + f"\n… ({len(s) - n:,} more characters)"


def category(fn: str) -> str:
    if fn == "blueprint_view_region":
        return "zoom"
    if fn in ("blueprint_preview_schematic",):
        return "preview"
    if fn in ("blueprint_submit_schematic",):
        return "submit"
    if fn.startswith("blueprint_"):
        return "perceive"
    return "code"


def summarise(fn: str, args: dict, obs: str) -> str:
    if fn == "blueprint_view_region":
        x0, y0, x1, y1 = (args.get(k) for k in ("x0", "y0", "x1", "y1"))
        return f"({x0}, {y0}) → ({x1}, {y1}) · {x1 - x0}×{y1 - y0} px"
    if fn == "blueprint_segment_rooms":
        return f"{len(args.get('seeds', []))} seed points"
    if fn in ("blueprint_preview_schematic", "blueprint_submit_schematic"):
        m = re.search(r"\{[^{}]*'walls'[^{}]*\}", obs)
        return m.group(0).replace("'", "") if m else ""
    if fn == "bash":
        cmd = args.get("command", "")
        m = re.search(r"cat << '?EOF'? > (\S+)", cmd)
        if m:
            return f"writes + runs {m.group(1)}"
        return cmd.splitlines()[0][:110] if cmd else ""
    if fn == "write":
        return args.get("filePath") or args.get("file_path") or ""
    return ""


def headline(reasoning: str) -> str:
    m = re.search(r"\*\*(.+?)\*\*", reasoning or "")
    return m.group(1).strip() if m else ""


def components(trial: Path, gt_path: Path) -> dict | None:
    answer = trial / "artifacts" / "tmp" / "answer.json"
    if not (answer.exists() and gt_path.exists()):
        return None
    sys.path.insert(0, str(gt_path.parent))
    try:
        from score_metric import score  # type: ignore
        r = score(json.loads(gt_path.read_text("utf8")), json.loads(answer.read_text("utf8")), (2480, 1753))
        return {k: round(float(v), 4) for k, v in r["components"].items()}
    except Exception as exc:  # numpy/shapely missing etc. The page still renders without it.
        print(f"component breakdown skipped: {type(exc).__name__}: {exc}", file=sys.stderr)
        return None


def build(trial: Path, drawing: Path, gt_path: Path) -> dict:
    traj = json.loads((trial / "agent" / "trajectory.json").read_text("utf8"))
    steps, prev_t = [], None
    t0 = next(ts(s["timestamp"]) for s in traj["steps"] if s.get("timestamp"))
    for s in traj["steps"]:
        t = ts(s.get("timestamp"))
        m = s.get("metrics") or {}
        calls = s.get("tool_calls") or []
        results = {r.get("source_call_id"): r.get("content") for r in (s.get("observation") or {}).get("results", [])}
        tools = []
        for c in calls:
            fn, args = c["function_name"], c.get("arguments") or {}
            obs = results.get(c.get("tool_call_id"))
            obs = obs if isinstance(obs, str) else json.dumps(obs)
            tools.append({
                "fn": fn, "cat": category(fn), "summary": summarise(fn, args, obs or ""),
                "args": clip(json.dumps(args, indent=1) if fn != "bash" else args.get("command", ""), 2400),
                "obs": clip(obs or "", 1800),
                "region": [args[k] for k in ("x0", "y0", "x1", "y1")] if fn == "blueprint_view_region" else None,
            })
        steps.append({
            "id": s["step_id"], "source": s["source"],
            "t": None if t is None else round(t - t0, 1),
            "start": None if t is None else round((prev_t if prev_t is not None else t) - t0, 1),
            "message": clip(s.get("message", ""), 3000),
            "reasoning": clip(s.get("reasoning_content") or "", 4000),
            "headline": headline(s.get("reasoning_content") or ""),
            "tools": tools,
            "prompt": m.get("prompt_tokens", 0), "completion": m.get("completion_tokens", 0),
            "cached": m.get("cached_tokens", 0), "thinking": (m.get("extra") or {}).get("reasoning_tokens", 0),
            "cost": m.get("cost_usd", 0),
        })
        if t is not None:
            prev_t = t

    result = json.loads((trial / "result.json").read_text("utf8")) if (trial / "result.json").exists() else {}
    reward_file = trial / "verifier" / "reward.txt"
    reward = float(reward_file.read_text().strip()) if reward_file.exists() else None
    from PIL import Image  # noqa: F401  (size only)
    dw, dh = Image.open(drawing).size
    return {
        "trial": trial.name, "job": trial.parent.name,
        "task": result.get("task_name") or "", "agent": traj["agent"],
        "env": (result.get("config") or {}).get("environment", {}).get("type", ""),
        "reward": reward, "components": components(trial, gt_path),
        "final": traj.get("final_metrics", {}), "steps": steps,
        "duration": max(s["t"] for s in steps if s["t"] is not None),
        "drawing": {"src": jpeg_uri(drawing, 1600, 78), "w": dw, "h": dh},
        "comparison": jpeg_uri(trial / "verifier" / "comparison.png", 1400),
        "errors": jpeg_uri(trial / "verifier" / "errors.png", 1400),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("trial", type=Path, help="Harbor trial directory (contains agent/trajectory.json)")
    ap.add_argument("-o", "--out", type=Path, default=ROOT / "results" / "harness_trace.html")
    ap.add_argument("--drawing", type=Path, default=ROOT / "harbor_task" / "environment" / "task" / "drawing.png")
    ap.add_argument("--ground-truth", type=Path, default=ROOT / "harbor_task" / "tests" / "ground_truth.json",
                    help="used only to break the reward into components")
    a = ap.parse_args()
    data = build(a.trial, a.drawing, a.ground_truth)
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    html = TEMPLATE.read_text("utf8").replace("/*__DATA__*/null", payload)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(html, "utf8")
    print(f"wrote {a.out} ({len(html) / 1e6:.1f} MB, {len(data['steps'])} steps, reward {data['reward']})")


if __name__ == "__main__":
    main()
