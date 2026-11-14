"""Gemini agent loop for the blueprint -> schematic environment (function calling over REST).

usage: python -m blueprint_env.agent <task_id>[,<task_id>...] [--model gemini-3.1-pro-preview] [--runs 1]
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import time

import requests
from PIL import Image

from .env import MAX_CALLS as MAX_TURNS, Episode

_NUM = {"type": "number"}
_PTS = {"type": "array", "items": {"type": "array", "items": _NUM}}
TOOLS = [{"functionDeclarations": [
    {"name": "view_region",
     "description": "Return a zoomed crop of the drawing between pixel coordinates (x0,y0)-(x1,y1) with "
                    "coordinate rulers in original-image pixels.",
     "parameters": {"type": "object", "properties": {"x0": _NUM, "y0": _NUM, "x1": _NUM, "y1": _NUM},
                    "required": ["x0", "y0", "x1", "y1"]}},
    {"name": "segment_rooms",
     "description": "Computer-vision room segmentation. One seed [x,y] inside each room (e.g. at its printed number) "
                    "and your m_per_px; returns each room's outline polygon + pixel area and an overlay image.",
     "parameters": {"type": "object", "properties": {"seeds": _PTS, "m_per_px": _NUM}, "required": ["seeds"]}},
    {"name": "measure_area",
     "description": "Area of a polygon (original pixels) in pixels and m2 at the given metres-per-pixel.",
     "parameters": {"type": "object", "properties": {"polygon": _PTS, "m_per_px": _NUM},
                    "required": ["polygon", "m_per_px"]}},
    {"name": "preview_schematic",
     "description": "Render a schematic (JSON string, same format as submit) over the drawing, optionally "
                    "cropped to (x0,y0)-(x1,y1). Returns the image plus element counts. Does not score.",
     "parameters": {"type": "object", "properties": {
         "schematic_json": {"type": "string"}, "x0": _NUM, "y0": _NUM, "x1": _NUM, "y1": _NUM},
         "required": ["schematic_json"]}},
    {"name": "submit_schematic",
     "description": "Submit the final schematic (JSON string). Ends the episode.",
     "parameters": {"type": "object", "properties": {"schematic_json": {"type": "string"}},
                    "required": ["schematic_json"]}},
]}]


def _png_part(img: Image.Image) -> dict:
    buf = io.BytesIO(); img.save(buf, "PNG")
    return {"inlineData": {"mimeType": "image/png", "data": base64.b64encode(buf.getvalue()).decode()}}


def _api(model, key, body, retries=6):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    for i in range(retries):
        try:
            r = requests.post(url, json=body, headers={"x-goog-api-key": key}, timeout=600)
            if r.status_code == 200:
                return r.json()
            err = r.text[:400]
        except requests.RequestException as e:
            err = str(e)
        print(f"   api retry {i}: {err}", flush=True)
        time.sleep(10 * (i + 1))
    raise RuntimeError("API failed: " + err)


def _visible_note(text: str, limit: int = 650) -> str:
    """Keep user-visible model notes readable; never include hidden thought parts."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    clipped = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return clipped + " … (continued in next step)"


