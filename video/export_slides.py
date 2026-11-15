"""Export the video as a slide deck: one 1920x1080 page per scene -> video/out/slides.pdf

    python video/export_slides.py
Each slide is the last frame of its scene (subtitles off). The cover is the first page.
"""
from __future__ import annotations

import functools
import http.server
import io
import threading
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PICK = {"intro": 27.9}   # seconds into the scene; every other slide is the very last frame of its scene (all text and numbers complete)

BLOB = """async () => {
  for (const v of document.querySelectorAll('video')) {
    if (!v.src || v.src.startsWith('blob:')) continue;
    try { const b = await (await fetch(v.src)).blob();
      await new Promise(r => { v.addEventListener('loadeddata', r, { once: true }); v.src = URL.createObjectURL(b); setTimeout(r, 8000); });
    } catch (e) {}
  }
}"""
WAIT = """() => new Promise(res => { const t0 = performance.now(); const f = () => {
  const vs = [...document.querySelectorAll('.layer.on video')];
  if (vs.every(v => !v.seeking && v.readyState >= 2) || performance.now() - t0 > 3000) res(); else setTimeout(f, 5); }; f(); })"""


def main() -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    handler.log_message = lambda *a, **k: None  # type: ignore[attr-defined]
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 8791), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    pages = []
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge")
        page = b.new_page(viewport={"width": 1920, "height": 1080})
        page.goto("http://127.0.0.1:8791/index.html")
        page.wait_for_function("window.PLAYER && typeof SCENES !== 'undefined'")
        page.evaluate("document.body.classList.add('clean','nosubs'); window.dispatchEvent(new Event('resize'))")
        page.wait_for_timeout(2500)
        page.evaluate(BLOB)
        scenes = page.evaluate("SCENES.map(s => ({id: s.id, start: s.start, dur: s.dur}))")
        shots = [("cover", 0.02)] + [(s["id"], s["start"] + PICK.get(s["id"], s["dur"] - 0.03)) for s in scenes]
        for name, t in shots:
            page.evaluate(f"PLAYER.seek({t})")
            page.evaluate(WAIT)
            page.wait_for_timeout(120)
            im = Image.open(io.BytesIO(page.screenshot(type="png"))).convert("RGB")
            pages.append(im)
            (HERE / "out" / "slides").mkdir(parents=True, exist_ok=True)
            im.save(HERE / "out" / "slides" / f"{len(pages):02}_{name}.png")
            print("slide", name)
        b.close()
    httpd.shutdown()
    out = HERE / "out" / "slides.pdf"
    out.parent.mkdir(exist_ok=True)
    pages[0].save(out, "PDF", resolution=144.0, save_all=True, append_images=pages[1:], quality=92)
    print("wrote", out, f"({len(pages)} slides)")


if __name__ == "__main__":
    main()
