# Break the Agent — by AfterQuery (Junction 2026: European Tech Renaissance)

The brief this repository answers, as published on the Junction 2026 hacker dashboard. Our answer to each judging criterion is in the table at the end.

## The challenge

Build a reinforcement learning environment that challenges today's best AI agents, demonstrate real failure modes, and show that its rewards reflect real progress.

### Introduction

Today's cutting-edge AI systems can solve Millennium Problems, discover new drugs, and create entire production apps with a few lines of prompting. But they still struggle in a wide variety of novel situations, ranging from everyday use cases to niche, highly technical workflows. We ask: what should AI agents be able to do that they still struggle with today?

At AfterQuery, we build environments for training and testing agents. The work starts with choosing a problem worth learning, defining an action and observation space, and defining a reward function that defines what success looks like. Getting those pieces right is a heavy research and engineering problem in itself.

For this challenge, we want to see your take on it. Build a world with something interesting to learn. Find out where strong agents struggle, and whether your reward actually encourages the behavior you intended.

### The task

Choose a setting you find interesting and build an environment an agent can interact with. It could be a game, a scientific simulation, a software task, a real-world process, or something we haven't thought of. Explain why you chose it and what an agent could learn there.

Your environment should have a clear goal, actions the agent can take, and a reward you can check. Run a frontier agent in it and compare the results with a stronger reference run your team can demonstrate and reproduce. We'll provide the agent harness and model credits.

Show where the agent falls short and why. The challenge should come from the decisions it needs to make, with access to the information and tools needed to succeed. We'll also try to find shortcuts that earn a high score without completing the task: reward hacking.

The setting and approach are yours to choose. We care about what makes the environment useful for learning and what your experiments reveal.

**Optional stretch goal:** train a smaller model using experience from your environment and show whether it improves.

## Judging rubric

| criterion | points | full points | zero points |
|---|---|---|---|
| The gap | 30 | The frontier agent consistently scores below a stronger reference run your team demonstrates; both results can be reproduced across repeated runs. | No measurable gap, or the claimed gap cannot be reproduced or checked against a demonstrated reference run. |
| Meaningful difficulty | 30 | You can explain the agent's main mistakes and connect them to decisions in the task; the information and tools needed to do better are available to it. | The gap comes from unfairly withheld information, trick wording, impossible timing, or broken tools. |
| Reward integrity | 25 | The reward measures success at the task and holds up when judges try to exploit it; doing nothing or stopping early earns little or no credit; completing the task well remains the best way to score. | An exploit, scoring loophole, or strategy that avoids the task earns a better score than successful play. |
| Craft | 15 | The environment's rules and behavior make sense for the setting; judges can run the evaluation from your README with one command and reproduce your reported results. | The environment only works in your demo, or judges cannot reproduce the evaluation. |

**How judging runs:** each team gets a 10-minute demo. The judges then rerun the evaluation with the standard harness:
- your reference run,
- three agent runs,
- a do-nothing baseline,
- a stop-early baseline.

They also spend 15 minutes looking for reward exploits. Scores are based on these runs.

**Tiebreaker:** if point totals are close, the judges favor a team that shows a smaller model improving after training on experience from its environment.

**Starting points** (prompts, not required features):
- planning several steps ahead
- exploring an unfamiliar system
- using tools
- managing limited resources
- adapting when new information arrives

A small environment with a well-chosen challenge can be enough. Think about what better play looks like, how you would measure it, and whether an agent could increase its score without getting better at the task.

## Resources provided

- An open-source agent harness, Harbor running the OpenCode agent, that connects to the environment over MCP.
- A scoring skeleton.
- Frontier model API credits per team.
- On-site mentors from AfterQuery's environments team (Daksh Raghuwanshi, Ved Vedere).
- A starter kit with the harness documentation and the judging rubric.

**Prizes:** €3,000 / €1,500 / €500 for the top three teams, plus a fast track to AfterQuery's work trial for the winners.

## How this repository answers each criterion

| criterion | where |
|---|---|
| The gap | `python -m blueprint_env.evaluate`: frontier agent (3 runs per plan) vs the CV reference solver on the same 15 test plans. See README → Results. |
| Meaningful difficulty | README → "Where the agent fails". Every tool the reference uses (`segment_rooms`, `measure_area`, zoom, preview) is also available to the agent. The scale is printed on every sheet. |
| Reward integrity | `blueprint_env/score.py` (one-to-one F1 matching for every class) and `blueprint_env/baselines.py` (do-nothing, stop-early, spam, giant room, duplicates, wrong scale, junk). Ground truth is alignment-checked. |
| Craft | One-command eval; MCP server for Harbor/OpenCode (`blueprint_env/mcp_server.py`); deterministic reference; all runs saved under `runs/`. |
| Stretch goal | `modal_app.py`: Qwen3-VL fine-tuning on ground truth, then on its own best-scoring samples (experience from the environment). |
