# Small-model learning experiment

This project has two independent responsibilities:

- **Harbor on Modal** runs the submitted task in an isolated environment, exposes the MCP tools, and obtains the verifier reward.
- **Modal training** fine-tunes a 2B vision-language model on an H100 (set `GPU=L4` for a cheaper, slower run) and uses the same environment reward to select its own useful experience.

Keeping these separate is deliberate. Harbor is the task runner and verifier; it is not a model optimizer. This makes the result easier to reproduce and avoids claiming that an autonomous OpenCode run is training the small model.

## Run order

Before the first Harbor-on-Modal run, install Harbor's optional Modal support once:

```powershell
uv pip install --python .\.uv-tools\harbor\Scripts\python.exe modal dockerfile-parse
```

1. Confirm the packaged Harbor task works on Modal:

   ```powershell
   .\.uv-tools\harbor\Scripts\harbor.exe run -c harbor_modal.json --env-file .env
   ```

   This is a single Harbor playthrough. It saves the trajectory and the verifier reward under `jobs/`.

On Windows, set `$env:PYTHONUTF8=1` first; the Modal CLI otherwise crashes printing its progress symbols.

2. Validate the small-model pipeline before paying for the full experiment:

   ```powershell
   modal run --detach modal_app.py --stages fetch,build,plans,smoke
   modal run modal_app.py --stages status
   ```

3. Train and measure learning:

   ```powershell
   modal run --detach modal_app.py --stages base_eval,sft,sft_eval,exp_sample,exp_train,exp_eval
   ```

4. Retrieve and summarize held-out results:

   ```powershell
   modal volume get blueprint-vol runs/ .
   python -m blueprint_env.evaluate
   ```

The 15 plans in `split.json` under `test` are never used in either supervised training or reward-selected experience. The final comparison is therefore between the untrained 2B base model, the ground-truth fine-tuned model, and the model fine-tuned on its own reward-selected attempts.

## Speed settings

- GPU: H100 by default (`GPU=L4` for the cheapest, slowest run).
- `base_eval` runs in its own container in parallel with `sft`.
- Evaluation is greedy only (one episode per test plan).
- `sft` trains 1 epoch on floors whose target schematic is at most 8,000 characters.
- `exp_sample` writes 4 samples per plan, split over `EXP_SHARDS` (default 4) GPU containers.
- The model sees the drawing at most 1536 px on its long side (`MODEL_MAX_SIDE` in `blueprint_env/policy.py`).

## What demonstrates learning

The evidence is the change in mean reward on the unchanged test split:

`qwen3vl-2b-base` -> `qwen3vl-2b-sft` -> `qwen3vl-2b-sft-exp`.

The final stage only learns from model-generated schematics that the environment scored better than the average sample for their plan. It does not copy the ground-truth target into those experience rows.
