"""LoRA fine-tuning of a vision-language model on rows from make_sft.py (ground truth) or rollout.py
--save-best (the model's own best-scoring samples = experience from the environment), then merge the
adapter so vLLM can serve the result.

    python -m blueprint_env.train_sft --data rows.jsonl --model Qwen/Qwen3-VL-8B-Instruct --out ckpt/sft --epochs 2

Writes <out>/ (adapter + checkpoints, resumes if interrupted) and <out>-merged/ (with a DONE marker).
Adapted from train_sft.py in github.com/AistisV/reinforcement-testing (MIT, (c) 2026 Aistis Verkauskas
and the Junction 2026 team).
"""
import argparse
import glob
import json
import os
import shutil

import torch
from peft import LoraConfig, get_peft_model
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor, Trainer, TrainingArguments

from .policy import model_image

ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True)
ap.add_argument("--model", default="Qwen/Qwen3-VL-8B-Instruct")
ap.add_argument("--out", required=True)
ap.add_argument("--epochs", type=float, default=2)
ap.add_argument("--max-steps", type=int, default=-1)
ap.add_argument("--accum", type=int, default=8)
ap.add_argument("--lr", type=float, default=1e-4)
ap.add_argument("--rank", type=int, default=32)
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--save-steps", type=int, default=40)
ap.add_argument("--cpu", action="store_true", help="tiny-model test on CPU")
a = ap.parse_args()

merged_dir = a.out.rstrip("/") + "-merged"
if os.path.exists(os.path.join(merged_dir, "DONE")):
    print("already trained and merged:", merged_dir); raise SystemExit(0)

proc = AutoProcessor.from_pretrained(a.model)
tok = proc.tokenizer
rows = [json.loads(l) for l in open(a.data, encoding="utf-8") if l.strip()]
rows = [r for r in rows if os.path.exists(r["image"])]
if a.limit:
    rows = rows[:a.limit]
print(len(rows), "training rows", flush=True)
assert rows, "no training rows"
ASSIST = tok.encode("<|im_start|>assistant\n", add_special_tokens=False)


class Rows(torch.utils.data.Dataset):
    def __len__(self): return len(rows)
    def __getitem__(self, i): return rows[i]


def collate(batch):
    r = batch[0]                                   # batch size is always 1
    img = model_image(Image.open(r["image"]))
    text = proc.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=False)
    enc = proc(text=[text], images=[img], return_tensors="pt")
    ids = enc["input_ids"][0]
    labels = ids.clone()
    L, n, start = ids.tolist(), len(ASSIST), -1
    for k in range(len(L) - n, -1, -1):            # train only on the assistant reply
        if L[k:k + n] == ASSIST:
            start = k + n; break
    if start > 0:
        labels[:start] = -100
    out = dict(enc)
    out["labels"] = labels.unsqueeze(0)
    return out


dt = torch.float32 if a.cpu else torch.bfloat16
try:
    model = AutoModelForImageTextToText.from_pretrained(a.model, dtype=dt)
except TypeError:
    model = AutoModelForImageTextToText.from_pretrained(a.model, torch_dtype=dt)
model = model.to(dt)
model.config.use_cache = False
try:
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
except Exception as e:
    print("WARNING: gradient checkpointing not enabled:", repr(e))
model.enable_input_require_grads()

TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
try:   # language model only; the vision encoder stays frozen
    model = get_peft_model(model, LoraConfig(r=a.rank, lora_alpha=2 * a.rank, lora_dropout=0.05, bias="none",
                                             target_modules=r".*language_model.*\.(" + "|".join(TARGETS) + ")"))
except Exception as e:
    print("regex target failed, using module names:", repr(e))
    model = get_peft_model(model, LoraConfig(r=a.rank, lora_alpha=2 * a.rank, lora_dropout=0.05, bias="none", target_modules=TARGETS))
model.print_trainable_parameters()

args = TrainingArguments(output_dir=a.out, num_train_epochs=a.epochs, max_steps=a.max_steps, per_device_train_batch_size=1,
                         gradient_accumulation_steps=a.accum, learning_rate=a.lr, lr_scheduler_type="cosine", warmup_steps=5,
                         bf16=not a.cpu, logging_steps=5, save_strategy="steps", save_steps=a.save_steps, save_total_limit=2,
                         report_to="none", remove_unused_columns=False, dataloader_num_workers=0,
                         label_names=["labels"], use_cpu=a.cpu)
trainer = Trainer(model=model, args=args, train_dataset=Rows(), data_collator=collate)
ckpts = sorted(glob.glob(os.path.join(a.out, "checkpoint-*")), key=lambda p: int(p.rsplit("-", 1)[1]))
try:
    trainer.train(resume_from_checkpoint=ckpts[-1] if ckpts else None)
except Exception as e:
    if not ckpts:
        raise
    print("resume failed, training from the start:", repr(e), flush=True)
    trainer.train()
model.save_pretrained(a.out)
print("adapter saved, merging...", flush=True)

merged = model.merge_and_unload()
merged.config.use_cache = True
if os.path.isdir(merged_dir):
    shutil.rmtree(merged_dir)
merged.save_pretrained(merged_dir, max_shard_size="5GB")
proc.save_pretrained(merged_dir)
try:  # config / chat-template files of the base that save_pretrained does not write
    if os.path.isdir(a.model):
        src = a.model
    else:
        from huggingface_hub import snapshot_download
        src = snapshot_download(a.model, allow_patterns=["*.json", "*.jinja", "*.txt"])
    for f in os.listdir(src):
        p = os.path.join(src, f)
        if os.path.isfile(p) and not f.endswith((".safetensors", ".bin")) and f != "DONE" and not os.path.exists(os.path.join(merged_dir, f)):
            shutil.copy(p, os.path.join(merged_dir, f))
except Exception as e:
    print("WARNING: could not copy extra base files:", repr(e))
open(os.path.join(merged_dir, "DONE"), "w").write("ok")
print("merged model saved:", merged_dir, flush=True)
