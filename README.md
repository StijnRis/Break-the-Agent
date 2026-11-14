# Blueprint → Schematic: an RL environment for reading construction drawings

## Run the interactive demo website

Install the project dependencies once, then start the local demo from the repository root:

```bash
uv sync
uv run python -m blueprint_env.demo_server
```

Open `http://127.0.0.1:8766`. Choose one of the 15 held-out benchmark plans or upload a floor-plan image, edit the prepared prompt, and run the agent. The page shows four full-image views: the source drawing, surveyed answer, our computer-vision solver, and Gemini's submission. The reference solver and Gemini run concurrently. Gemini's panel opens on a step-by-step reasoning/activity view, including zoom coordinates and returned crops; it switches to the submitted output when the run finishes. Benchmark plans include per-component weighted scores. Uploaded drawings can be compared visually but have no score because there is no surveyed answer key.

The live agent uses the Gemini runner and needs `GEMINI_API_KEY` in `.env` or the environment. Set `DEMO_MODEL` to a supported Gemini model name to change the model; the default is `gemini-3.1-pro-preview`. The reference solver runs locally. The demo binds to localhost only.

An agent gets a raster construction floor plan (one storey of a Swiss apartment building) and has to turn it into a **formal schematic**. The schematic holds walls, room outlines with their printed number and name, doors, windows, sanitary and kitchen fixtures, and the drawing scale, all in image-pixel coordinates. With a correct schematic, questions like "net area of room 2.05?" or "how many WCs?" become a few lines of deterministic code. Producing the schematic is the skill worth learning.

Frontier agents are poor at this. On the same drawings they score **0.26–0.29**, while our scripted computer-vision reference scores **0.57** and the reward ceiling is **1.0**. The agent has every tool it needs (zoom, a room segmenter, an area calculator, an overlay preview). Its failures come from measuring and committing to precise geometry, not from missing information.

The brief is in [CHALLENGE.md](CHALLENGE.md), with a table mapping each judging criterion to where this repository answers it. Slide-ready figures are in [presentation/](presentation) (rebuild them with `python -m blueprint_env.make_figures`).

## Harbor submission

The organizer's update is saved in [ORGANIZER_REQUIREMENTS.md](ORGANIZER_REQUIREMENTS.md). A Harbor task for the `site279_bldg514_floor2041` benchmark plan is packaged in [harbor_task/](harbor_task), including the required task files and isolated verifier. It has been run with Harbor/OpenCode and scored 0.6159. The run summary, logs, trajectory, and source-versus-submission comparison image are linked from [results/harbor_run.md](results/harbor_run.md).

The AI receives eight MCP tools: `get_task` (instructions and overview), `view_region` (zoom with pixel rulers), `estimate_scale` (scale bar/title-block estimate), `read_room_labels` (room-label OCR and coordinates), `segment_rooms` (seeded polygon proposals), `measure_area` (pixel and square-metre area), `preview_schematic` (overlay review), and `submit_schematic` (final answer). Full input and output descriptions are in [the Harbor task README](harbor_task/README.md).

Data: Swiss Dwellings (Archilyse AG, CC BY 4.0, doi:10.5281/zenodo.7788422), as rendered for Junction 2026. Each PNG comes with the DXF it was drawn from, so the ground truth is exact.

