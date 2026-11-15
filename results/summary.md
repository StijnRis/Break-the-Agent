Test split: 15 plans. Reward in [0, 1]; mean over plans and runs.

| run | episodes | reward | sd over runs | walls | rooms | doors | windows | fixtures | areas | speed |
|---|---|---|---|---|---|---|---|---|---|---|
| ceiling (ground-truth replay) | 15 | **1.000** | 0.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| reference (CV solver, no ground truth) | 15 | **0.586** | 0.000 | 0.89 | 0.64 | 0.56 | 0.49 | 0.09 | 0.37 | 1.00 |
| stop early (50 %) | 15 | **0.438** | 0.000 | 0.81 | 0.40 | 0.45 | 0.31 | 0.05 | 0.17 | 1.00 |
| agent: gemini-3.1-pro-preview | 45 | **0.342** | 0.010 | 0.24 | 0.54 | 0.34 | 0.34 | 0.42 | 0.13 | 0.65 |
| stop early (25 %) | 15 | **0.283** | 0.000 | 0.60 | 0.24 | 0.24 | 0.18 | 0.01 | 0.09 | 1.00 |
| agent: gemini-3.1-pro-parallel-20261114-batch2 | 4 | **0.150** | 0.000 | 0.22 | 0.26 | 0.02 | 0.03 | 0.09 | 0.13 | 1.00 |
| agent: stop-early-gemini-3-flash-4calls | 15 | **0.141** | 0.000 | 0.23 | 0.18 | 0.06 | 0.10 | 0.09 | 0.04 | 1.00 |
| agent: gemini-3.1-pro-parallel-20261114 | 4 | **0.032** | 0.000 | 0.00 | 0.13 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 |
| do nothing | 15 | **0.000** | 0.000 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 |

Exploit attempts (mean reward):

- scale only: 0.000
- wall = whole building box: 0.094
- one giant room: 0.000
- door/window/fixture spam (961 each): 0.011
- grid of rooms over the building (as many cells as rooms): 0.002
- thick ring wall around the building: 0.073
- every fixture type stacked on every true fixture: 0.033
- true room outlines, every name set to the most common label: 0.914
- rooms duplicated x3: 0.875
- right geometry, scale x1.3: 0.900
- malformed junk: 0.000
