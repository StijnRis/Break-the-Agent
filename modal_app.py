"""Fine-tune a small vision-language model on experience from the environment, on Modal GPUs.

    modal run --detach modal_app.py                    # whole pipeline (finished stages are skipped)
    modal run --detach modal_app.py --stages smoke     # only the 5-minute end-to-end smoke test
    modal run modal_app.py --stages status             # which stages are done + their summaries
    modal volume get blueprint-vol runs/ .             # copy the policy runs into ./runs, then:
    python -m blueprint_env.evaluate                   # the table now includes the trained model's rows

Stages (each writes /vol/done/<stage> when finished):
  fetch       full Junction dataset -> volume (Swiss Dwellings DXF + PNG)
  build       ground truth for every plan (blueprint_env.build_tasks), alignment-checked
  plans       fixed split of the valid plans: test = split.json test; the rest 70 % 'sft' / 30 % 'exp'
  smoke       3 training steps -> merge -> serve -> score 2 plans (catches crashes before the long run)
  base_eval   untrained model on the test plans (greedy + 2 samples)
  sft         LoRA fine-tuning on ground-truth schematics of the 'sft' plans (format + symbols)
  sft_eval    same test plans
  exp_sample  SFT model writes 8 schematics for each 'exp' plan; the environment scores them; per plan the
              best one is kept if it beats that plan's average -> experience rows (no ground truth in the targets)
  exp_train   fine-tune the SFT model on its own best experience
  exp_eval    same test plans
"""
import hashlib
import json
import os
import shutil
import signal
import subprocess
import time

import modal

HERE = os.path.dirname(os.path.abspath(__file__))
# A 2B checkpoint is intentional: this experiment is meant to demonstrate
# improvement from the environment, not to maximize raw model size or cost.
# Both values remain environment overrides for a larger follow-up experiment.
APP = "blueprint-schematic-small"
BASE = os.environ.get("BASE_MODEL", "Qwen/Qwen3-VL-2B-Instruct")
TAG = os.environ.get("MODEL_TAG", "qwen3vl-2b")
DATA_URL = "https://fwjydgxpttajiqpfmqtj.supabase.co/storage/v1/object/public/stoa-junction-2026/junction-dataset.zip"
SRC, TASKS, PLANS, CKPT, RUNS = "/vol/data/swiss_dwellings", "/vol/tasks", "/vol/plans.json", "/vol/ckpt", "/vol/runs"

image = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu22.04", add_python="3.11")
    .apt_install("wget", "unzip", "curl", "libgl1", "libglib2.0-0")
    .pip_install("vllm", "openai", "pillow", "shapely", "opencv-python-headless", "scikit-image", "scipy", "numpy",
                 "ezdxf", "requests", "rapidocr-onnxruntime", "trl", "peft", "accelerate", "datasets", "qwen-vl-utils")
    .env({"HF_HOME": "/vol/hf", "TOKENIZERS_PARALLELISM": "false", "PYTHONUNBUFFERED": "1"})
    .add_local_dir(os.path.join(HERE, "blueprint_env"), "/code/blueprint_env", ignore=["__pycache__"])
    .add_local_file(os.path.join(HERE, "split.json"), "/code/split.json")
)
vol = modal.Volume.from_name("blueprint-vol", create_if_missing=True)
app = modal.App(APP, image=image)
# Qwen3-VL-2B plus LoRA fits comfortably on a 24 GB L4.  This keeps the
# learning demonstration affordable; override this only for a larger model.
GPU = dict(gpu="L4", volumes={"/vol": vol}, cpu=8, memory=65536, timeout=10 * 3600)
CPU = dict(volumes={"/vol": vol}, cpu=16, memory=32768, timeout=4 * 3600)


