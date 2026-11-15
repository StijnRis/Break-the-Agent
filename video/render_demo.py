"""Render the browser demo video (index.html) to video/out/demo.mp4.

Frame by frame: seek the player clock, screenshot the stage, pipe frames to ffmpeg.
Audio is mixed from the per-scene voiceovers (media/vo/<id>.mp3) and the audio of
filmed clips (clipAudio scenes). Uses the installed Microsoft Edge (no browser download).

    python video/render_demo.py [--fps 30] [--out video/out/demo.mp4]
"""
from __future__ import annotations

import argparse
import functools
import http.server
import subprocess
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
WAIT_VIDEOS = """() => new Promise(res => {
  const t0 = performance.now();
  const f = () => {
    const vs = [...document.querySelectorAll('.layer.on video')];
    if (vs.every(v => !v.seeking && v.readyState >= 2) || performance.now() - t0 > 3000) res(); else setTimeout(f, 4);
  };
  f();
})"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--out", type=Path, default=HERE / "out" / "demo.mp4")
    ap.add_argument("--port", type=int, default=8790)
    ap.add_argument("--limit", type=float, default=0, help="render only the first N seconds (testing)")
    a = ap.parse_args()
    a.out.parent.mkdir(parents=True, exist_ok=True)

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    handler.log_message = lambda *args, **kw: None  # type: ignore[attr-defined]
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    silent = a.out.with_suffix(".silent.mp4")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", args=["--autoplay-policy=no-user-gesture-required"])
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(f"http://127.0.0.1:{a.port}/index.html")
        page.wait_for_function("window.PLAYER && typeof SCENES !== 'undefined'")
        page.evaluate("document.body.classList.add('clean'); window.dispatchEvent(new Event('resize'))")
        page.wait_for_timeout(2500)  # let media metadata load
        scenes = page.evaluate("SCENES.map(s => ({id: s.id, start: s.start, dur: s.dur, clip: s.clip || null, clipAudio: !!s.clipAudio, noTTS: !!s.noTTS}))")
        total = page.evaluate("PLAYER.total")
        if a.limit:
            total = min(total, a.limit)
        frames = int(total * a.fps)
        ff = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(a.fps), "-c:v", "mjpeg", "-i", "pipe:0",
             "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", str(silent)],
            stdin=subprocess.PIPE)
        for i in range(frames):
            page.evaluate(f"PLAYER.seek({i / a.fps})")
            page.evaluate(WAIT_VIDEOS)
            ff.stdin.write(page.screenshot(type="jpeg", quality=93))
            if i % 150 == 0:
                print(f"frame {i}/{frames}", flush=True)
        ff.stdin.close()
        ff.wait()
        browser.close()
    httpd.shutdown()

    # ---- audio ----
    inputs, filters, labels = [], [], []
    for s in scenes:
        parts = []
        if not s["noTTS"] and (HERE / "media" / "vo" / f"{s['id']}.mp3").exists():
            parts.append(HERE / "media" / "vo" / f"{s['id']}.mp3")
        if s["clip"] and s["clipAudio"] and (HERE / "media" / s["clip"]).exists():
            parts.append(HERE / "media" / s["clip"])
        for path in parts:
            n = len(inputs) // 2
            inputs += ["-i", str(path)]
            ms = int(s["start"] * 1000)
            filters.append(f"[{n + 1}:a]atrim=0:{s['dur']},asetpts=PTS-STARTPTS,adelay={ms}|{ms}[a{n}]")
            labels.append(f"[a{n}]")
    if labels:
        filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0,alimiter=limit=0.95[aout]")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), *inputs, "-filter_complex", ";".join(filters),
               "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(total), str(a.out)]
        subprocess.run(cmd, check=True)
        silent.unlink()
    else:
        silent.replace(a.out)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
