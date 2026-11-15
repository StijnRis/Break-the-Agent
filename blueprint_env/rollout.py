"""Run a policy served behind an OpenAI-compatible API (vLLM) on plans, score every reply with the
environment (score.py), and optionally keep the best samples as training rows.

    vllm serve <model> --served-model-name policy --max-model-len 32768 --limit-mm-per-prompt '{"image":1}'
    # evaluation: greedy + 3 sampled runs on the test split, written where evaluate.py finds them
    python -m blueprint_env.rollout --plans split.json --key test --greedy --samples 3 --tag qwen-sft
    # experience: 8 samples per plan; per plan keep the best one if it beats that plan's average sample
    python -m blueprint_env.rollout --plans plans.json --key exp --samples 8 --tag exp-r1 --save-best exp_rows.jsonl

Outputs runs/<tag>/<task>/run<k>/episode.json (run0 = greedy when --greedy). Resumable.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import statistics as st
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image

from .make_sft import row, test_plans
from .policy import from_text, model_image, prompt_for, to_text
from .score import score


def one(client, model, root, task, temperature, max_tokens, rep_penalty=1.0):
    td = os.path.join(root, task)
    img = Image.open(os.path.join(td, "drawing.png")).convert("RGB")
    W, H = img.size
    buf = io.BytesIO(); model_image(img).save(buf, "PNG")
    url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    t0 = time.time()
    r = client.chat.completions.create(model=model, temperature=temperature, max_tokens=max_tokens,
        extra_body={"repetition_penalty": rep_penalty} if rep_penalty != 1.0 else None, messages=[
        {"role": "user", "content": [{"type": "image_url", "image_url": {"url": url}},
                                     {"type": "text", "text": prompt_for(W, H)}]}])
    text = r.choices[0].message.content or ""
    sch = from_text(text, W, H)
    gt = json.load(open(os.path.join(td, "ground_truth.json"), encoding="utf8"))
    elapsed = time.time() - t0
    res = score(gt, sch, (W, H), elapsed)
    u = r.usage
    return {"result": {"task": task, "model": model, "submitted": bool(text.strip()), "temperature": temperature,
                       "finish": r.choices[0].finish_reason, "seconds": round(elapsed, 1),
                       "tokens": {"in": u.prompt_tokens, "out": u.completion_tokens} if u else {}, **res},
            "schematic": sch, "image": os.path.abspath(os.path.join(td, "drawing.png")), "size": [W, H]}


def main():
    from openai import OpenAI
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="policy")
    ap.add_argument("--base-url", default="http://localhost:8000/v1")
    ap.add_argument("--root", default="tasks")
    ap.add_argument("--plans", default="split.json"); ap.add_argument("--key", default="test")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--greedy", action="store_true")
    ap.add_argument("--samples", type=int, default=0)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--max-tokens", type=int, default=12000)
    ap.add_argument("--rep-penalty", type=float, default=1.0, help="vLLM repetition_penalty; >1 curbs endless loops")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--runs-dir", default="runs")
    ap.add_argument("--save-best", default="")
    ap.add_argument("--min-reward", type=float, default=0.15)
    ap.add_argument("--margin", type=float, default=0.02, help="best sample must beat the plan's mean sample by this")
    a = ap.parse_args()
    client = OpenAI(base_url=a.base_url, api_key="x", timeout=3600, max_retries=1)
    plans = [p for p in json.load(open(a.plans))[a.key] if os.path.exists(os.path.join(a.root, p, "drawing.png"))]
    if a.key != "test":
        plans = [p for p in plans if p not in test_plans()]
    if a.limit:
        plans = plans[:a.limit]
    jobs = ([(p, 0, 0.0) for p in plans] if a.greedy else []) + \
           [(p, k + (1 if a.greedy else 0), a.temperature) for p in plans for k in range(a.samples)]
    out = {}
    todo = []
    for p, k, T in jobs:
        f = os.path.join(a.runs_dir, a.tag, p, f"run{k}", "episode.json")
        if os.path.exists(f):
            out.setdefault(p, {})[k] = json.load(open(f, encoding="utf8"))
        else:
            todo.append((p, k, T))
    print(f"{len(jobs)} jobs, {len(jobs) - len(todo)} done, {len(todo)} to run", flush=True)
    with ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(one, client, a.model, a.root, p, T, a.max_tokens, a.rep_penalty): (p, k) for p, k, T in todo}
        for i, f in enumerate(as_completed(futs)):
            p, k = futs[f]
            try:
                ep = f.result()
            except Exception as e:  # request failed: not saved, a rerun retries it
                print(f"[{i + 1}/{len(todo)}] {p} run{k} FAILED {e!r}"[:300], flush=True); continue
            d = os.path.join(a.runs_dir, a.tag, p, f"run{k}"); os.makedirs(d, exist_ok=True)
            json.dump(ep, open(os.path.join(d, "episode.json"), "w", encoding="utf8"), ensure_ascii=False)
            out.setdefault(p, {})[k] = ep
            r = ep["result"]
            print(f"[{i + 1}/{len(todo)}] {p:34s} run{k} reward={r['reward']:.3f} {r['finish']} {r['components']}", flush=True)
    allr = [e["result"]["reward"] for v in out.values() for e in v.values()]
    if allr:
        print(f"=== {a.tag}: {len(out)} plans, {len(allr)} episodes, mean reward {st.mean(allr):.3f}")
        if a.greedy:
            g = [v[0]["result"]["reward"] for v in out.values() if 0 in v]
            print(f"    greedy mean {st.mean(g):.3f} over {len(g)} plans")
    if a.save_best:
        n = 0
        with open(a.save_best, "w", encoding="utf8") as f:
            for p, v in out.items():
                eps = [e for e in v.values() if e["result"]["finish"] != "length"]
                if len(eps) < 2:
                    continue
                mean = st.mean(e["result"]["reward"] for e in eps)
                best = max(eps, key=lambda e: e["result"]["reward"])
                r = best["result"]["reward"]
                if r >= a.min_reward and r >= mean + a.margin:
                    W, H = best["size"]
                    sch = best["schematic"]
                    text = to_text({"m_per_px": sch["m_per_px"] or 0.0, **{k: sch[k] for k in ("walls", "rooms", "doors", "windows", "fixtures")}}, W, H)
                    f.write(json.dumps(row(p, best["image"], W, H, text, reward=r, plan_mean=round(mean, 4)), ensure_ascii=False) + "\n")
                    n += 1
        print(f"saved {n} experience rows (best sample beats its plan mean by >= {a.margin}) -> {a.save_best}")


if __name__ == "__main__":
    main()