def sh(cmd):
    print("$", cmd, flush=True)
    p = subprocess.Popen(cmd, shell=True, cwd="/code", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    lines = []
    for line in p.stdout:
        print(line, end="", flush=True); lines.append(line)
    if p.wait():
        raise RuntimeError(f"failed ({p.returncode}): {cmd}\n" + "".join(lines[-30:]))
    return "".join(lines)


def done(stage, summary=None):
    os.makedirs("/vol/done", exist_ok=True)
    if summary is None:
        return os.path.exists(f"/vol/done/{stage}")
    open(f"/vol/done/{stage}", "w").write(summary)
    vol.commit()


class vllm:
    """Serve a model with vLLM for the duration of a with-block."""
    def __init__(self, model): self.model = model
    def __enter__(self):
        self.p = subprocess.Popen(["vllm", "serve", self.model, "--served-model-name", "policy", "--max-model-len", "32768",
                                   "--limit-mm-per-prompt", '{"image":1}', "--gpu-memory-utilization", "0.88"],
                                  stdout=open("/tmp/vllm.log", "w"), stderr=subprocess.STDOUT, start_new_session=True)
        for i in range(240):
            if self.p.poll() is not None:
                break
            if subprocess.run("curl -sf localhost:8000/v1/models > /dev/null", shell=True).returncode == 0:
                print(f"vLLM up after {i * 10}s", flush=True); return self
            time.sleep(10)
        raise RuntimeError("vLLM failed:\n" + open("/tmp/vllm.log", errors="replace").read()[-3000:])
    def __exit__(self, *a):
        try: os.killpg(self.p.pid, signal.SIGTERM); self.p.wait(60)
        except Exception:
            try: os.killpg(self.p.pid, signal.SIGKILL)
            except Exception: pass


def rollout(tag, key, extra=""):
    return sh(f"python -m blueprint_env.rollout --root {TASKS} --plans {PLANS} --key {key} --tag {tag} --runs-dir {RUNS} {extra}")


# ---------------------------------------------------------------- stages
@app.function(**CPU)
def fetch():
    import glob, zipfile
    if len(glob.glob(SRC + "/*.dxf")) > 500:
        return f"already there: {len(glob.glob(SRC + '/*.dxf'))} DXF"
    os.makedirs(SRC, exist_ok=True)
    z = "/vol/data/junction-dataset.zip"
    sh(f"wget -q -c '{DATA_URL}' -O {z} || wget -q '{DATA_URL}' -O {z}")
    n = 0
    with zipfile.ZipFile(z) as zf:
        for name in zf.namelist():
            base = os.path.basename(name)
            if base and "/swiss_dwellings/" in "/" + name and base.endswith((".dxf", ".png")):
                with zf.open(name) as s, open(os.path.join(SRC, base), "wb") as d:
                    shutil.copyfileobj(s, d, 1 << 20)
                n += 1
    os.remove(z)
    vol.commit()
    return f"extracted {n} files"


@app.function(**CPU)
def build():
    out = sh(f"python -m blueprint_env.build_tasks {SRC} {TASKS} --procs 16 | tail -5")
    vol.commit()
    idx = json.load(open(f"{TASKS}/index.json"))
    ok = [r for r in idx if r.get("valid") and "error" not in r]
    return f"{len(idx)} plans, {len(ok)} valid\n" + out[-500:]


@app.function(**CPU)
def plans():
    import sys; sys.path.insert(0, "/code")
    from blueprint_env.build_tasks import valid_tasks
    test = json.load(open("/code/split.json"))["test"]
    ok = [t for t in valid_tasks(TASKS) if t not in test]
    h = lambda t: int(hashlib.md5(t.encode()).hexdigest(), 16) % 10
    split = {"test": [t for t in test if os.path.exists(f"{TASKS}/{t}/drawing.png")],
             "sft": [t for t in ok if h(t) < 7], "exp": [t for t in ok if h(t) >= 7]}
    json.dump(split, open(PLANS, "w"), indent=1)
    vol.commit()
    return json.dumps({k: len(v) for k, v in split.items()})


@app.function(**GPU)
def smoke():
    for d in (f"{CKPT}/smoke", f"{CKPT}/smoke-merged"):
        shutil.rmtree(d, ignore_errors=True)
    sh(f"python -m blueprint_env.make_sft --root {TASKS} --plans {PLANS} --key sft --limit 3 --out /tmp/smoke.jsonl")
    sh(f"python -m blueprint_env.train_sft --data /tmp/smoke.jsonl --model {BASE} --out {CKPT}/smoke --max-steps 3 --accum 1 --save-steps 100")
    with vllm(f"{CKPT}/smoke-merged"):
        txt = rollout("smoke", "test", "--limit 2 --greedy --max-tokens 2000")
    shutil.rmtree(f"{RUNS}/smoke", ignore_errors=True)
    for d in (f"{CKPT}/smoke", f"{CKPT}/smoke-merged"):
        shutil.rmtree(d, ignore_errors=True)
    vol.commit()
    return "train + merge + serve + score ran\n" + txt[-600:]


@app.function(**GPU)
def evaluate(model: str, tag: str):
    with vllm(model):
        txt = rollout(tag, "test", "--greedy --samples 2 --temperature 0.7")
    vol.commit()
    return txt[txt.rfind("==="):]


@app.function(**GPU)
def sft():
    sh(f"python -m blueprint_env.make_sft --root {TASKS} --plans {PLANS} --key sft --out /vol/sft.jsonl")
    out = sh(f"python -m blueprint_env.train_sft --data /vol/sft.jsonl --model {BASE} --out {CKPT}/sft --epochs 2")
    vol.commit()
    return out[-600:]


@app.function(**GPU)
def exp_sample():
    with vllm(f"{CKPT}/sft-merged"):
        txt = rollout(f"{TAG}-exp-samples", "exp", "--samples 8 --temperature 0.9 --save-best /vol/exp_rows.jsonl")
    vol.commit()
    return txt[-600:]


@app.function(**GPU)
def exp_train():
    out = sh(f"python -m blueprint_env.train_sft --data /vol/exp_rows.jsonl --model {CKPT}/sft-merged --out {CKPT}/exp "
             f"--epochs 1 --lr 3e-5")
    vol.commit()
    return out[-600:]


@app.function(volumes={"/vol": vol}, timeout=3600)
def status():
    vol.reload()
    if not os.path.isdir("/vol/done"):
        return "nothing done yet"
    return "\n\n".join(f"[{s}]\n{open('/vol/done/' + s).read()[-800:]}" for s in sorted(os.listdir("/vol/done")))


STAGES = {
    "fetch": lambda: fetch.remote(),
    "build": lambda: build.remote(),
    "plans": lambda: plans.remote(),
    "smoke": lambda: smoke.remote(),
    "base_eval": lambda: evaluate.remote(BASE, f"{TAG}-base"),
    "sft": lambda: sft.remote(),
    "sft_eval": lambda: evaluate.remote(f"{CKPT}/sft-merged", f"{TAG}-sft"),
    "exp_sample": lambda: exp_sample.remote(),
    "exp_train": lambda: exp_train.remote(),
    "exp_eval": lambda: evaluate.remote(f"{CKPT}/exp-merged", f"{TAG}-sft-exp"),
}


@app.function(volumes={"/vol": vol}, timeout=24 * 3600)
def pipeline(stages: str = "all", force: bool = False):
    names = list(STAGES) if stages == "all" else stages.split(",")
    for s in names:
        vol.reload()
        if done(s) and not force:
            print(f"== {s}: already done", flush=True); continue
        print(f"== {s}: running", flush=True)
        t0 = time.time()
        out = STAGES[s]()
        vol.reload()
        done(s, f"{out}\n({(time.time() - t0) / 60:.0f} min)")
        print(f"== {s}: done in {(time.time() - t0) / 60:.0f} min\n{out}", flush=True)
    return "ALL DONE"


@app.local_entrypoint()
def main(stages: str = "all", force: bool = False):
    if stages == "status":
        print(status.remote()); return
    print(pipeline.remote(stages, force))
