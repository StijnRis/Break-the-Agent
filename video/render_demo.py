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
import time
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
    ap.add_argument("--out", type=Path, default=None, help="default: video/out/demo_<timestamp>.mp4 (only the newest 2 renders are kept)")
    ap.add_argument("--port", type=int, default=8790)
    ap.add_argument("--limit", type=float, default=0, help="render only the first N seconds (testing)")
    a = ap.parse_args()
    if a.out is None:
        a.out = HERE / "out" / f"demo_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
    a.out.parent.mkdir(parents=True, exist_ok=True)

    import make_subs
    make_subs.export()  # captions burned into the render (also written as out/subtitles.srt)
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
        # python's http.server has no Range support, so Chrome cannot seek in the clips: the recorded video
        # froze on one frame. Load every clip fully into a blob URL first; blobs seek perfectly.
        page.evaluate("""async () => {
          for (const v of document.querySelectorAll('video')) {
            if (!v.src || v.src.startsWith('blob:')) continue;
            try {
              const blob = await (await fetch(v.src)).blob();
              await new Promise(res => { v.addEventListener('loadeddata', res, { once: true }); v.src = URL.createObjectURL(blob); setTimeout(res, 8000); });
            } catch (e) { /* clip missing */ }
          }
        }""")
        scenes = page.evaluate("SCENES.map(s => ({id: s.id, start: s.start, dur: s.dur, warp: s.warp || 1, clip: s.clip || null, clipAudio: !!s.clipAudio, noTTS: !!s.noTTS}))")
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

    # ---- audio: leveled voiceovers + phone clip + sound effects (see audio_mix.py) ----
    import audio_mix
    audio_mix.export_events(scenes, HERE / 'media' / 'sfx' / 'events.json')
    mix = audio_mix.build(scenes, total, a.out.parent / "_audio")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(mix), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(total), str(a.out)], check=True)
    silent.unlink()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(a.out), "-frames:v", "1", str(a.out.parent / "cover.png")], check=True)
    keep = sorted(a.out.parent.glob("demo_*.mp4"), key=lambda p: p.stat().st_mtime)[-2:]
    for old in a.out.parent.glob("demo_*.mp4"):
        if old not in keep:
            old.unlink()
    print("wrote", a.out, "| kept:", ", ".join(p.name for p in keep))


if __name__ == "__main__":
    main()
