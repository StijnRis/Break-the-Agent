# AfterQuery organizer update

Saved from the organizer's message for the Break the Agent challenge.

## Required submission format

- Use Harbor; each environment is a task containing `instruction.md`, `task.toml`, `environment/Dockerfile`, `tests/`, and `solution/`.
- Use OpenCode with Harbor where possible, for example `harbor run -p ./my-task -a opencode -m [provider/model]`.
- The verifier writes one score from 0 to 1 to `/logs/verifier/reward.txt`; partial credit is welcome.

## Before submitting

- Include at least one Harbor run log with its score showing an agent playing the environment. Playthroughs are encouraged in the demo video.
- Include a short README explaining the agent's objective, why it is difficult, and how scoring works.
- Submit by the challenge deadline.

## Credits and judging interests

- AfterQuery cannot provide inference credits; use credits provided by Google, OpenAI, or Modal.
- The organizers are interested in simulations, environments, and post-training experiments.
- The challenge is research-heavy and expects participants to learn relevant RL concepts.

## Implementation in this repository

The Harbor package in `harbor_task/` uses a separate verifier container so surveyed ground truth is not available in the agent's environment. It writes the continuous score from the existing scorer to Harbor's required reward file. An OpenCode/Gemini Harbor playthrough scored 0.6159; logs, the verified reward, and a source-versus-submission comparison visual are summarized in `results/harbor_run.md`.