## Run the evaluation (one command)

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt     # Linux/macOS: .venv/bin/pip
python -m blueprint_env.evaluate
```

This scores every row below on the fixed 15-plan test split (`split.json`) and writes `results/summary.md` and `results/summary.json`. The rows are the ground-truth ceiling, the CV reference (recomputed if missing), do-nothing, stop-early, the exploit suite, and every agent run found under `runs/`.

To also run a frontier agent with our Gemini runner, put `GEMINI_API_KEY=...` in `.env` and run:

```bash
python -m blueprint_env.evaluate --agent gemini-3.1-pro-preview --runs 3
```

## Results (test split, 15 plans)

| run | episodes | reward | sd over runs | walls | rooms | doors | windows | fixtures | areas |
|---|---|---|---|---|---|---|---|---|---|
| ceiling (ground-truth replay) | 15 | **1.000** | 0.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| **reference (CV solver, no ground truth)** | 15 | **0.573** | 0.000 | 0.89 | 0.59 | 0.56 | 0.49 | 0.09 | 0.37 |
| agent: gemini-3-flash-preview | 6 | **0.294** | – | 0.50 | 0.26 | 0.17 | 0.24 | 0.41 | 0.01 |
| agent: gemini-3.1-pro-preview (3 runs) | 18 | **0.263** | 0.016 | 0.39 | 0.29 | 0.19 | 0.17 | 0.28 | 0.09 |
| do nothing | 15 | **0.000** | 0.000 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

`results/summary.md` holds the current table, including the stop-early rows and the agent stop-early run (`runs/stop-early-gemini-3-flash-4calls`).

Notes on these numbers:
- The Gemini runs above were made before `segment_rooms` and `measure_area` were added to the toolset. They cover 6 of the 15 test plans. Rerun them with `--agent` for the full split.
- The reference is deterministic, so its sd over runs is 0. The agent's sd is computed over its 3 runs.

### Where the agent fails (and why that is a fair test)

- **Scale (areas ≈ 0.01–0.09).** The agent rarely derives `m_per_px` from the scale bar or the printed "1:100 (A3)". It often guesses, and then every area is off. The printed scale and the scale bar are on every sheet, and `measure_area` checks a guess in one call.
- **Rough room outlines (rooms ≈ 0.27).** The agent draws boxes by eye from a downscaled view instead of zooming in. It also doesn't use `segment_rooms`, which returns exact outlines from a seed point per room. The reference does exactly that, and gets rooms to 0.59 and areas to 0.37.
- **Doors and windows (≈ 0.2).** The agent counts too few or places them by eye, with an error above 40 cm. They are visible in `view_region` crops at full resolution.
- **Walls (≈ 0.4–0.5).** The agent outlines the building's outer shell and skips the interior partitions.

## The environment

| | |
|---|---|
| Observation | the drawing (2480×1753 px, printed room areas masked out so they can't be copied), plus tool outputs |
| Actions (tools) | `view_region` (zoomed crop with pixel rulers), `segment_rooms` (CV room outlines from seed points), `measure_area`, `preview_schematic` (overlay of the draft on the drawing), `submit_schematic` |
| Budget | 30 tool calls. After that only `submit_schematic` is accepted. No submission scores 0. |
| Goal | submit a schematic that matches the surveyed geometry |
| Reward | `blueprint_env/score.py`, a number in [0, 1], shown in the table below |

### Reward (`blueprint_env/score.py`)

| component | weight | how |
|---|---|---|
| walls | 0.25 | mask F1, 15 cm tolerance |
| rooms | 0.25 | Hungarian match on polygon IoU (credit ramps from IoU 0.5 to 0.9); half credit if the label is wrong |
| doors | 0.15 | Hungarian match, opening midpoint within 40 cm, F1 |
| windows | 0.15 | midpoint within 40 cm, F1 |
| fixtures | 0.10 | same type (wc, washbasin, bathtub, shower, kitchen), within 50 cm, F1 |
| areas | 0.10 | share of GT rooms whose area, computed with the agent's own scale, is within 5 % |
| speed | ×0.90–1.00 | multiplier on geometry earned: full credit through 5 minutes, decreasing linearly to ×0.90 at the 8-minute deadline |

- Placement is judged with the **true** scale.
- Calibration pays only through `areas`, which also requires the room to be matched, so neither part can be farmed on its own.
- Every class is an F1 score, so both missing and extra elements cost points.
- A speed bonus cannot be farmed: it only multiplies geometry already earned.

### Reward integrity (mean reward on the test split, `python -m blueprint_env.baselines`)

| attempt | reward |
|---|---|
| ground truth (ceiling) | 1.000 |
| do nothing / no submission | 0.000 |
| scale only | 0.000 |
| one giant room covering the building | 0.000 |
| one wall = whole building box | 0.094 |
| thick ring wall around the building | 0.073 |
| grid of rooms over the building (as many cells as rooms) | 0.002 |
| every fixture type stacked on every true fixture | 0.033 |
| true room outlines, every name set to the most common label | 0.914 (< 1.0) |
| 961 doors + windows + fixtures on a grid | 0.011 |
| malformed / NaN / junk JSON | 0.000 |
| correct geometry, rooms duplicated ×3 | 0.875 (< 1.0) |
| correct geometry, scale ×1.3 | 0.900 (< 1.0) |
| stop early: first 25 % / 50 % of the reference's elements | 0.28 / 0.43 (proportional to the work done) |

**Fairness fixes found while auditing.** These were all applied before the agent runs reported above:
- Room labels are compared without case or accents, so `Pièce` matches `piece`.
- Plain empty boxes are no longer scored as washing machines. The drawings draw them without the legend's washing-machine circle, so an agent following the legend would have been penalised.
- The instructions now say how double doors are counted (one door per leaf), matching the ground truth.

**Ground-truth quality.** `build_tasks` checks every plan: the DXF must line up with the PNG at the scale printed in the title block, and the GT walls must lie on drawn ink. A plan that fails is excluded (`split.json` → `excluded`). Two of the 65 preview plans had been registered at 1:300 instead of the printed 1:100. One was fixed by constraining the registration to the printed scale; the other could not be aligned and is excluded.

## Running in an MCP agent harness (Harbor + OpenCode)

The environment is a stdio MCP server, with one server process per episode:

```bash
python -m blueprint_env.mcp_server --task site279_bldg514_floor2041 --result runs/<agent>/site279_bldg514_floor2041/run0/episode.json
```

It provides the tools `get_task`, `view_region`, `segment_rooms`, `measure_area`, `preview_schematic` and `submit_schematic`.
- Images come back as MCP image content.
- On submit, or when the server exits, the episode is scored and written to `--result`, in the same format `evaluate.py` reads.
- The score is **never shown to the agent.**

Example OpenCode config (`opencode.json`):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "blueprint": {
      "type": "local",
      "command": ["python", "-m", "blueprint_env.mcp_server", "--task", "site279_bldg514_floor2041",
                  "--result", "runs/opencode/site279_bldg514_floor2041/run0/episode.json"],
      "enabled": true
    }
  }
}
```