def run_episode(task_dir: str, model: str, key: str, log_dir: str, max_calls: int = MAX_TURNS,
                on_event=None, score_result: bool = True, user_prompt: str | None = None) -> dict:
    ep = Episode(task_dir, max_calls=max_calls)
    W, H = ep.img.size
    contents = [{"role": "user", "parts": [
        {"text": user_prompt or f"Digitise this floor plan into the schematic format. Image size {W}x{H} px."},
        _png_part(ep.img)]}]
    body_base = {"systemInstruction": {"parts": [{"text": ep.instructions()}]},
                 "tools": TOOLS,
                 "generationConfig": {"maxOutputTokens": 8192, "mediaResolution": "MEDIA_RESOLUTION_HIGH",
                                      "thinkingConfig": {"thinkingLevel": "low"}}}
    trace = []; usage = {"in": 0, "out": 0}; t0 = time.time(); calls = 0
    while calls < max_calls + 2 and ep.submitted is None:
        if on_event:
            on_event({"type": "request_start", "turn": len(trace) + 1,
                      "message": f"Gemini is composing its next response (request {len(trace) + 1})."})
        resp = _api(model, key, {**body_base, "contents": contents})
        um = resp.get("usageMetadata", {})
        usage["in"] += um.get("promptTokenCount", 0); usage["out"] += um.get("candidatesTokenCount", 0) + um.get("thoughtsTokenCount", 0)
        cand = (resp.get("candidates") or [{}])[0]
        content = cand.get("content") or {"role": "model", "parts": []}
        content["role"] = "model"
        contents.append(content)
        fcs = [p["functionCall"] for p in content.get("parts", []) if "functionCall" in p]
        text = " ".join(p.get("text", "") for p in content.get("parts", []) if "text" in p and not p.get("thought"))
        if not fcs:
            trace.append({"turn": len(trace), "text": text[:2000], "finish": cand.get("finishReason")})
            if on_event:
                on_event({"type": "note", "message": _visible_note(text) if text else "The agent is reviewing its last tool result."})
            contents.append({"role": "user", "parts": [{"text": "Continue using the tools. Call submit_schematic with your final schematic."}]})
            calls += 1
            continue
        parts = []; imgs = []
        for fc in fcs:
            calls += 1
            res, img = ep.call(fc["name"], fc.get("args", {}))
            a = dict(fc.get("args", {}))
            if "schematic_json" in a:
                a["schematic_json"] = f"<{len(a['schematic_json'])} chars>"
            trace.append({"turn": len(trace), "text": text[:2000], "tool": fc["name"], "args": a, "result": res})
            if on_event:
                if text:
                    on_event({"type": "note", "message": _visible_note(text)})
                on_event({"type": "tool", "tool": fc["name"], "args": a,
                          "result": res[:1400], "image": img})
            parts.append({"functionResponse": {"name": fc["name"], "response": {"result": res}}})
            if img is not None:
                imgs.append(img)
            print(f"   [{calls}] {fc['name']} {a} -> {res[:120]}", flush=True)
        for im in imgs:
            parts.append(_png_part(im))
        contents.append({"role": "user", "parts": parts})

    sch = ep.submitted
    out = {"model": model, "seconds": round(time.time() - t0), "tokens": usage}
    if score_result:
        out.update(ep.result(elapsed_seconds=time.time() - t0))
    elif sch is not None:
        out.update({"task": ep.task, "submitted": True, "tool_calls": ep.calls})
    os.makedirs(log_dir, exist_ok=True)
    json.dump({"result": out, "schematic": sch, "last_preview": ep.last_preview, "trace": trace},
              open(os.path.join(log_dir, "episode.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks")
    ap.add_argument("--model", default="gemini-3.1-pro-preview")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--run-offset", type=int, default=0)
    ap.add_argument("--root", default="tasks")
    ap.add_argument("--out", default="runs")
    ap.add_argument("--max-calls", type=int, default=MAX_TURNS)
    ap.add_argument("--label", default="", help="run folder name (default: the model name)")
    a = ap.parse_args()
    key = os.environ.get("GEMINI_API_KEY") or dict(
        l.strip().split("=", 1) for l in open(".env") if "=" in l)["GEMINI_API_KEY"]
    for t in a.tasks.split(","):
        for r in range(a.run_offset, a.run_offset + a.runs):
            print(f"== {t} run {r} ({a.model})", flush=True)
            res = run_episode(os.path.join(a.root, t), a.model, key, os.path.join(a.out, a.label or a.model, t, f"run{r}"), a.max_calls)
            print(json.dumps({k: res[k] for k in ("task", "reward", "components", "tool_calls", "seconds", "tokens")}), flush=True)


if __name__ == "__main__":
    main()
