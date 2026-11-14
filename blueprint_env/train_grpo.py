"""Optional: GRPO with the environment reward (score.py), starting from the SFT model.
Not part of the default Modal pipeline (rejection sampling in modal_app.py is the tested path).

    python -m blueprint_env.train_grpo --model /vol/ckpt/sft-merged --root /vol/tasks --plans /vol/plans.json --key exp

For each plan the model writes --gens schematics; each is scored by score.py and compared with the group
mean, so above-average schematics are reinforced. The reward's exploit resistance (baselines.py) is what
makes this safe: spam, duplicates and do-nothing all score low.
Adapted from train_grpo.py in github.com/AistisV/reinforcement-testing (MIT, (c) 2026 Aistis Verkauskas
and the Junction 2026 team).
"""
import argparse
import json
import os

from datasets import Dataset
from peft import LoraConfig
from PIL import Image
from trl import GRPOConfig, GRPOTrainer

from .make_sft import test_plans
from .policy import from_text, model_image, prompt_for
from .score import score

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--root", default="tasks")
ap.add_argument("--plans", required=True); ap.add_argument("--key", default="exp")
ap.add_argument("--out", default="ckpt/grpo")
ap.add_argument("--steps", type=int, default=150)
ap.add_argument("--gens", type=int, default=4)
ap.add_argument("--max-completion", type=int, default=8192)
ap.add_argument("--lr", type=float, default=5e-6)
a = ap.parse_args()

test = test_plans()
plans = [p for p in json.load(open(a.plans))[a.key] if p not in test]
GT, SIZE, rows = {}, {}, []
for p in plans:
    td = os.path.join(a.root, p)
    img = Image.open(os.path.join(td, "drawing.png")).convert("RGB")
    GT[p] = json.load(open(os.path.join(td, "ground_truth.json"), encoding="utf8")); SIZE[p] = img.size
    rows.append({"plan": p, "image": model_image(img),
                 "prompt": [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt_for(*img.size)}]}]})
print(len(rows), "plans")


def env_reward(completions, plan, **kw):
    out = []
    for c, p in zip(completions, plan):
        text = c[0]["content"] if isinstance(c, list) else c
        try:
            out.append(float(score(GT[p], from_text(text, *SIZE[p]), SIZE[p])["reward"]))
        except Exception:
            out.append(0.0)
    return out


cfg = GRPOConfig(output_dir=a.out, max_steps=a.steps, learning_rate=a.lr, per_device_train_batch_size=a.gens,
                 gradient_accumulation_steps=2, num_generations=a.gens, max_completion_length=a.max_completion,
                 temperature=1.0, beta=0.0, bf16=True, gradient_checkpointing=True, logging_steps=1, save_steps=25,
                 report_to="none", use_vllm=True, vllm_mode="colocate", vllm_gpu_memory_utilization=0.35)
peft = LoraConfig(r=64, lora_alpha=128, lora_dropout=0.0, task_type="CAUSAL_LM",
                  target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
trainer = GRPOTrainer(model=a.model, reward_funcs=[env_reward], args=cfg, train_dataset=Dataset.from_list(rows), peft_config=peft)
trainer.train()
trainer.save_model(a.out)
print("saved", a.out)
