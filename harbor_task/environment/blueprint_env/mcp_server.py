"""MCP server for one episode (stdio). This is what an MCP agent harness (Harbor + OpenCode) connects to.

    python -m blueprint_env.mcp_server --task site279_bldg514_floor2041 --result runs/mcp/<task>/result.json

The agent sees the drawing and the tools; the ground truth is read only by the scorer when the
schematic is submitted (keep --gt outside anything the agent can read in a sandboxed setup).
The score is written to --result and is NOT shown to the agent.
"""
from __future__ import annotations

import argparse
import atexit
import io
import json
import os

from mcp.server.fastmcp import FastMCP, Image as McpImage

from .env import Episode


def _img(pil):
    buf = io.BytesIO(); pil.save(buf, "PNG")
    return McpImage(data=buf.getvalue(), format="png")


def build(ep: Episode, result_path: str | None, submission_path: str | None = None) -> FastMCP:
    mcp = FastMCP("blueprint-schematic", instructions=ep.instructions())
    state = {"written": False}

    def write_result():
        if submission_path:
            if not state["written"]:
                state["written"] = True
                os.makedirs(os.path.dirname(os.path.abspath(submission_path)), exist_ok=True)
                with open(submission_path, "w", encoding="utf8") as f:
                    json.dump(ep.submitted, f, ensure_ascii=False, indent=1)
            return
        if result_path and not state["written"]:
            state["written"] = True
            os.makedirs(os.path.dirname(os.path.abspath(result_path)), exist_ok=True)
            out = {"result": ep.result(), "schematic": ep.submitted, "last_preview": ep.last_preview, "trace": ep.trace}
            json.dump(out, open(result_path, "w", encoding="utf8"), ensure_ascii=False, indent=1)

    atexit.register(write_result)          # agent quits without submitting -> scored as empty (0)

    def reply(name, args):
        text, im = ep.call(name, args)
        if name == "submit_schematic" and ep.done:
            write_result()
        return [text, _img(im)] if im is not None else text

    @mcp.tool()
    def get_task() -> list:
        """Task instructions plus the full drawing (downscaled). Call this first."""
        W, H = ep.img.size
        im = ep.img.copy(); im.thumbnail((1600, 1600))
        return [ep.instructions() + f"\n\nThe attached overview is downscaled to {im.width}x{im.height}; "
                f"all coordinates you report are in the ORIGINAL {W}x{H} pixels. Use view_region for detail.", _img(im)]

    @mcp.tool()
    def view_region(x0: float, y0: float, x1: float, y1: float) -> list:
        """Zoomed crop of the drawing between original pixel coordinates (x0,y0)-(x1,y1), with coordinate rulers."""
        return reply("view_region", dict(x0=x0, y0=y0, x1=x1, y1=y1))

    @mcp.tool()
    def estimate_scale() -> str:
        """Estimate pixels per metre and metres per pixel from the printed scale or scale bar."""
        return reply("estimate_scale", {})

    @mcp.tool()
    def read_room_labels(x0: float | None = None, y0: float | None = None,
                         x1: float | None = None, y1: float | None = None) -> str:
        """OCR room numbers and nearby printed names, returning their original-image pixel coordinates.
        Optionally limit detections to a crop in original pixel coordinates."""
        return reply("read_room_labels", dict(x0=x0, y0=y0, x1=x1, y1=y1))

    @mcp.tool()
    def segment_rooms(seeds: list[list[float]], m_per_px: float | None = None) -> list:
        """Computer-vision room segmentation: one seed [x, y] inside each room (original pixels), e.g. at
        its printed number. Pass your m_per_px for better results (building outline, door-sized splits).
        Returns each room's outline polygon + pixel area, and an overlay image."""
        return reply("segment_rooms", dict(seeds=seeds, m_per_px=m_per_px))

    @mcp.tool()
    def measure_area(polygon: list[list[float]], m_per_px: float) -> str:
        """Area of a polygon (original pixels) in pixels and in m2 at the given metres-per-pixel scale."""
        return reply("measure_area", dict(polygon=polygon, m_per_px=m_per_px))

    @mcp.tool()
    def preview_schematic(schematic_json: str, x0: float | None = None, y0: float | None = None,
                          x1: float | None = None, y1: float | None = None) -> list:
        """Draw a schematic (JSON string, same format as submit) over the drawing, optionally cropped. Does not score."""
        return reply("preview_schematic", dict(schematic_json=schematic_json, x0=x0, y0=y0, x1=x1, y1=y1))

    @mcp.tool()
    def submit_schematic(schematic_json: str) -> str:
        """Submit the final schematic (JSON string). Ends the episode; only the first submission counts."""
        return reply("submit_schematic", dict(schematic_json=schematic_json))

    return mcp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default=os.environ.get("BLUEPRINT_TASK"))
    ap.add_argument("--root", default=os.environ.get("BLUEPRINT_ROOT", "tasks"))
    ap.add_argument("--gt", default=os.environ.get("BLUEPRINT_GT"), help="ground-truth JSON (default: <task>/ground_truth.json)")
    ap.add_argument("--result", default=os.environ.get("BLUEPRINT_RESULT"))
    ap.add_argument("--submission", default=os.environ.get("BLUEPRINT_SUBMISSION"),
                    help="write only the submitted schematic here (Harbor mode; no ground truth needed)")
    ap.add_argument("--max-calls", type=int, default=int(os.environ.get("BLUEPRINT_MAX_CALLS", 30)))
    a = ap.parse_args()
    if not a.task:
        ap.error("--task (or BLUEPRINT_TASK) is required")
    ep = Episode(os.path.join(a.root, a.task), a.gt, a.max_calls)
    result_path = None if a.submission else (a.result or os.path.join("runs", "mcp", a.task, "result.json"))
    build(ep, result_path, a.submission).run("stdio")


if __name__ == "__main__":
    main()
