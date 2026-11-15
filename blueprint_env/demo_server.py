"""Local web demo for the blueprint digitisation challenge. Run with python -m blueprint_env.demo_server."""
from __future__ import annotations

import base64
import io
import json
import os
import secrets
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "tasks"
WEB = ROOT / "web_demo"
MODEL = os.environ.get("DEMO_MODEL", "gemini-3.1-pro-preview")
JOBS: dict[str, dict] = {}
LOCK = threading.Lock()
LATEST_JOB_ID: str | None = None
VIDEO_JOB: dict[str, str] = {"stage": "ready" if (ROOT / "results" / "final_pitch_video_v3.mp4").exists() else "idle"}


def _data_url(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _update(job_id, **values):
    with LOCK:
        JOBS[job_id].update(values)


def _run(job_id, task_dir: Path, task_id: str, has_gt: bool, prompt: str):
    try:
        from . import reference
        from .agent import run_episode
        from .render import overlay
        from .score import score

        image_path = task_dir / "drawing.png"
        drawing = Image.open(image_path).convert("RGB")
        with LOCK:
            JOBS[job_id]["visuals"]["input"] = _data_url(drawing)
            JOBS[job_id].update(stage="working", message="Reference solver and Gemini started in parallel.")

        def make_reference():
            gt = json.loads((task_dir / "ground_truth.json").read_text(encoding="utf-8")) if has_gt else None
            schematic = reference.solve(drawing)
            visuals = {"our_model": _data_url(overlay(str(image_path), schematic))}
            if gt is not None:
                visuals["reference"] = _data_url(overlay(str(image_path), gt))
            return {"visuals": visuals,
                    "reference_score": score(gt, gt, drawing.size) if gt is not None else None,
                    "our_model_score": score(gt, schematic, drawing.size) if gt is not None else None,
                    "our_model_counts": {k: len(schematic.get(k, [])) for k in ("walls", "rooms", "doors", "windows", "fixtures")}}

        def run_gemini():
            key = os.environ.get("GEMINI_API_KEY")
            env_file = ROOT / ".env"
            if not key and env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("GEMINI_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
            if not key:
                raise RuntimeError("Add GEMINI_API_KEY to .env or the environment to run the live agent.")

            def on_event(event):
                if isinstance(event.get("image"), Image.Image):
                    event["image"] = _data_url(event["image"])
                with LOCK:
                    job = JOBS[job_id]
                    job["events"].append({"at": round(time.time()), **event})
                    job["message"] = event.get("message", event.get("tool", "Gemini is working…"))

            out_dir = Path(tempfile.gettempdir()) / "break-agent-demo" / job_id
            result = run_episode(str(task_dir), MODEL, key, str(out_dir), max_calls=30,
                                 on_event=on_event, score_result=has_gt, user_prompt=prompt)
            schematic = json.loads((out_dir / "episode.json").read_text(encoding="utf-8")).get("schematic")
            if schematic is None:
                raise RuntimeError("Gemini finished without submitting a schematic.")
            gt = json.loads((task_dir / "ground_truth.json").read_text(encoding="utf-8")) if has_gt else None
            return {"visuals": {"gemini": _data_url(overlay(str(image_path), schematic))},
                    "gemini_score": score(gt, schematic, drawing.size) if gt is not None else None,
                    "gemini_counts": {k: len(schematic.get(k, [])) for k in ("walls", "rooms", "doors", "windows", "fixtures")},
                    "result": {"seconds": result.get("seconds"), "tool_calls": result.get("tool_calls"), "model": MODEL}}

        failures = []
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="blueprint-demo") as pool:
            futures = {pool.submit(make_reference): "reference", pool.submit(run_gemini): "gemini"}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    output = future.result()
                    with LOCK:
                        job = JOBS[job_id]
                        job["visuals"].update(output.pop("visuals"))
                        job.update(output)
                        completed = job.get("completed", set())
                        completed.add(name)
                        job["completed"] = completed
                        if len(completed) < 2:
                            job["message"] = "Reference solution ready; Gemini is still working." if name == "reference" else "Gemini submitted; reference solver is finishing."
                except Exception as exc:
                    failures.append(f"{name}: {exc}")
            if failures:
                _update(job_id, stage="error", error="; ".join(failures), message="One or more results could not be generated.")
            else:
                _update(job_id, stage="done", message="Both solutions are ready.")
    except Exception as exc:  # surface actionable errors to the local demo UI
        _update(job_id, stage="error", error=str(exc), message="The run could not be completed.")


def _render_pitch_video():
    """Rebuild the local pitch MP4 from generated narration and presentation assets."""
    try:
        with LOCK:
            VIDEO_JOB.update(stage="rendering", message="Rendering motion graphics, sound bed, and captions…")
        completed = subprocess.run(
            [sys.executable, str(ROOT / "video" / "render_recorded_pitch.py")], cwd=ROOT,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=600,
        )
        if completed.returncode:
            raise RuntimeError(completed.stderr[-900:] or "Video renderer stopped unexpectedly.")
        with LOCK:
            VIDEO_JOB.update(stage="ready", message="Pitch video is ready to download.")
    except Exception as exc:
        with LOCK:
            VIDEO_JOB.update(stage="error", message=str(exc))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def _send(self, status, body, content_type="application/json; charset=utf-8"):
        raw = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, (WEB / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif path == "/api/tasks":
            split = json.loads((ROOT / "split.json").read_text(encoding="utf-8"))
            tasks = [{"id": task, "label": task.replace("_", " · ")} for task in split["test"]]
            self._send(200, json.dumps(tasks))
        elif path.startswith("/api/plan/"):
            task_id = path.rsplit("/", 1)[-1]
            split = json.loads((ROOT / "split.json").read_text(encoding="utf-8"))
            if task_id not in split["test"]:
                self._send(404, json.dumps({"error": "Plan not found"}))
                return
            image = Image.open(TASKS / task_id / "drawing.png").convert("RGB")
            self._send(200, json.dumps({"image": _data_url(image), "size": image.size}))
        elif path.startswith("/api/jobs/"):
            job_id = path.rsplit("/", 1)[-1]
            query = parse_qs(urlparse(self.path).query)
            after = max(0, int(query.get("events_after", ["0"])[0]))
            requested_images = [k for k in query.get("images", [""])[0].split(",") if k]
            with LOCK:
                job = JOBS.get(job_id)
                payload = ({k: job.get(k) for k in ("id", "task", "has_gt", "stage", "message", "reference_score",
                            "our_model_score", "our_model_counts", "gemini_score", "gemini_counts", "result", "error")}
                           if job else None)
                if payload:
                    events = job.get("events", [])
                    payload["events"] = events[after:]
                    payload["event_count"] = len(events)
                    visuals = job.get("visuals", {})
                    payload["visuals"] = {k: visuals[k] for k in requested_images if k in visuals}
            self._send(200 if payload else 404, json.dumps(payload or {"error": "Run not found"}))
        elif path == "/api/latest":
            with LOCK:
                latest = JOBS.get(LATEST_JOB_ID) if LATEST_JOB_ID else None
                payload = {"id": latest.get("id"), "task": latest.get("task")} if latest else {"id": None}
            self._send(200, json.dumps(payload))
        elif path == "/api/render-video":
            with LOCK:
                self._send(200, json.dumps(VIDEO_JOB))
        elif path == "/artifacts/final_pitch_video.mp4":
            artifact = ROOT / "results" / "final_pitch_video_v3.mp4"
            if not artifact.exists():
                self._send(404, "Video has not been rendered yet.", "text/plain; charset=utf-8")
            else:
                self._send(200, artifact.read_bytes(), "video/mp4")
        else:
            self._send(404, "Not found", "text/plain; charset=utf-8")

    def do_POST(self):
        global LATEST_JOB_ID
        endpoint = urlparse(self.path).path
        if endpoint == "/api/render-video":
            with LOCK:
                if VIDEO_JOB.get("stage") != "rendering":
                    VIDEO_JOB.update(stage="queued", message="Pitch render queued…")
                    threading.Thread(target=_render_pitch_video, daemon=True).start()
                payload = dict(VIDEO_JOB)
            self._send(202, json.dumps(payload))
            return
        if endpoint != "/api/run":
            self._send(404, json.dumps({"error": "Not found"}))
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 16 * 1024 * 1024:
                raise ValueError("Image upload is too large (maximum 16 MB).")
            payload = json.loads(self.rfile.read(length))
            task_id = payload.get("task_id")
            if task_id:
                split = json.loads((ROOT / "split.json").read_text(encoding="utf-8"))
                if task_id not in split["test"]:
                    raise ValueError("Choose a benchmark plan from the test set.")
                task_dir = TASKS / task_id
                has_gt = True
            elif payload.get("image"):
                raw = base64.b64decode(payload["image"].split(",", 1)[-1], validate=True)
                image = Image.open(io.BytesIO(raw)).convert("RGB")
                task_dir = Path(tempfile.gettempdir()) / "break-agent-demo" / ("upload-" + secrets.token_hex(8))
                task_dir.mkdir(parents=True, exist_ok=True)
                image.save(task_dir / "drawing.png")
                has_gt = False
                task_id = "Uploaded floor plan"
            else:
                raise ValueError("Choose a sample plan or upload a floor plan image.")
            job_id = secrets.token_urlsafe(12)
            with LOCK:
                JOBS[job_id] = {"id": job_id, "task": task_id, "has_gt": has_gt, "stage": "queued",
                                "message": "Starting…", "events": [], "visuals": {}, "result": None}
                LATEST_JOB_ID = job_id
            prompt = str(payload.get("prompt") or "Digitise this floor plan into the schematic format.")[:2000]
            threading.Thread(target=_run, args=(job_id, task_dir, task_id, has_gt, prompt), daemon=True).start()
            self._send(202, json.dumps({"id": job_id, "task": task_id, "has_gt": has_gt}))
        except Exception as exc:
            self._send(400, json.dumps({"error": str(exc)}))


def main():
    server = ThreadingHTTPServer(("127.0.0.1", int(os.environ.get("PORT", "8766"))), Handler)
    print(f"Blueprint demo ready at http://127.0.0.1:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
