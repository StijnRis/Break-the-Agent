# Harbor run: Blueprint schematic

**Reward: 0.6159 / 1.0**

- Harbor: 0.26.0
- Harness: OpenCode
- Model: `google/gemini-3.1-pro-preview`
- Task: `afterquery/blueprint-schematic-site279` (`site279_bldg514_floor2041`)
- Verifier: passed; wrote `0.615900` to Harbor's `reward.txt`

The agent submitted 88 walls, 20 rooms, 23 doors, 12 fixtures, and no windows. It used the calibrated scale `0.01693333` m/px. The prebuilt OpenCode image was detected during setup, so the trial skipped the usual OpenCode installation. Harbor completed without an agent or verifier error.

The verifier automatically writes a comparison image after every run. It shows the public source drawing beside the submitted geometry overlay; it never contains surveyed ground truth.

## Run artifacts

- Harbor summary: [`result.json`](../jobs/blueprint-harbor-cached/harbor_task__iW5q6LC/result.json)
- Verifier reward: [`reward.txt`](../jobs/blueprint-harbor-cached/harbor_task__iW5q6LC/verifier/reward.txt)
- Comparison visual: [`comparison.png`](../jobs/blueprint-harbor-cached/harbor_task__iW5q6LC/verifier/comparison.png)
- Error diagnostic: [`errors.png`](../jobs/blueprint-harbor-cached/harbor_task__iW5q6LC/verifier/errors.png)
- Three-panel review: [`review.png`](../jobs/blueprint-harbor-cached/harbor_task__iW5q6LC/verifier/review.png)
- Agent trajectory: [`trajectory.json`](../jobs/blueprint-harbor-cached/harbor_task__iW5q6LC/agent/trajectory.json)
- OpenCode log: [`opencode.txt`](../jobs/blueprint-harbor-cached/harbor_task__iW5q6LC/agent/opencode.txt)
- Submitted schematic: [`answer.json`](../jobs/blueprint-harbor-cached/harbor_task__iW5q6LC/artifacts/tmp/answer.json)
