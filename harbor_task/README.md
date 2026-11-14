# Harbor task: Blueprint schematic

The agent digitizes one Swiss apartment floor plan into a formal schematic using the supplied MCP tools. The challenge is precise visual measurement: room boundaries, labels, walls, openings, fixtures, and scale must agree with surveyed geometry. The verifier uses the repository's weighted scorer and returns its 0–1 score, so partial credit is preserved.

## Tools available to the agent

The agent connects to the `blueprint` MCP server and has a budget of 30 tool calls. The server exposes:

| Tool | Inputs | What it does |
|---|---|---|
| `get_task` | none | Returns the task rules and a downscaled overview. Call this first. All coordinates in later calls use the original image pixels. |
| `view_region` | `x0`, `y0`, `x1`, `y1` | Returns a zoomed crop with rulers labeled in original-image coordinates. |
| `estimate_scale` | none | Estimates pixels per metre and metres per pixel from the printed scale or scale bar, and reports which source it used. |
| `read_room_labels` | optional `x0`, `y0`, `x1`, `y1` | OCRs numbered rooms and nearby names, returning their original-image pixel locations. An optional crop limits detections. |
| `segment_rooms` | `seeds` as `[[x,y], ...]`; optional `m_per_px` | Proposes room polygons from one seed inside each room. Supplying scale can improve the building boundary and door-gap handling. Returns polygons, areas, closure flags, and an overlay. Review and correct its proposals. |
| `measure_area` | `polygon`, `m_per_px` | Calculates a polygon's area in pixels and square metres at the supplied scale. |
| `preview_schematic` | `schematic_json`; optional crop bounds | Draws the current schematic over the drawing, optionally zoomed, so geometry can be reviewed before submission. |
| `submit_schematic` | `schematic_json` | Submits the final schematic and ends the episode. Only the first submission counts. |

Alongside these eight MCP tools, OpenCode has its normal terminal and file inspection/editing tools inside the task workspace. It can use Python and the installed drawing libraries available in that workspace. The task image contains the drawing and the MCP runtime; the surveyed answer and score are reserved for the separate verifier.

Run from the repository root after installing Harbor and Docker:

```sh
harbor run -p ./harbor_task -a opencode -m <provider/model>
```

The Harbor task contains the environment, instructions, verifier, and reference solution. The separate verifier container holds the ground truth; the agent receives only the floor-plan image. Harbor copies `/tmp/answer.json` from the agent to the verifier, which writes `/logs/verifier/reward.txt`.

After every scored trial, the verifier writes `/logs/verifier/review.png`, a three-panel image with the public source drawing, the submitted schematic on a plain canvas, and an error-only diff. It also writes the individual `/logs/verifier/comparison.png` and `/logs/verifier/errors.png` images. The diagnostic is generated only after scoring in the separate verifier: red marks missing surveyed geometry and green marks extra or misplaced submitted geometry.

## Harbor playthrough

Harbor 0.26.0 ran this task with OpenCode and `google/gemini-3.1-pro-preview`. The verifier scored the submitted schematic **0.6159**. The agent submitted 88 walls, 20 rooms, 23 doors, 12 fixtures, and no windows. The score file, comparison image, agent log, and trajectory are in [`results/harbor_run.md`](../results/harbor_run.md) and the linked Harbor job folders.
