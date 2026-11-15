Test split: 15 plans. Reward in [0, 1]; mean over plans and runs.

| run | episodes | reward | sd over runs | walls | rooms | doors | windows | fixtures | areas | speed |
|---|---|---|---|---|---|---|---|---|---|---|
| ceiling (ground-truth replay) | 15 | **1.000** | 0.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| reference + YOLO detector (external weights, train/test overlap unverified) | 8 | **0.800** | 0.000 | 0.89 | 0.63 | 0.86 | 0.97 | 0.94 | 0.51 | 1.00 |
| reference (CV solver, no ground truth) | 15 | **0.628** | 0.000 | 0.92 | 0.64 | 0.59 | 0.51 | 0.17 | 0.56 | 1.00 |
| stop early (50 %) | 15 | **0.468** | 0.000 | 0.85 | 0.40 | 0.47 | 0.32 | 0.10 | 0.27 | 1.00 |
| agent: gemini-3.1-pro-preview | 45 | **0.393** | 0.009 | 0.28 | 0.54 | 0.39 | 0.40 | 0.51 | 0.31 | 0.65 |
| stop early (25 %) | 15 | **0.302** | 0.000 | 0.64 | 0.24 | 0.26 | 0.18 | 0.03 | 0.14 | 1.00 |
| agent: gemini-3.1-pro-parallel-20261114-batch2 | 4 | **0.182** | 0.000 | 0.29 | 0.26 | 0.06 | 0.04 | 0.11 | 0.18 | 1.00 |
| agent: stop-early-gemini-3-flash-4calls | 15 | **0.181** | 0.000 | 0.29 | 0.18 | 0.11 | 0.13 | 0.17 | 0.08 | 1.00 |
| agent: gemini-3.1-pro-parallel-20261114 | 4 | **0.035** | 0.000 | 0.00 | 0.13 | 0.00 | 0.00 | 0.00 | 0.03 | 1.00 |
| do nothing | 15 | **0.000** | 0.000 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 |

Exploit attempts (mean reward):

- scale only: 0.000
- wall = whole building box: 0.139
- one giant room: 0.000
- door/window/fixture spam (961 each): 0.012
- grid of rooms over the building (as many cells as rooms): 0.003
- thick ring wall around the building: 0.097
- every fixture type stacked on every true fixture: 0.033
- true room outlines, every name set to the most common label: 0.914
- rooms duplicated x3: 0.875
- right geometry, scale x1.3: 0.900
- malformed junk: 0.000