> **Important for sandboxed harnesses.** The agent must not be able to read `tasks/*/ground_truth.json`. Copy only `drawing.png` into the agent's workspace, and keep the ground truth with the scorer: pass `--gt` / `BLUEPRINT_GT` to a path outside the sandbox, or run the MCP server outside it. Every flag can also be set by environment variable (`BLUEPRINT_TASK`, `BLUEPRINT_ROOT`, `BLUEPRINT_GT`, `BLUEPRINT_RESULT`, `BLUEPRINT_MAX_CALLS`).

## The reference run (`blueprint_env/reference.py`)

A scripted solver that sees only what the agent sees and never touches the ground truth:

```bash
python -m blueprint_env.reference --out runs/reference-cv
```

It works in this order:
1. **Text:** OCR (rapidocr, offline) reads the printed scale "1:N" and every room number and name.
2. **Walls:** thick straight ink, turned into rectangles.
3. **Building footprint:** all strokes closed over openings, with the page frame removed.
4. **Rooms:** a watershed of the free space, seeded at each printed room number. This is the same algorithm the agent gets through `segment_rooms`.
5. **Doors:** where two rooms touch without a wall between them.
6. **Windows and exterior doors:** gaps in the outer wall.
7. **Fixtures:** closed thin-line symbols, classified by size and contents following the legend. This is the weakest part (F1 0.09).

It scores 0.573 on the test split and 0.575 over all 64 valid plans, in about 8 s per plan.

## Training a smaller model (stretch goal): `modal_app.py`

The pipeline trains Qwen3-VL-2B on a Modal L4 (24 GB), starting with ground-truth fine-tuning and then training on experience scored by the environment. See [TRAINING.md](TRAINING.md) for the complete run order, including a Harbor-on-Modal verifier run:

```bash
modal run --detach modal_app.py                  # full pipeline; finished stages are skipped
modal run modal_app.py --stages status           # what is done, with summaries
modal volume get blueprint-vol runs/ .           # bring the model's test runs home
python -m blueprint_env.evaluate                 # the table gains rows: qwen3vl-2b-base / -sft / -sft-exp
```

| stage | what |
|---|---|
| fetch, build, plans | full Junction dataset (~1,000 Swiss plans), alignment-checked ground truth, fixed split (test = our 15 plans; the rest 70 % `sft` / 30 % `exp`) |
| smoke | 3 training steps → merge → vLLM → score 2 plans |
| base_eval | untrained model on the test plans |
| sft | LoRA (rank 32, language model only) on ground-truth schematics of the `sft` plans, 2 epochs |
| exp_sample | the SFT model writes 8 schematics per `exp` plan, and `score.py` scores each. Per plan, the best one is kept if it beats that plan's mean. These rows are the model's own outputs, chosen by the reward, not copied from the ground truth. |
| exp_train | fine-tune the SFT model on its own best experience |
| sft_eval, exp_eval | the same test plans: greedy plus 2 samples each |

How it fits together:
- The policy writes the whole schematic in one reply, as compact JSON with 0..1000 coordinates (`blueprint_env/policy.py`).
- Converting ground truth to that text and back still scores 0.999, so the format loses almost nothing.
- `blueprint_env/train_grpo.py` is an optional GRPO variant that uses the same reward.
- `rollout.py` serves both as the evaluation and as the experience collector.

## Files

| file | what |
|---|---|
| `blueprint_env/env.py` | the episode: tools, budget, instructions, scoring at the end |
| `blueprint_env/mcp_server.py` | MCP (stdio) server for agent harnesses |
| `blueprint_env/score.py` | the reward |
| `blueprint_env/baselines.py` | do-nothing / stop-early / exploit checks |
| `blueprint_env/reference.py`, `cv.py` | scripted reference solver; the CV room segmentation used by the `segment_rooms` tool |
| `blueprint_env/agent.py` | Gemini runner (function calling over REST) using the same `Episode` |
| `blueprint_env/evaluate.py` | the one-command evaluation |
| `blueprint_env/gt.py`, `build_tasks.py` | DXF → ground truth, registration to the PNG, alignment check, area masking |
| `blueprint_env/policy.py`, `make_sft.py`, `train_sft.py`, `rollout.py`, `train_grpo.py` | fine-tuning a small model |
| `modal_app.py` | the training pipeline on Modal |
| `split.json` | fixed test split (never trained on) and excluded plans |

Rebuild the tasks from the dataset with `python -m blueprint_env.build_tasks <junction-dataset>/data/swiss_dwellings tasks --procs 8`.

## Credits

- Swiss Dwellings drawings: Archilyse AG, CC BY 4.0.
- `cv.segment_rooms`, the policy JSON repair in `policy.py`, and `train_sft.py` / `train_grpo.py` are adapted from github.com/AistisV/reinforcement-testing (MIT, © 2026 Aistis Verkauskas and the Junction 2026 team).
