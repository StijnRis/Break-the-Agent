"""Audio for the demo video: level every source to the same loudness, add synthesized sound effects, mix."""
from __future__ import annotations

import json
import re
import subprocess
import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

HERE = Path(__file__).resolve().parent
SR = 44100
TARGET_LUFS = -16.0


def run(*a: str, **kw):
    return subprocess.run(a, check=True, capture_output=True, text=True, **kw)


def normalize(src: Path, dst: Path, compress: bool = False) -> None:
    """level a source to -16 LUFS. The phone clip (very dynamic, quiet) gets a compressor + dynamic loudnorm; clean voiceovers get linear two-pass loudnorm."""
    if compress:
        af = ("highpass=f=70,acompressor=threshold=0.03:ratio=6:attack=5:release=200:makeup=6,"
              f"loudnorm=I={TARGET_LUFS + 0.5}:TP=-1.0:LRA=4,volume=3.5dB,alimiter=limit=0.95")
        run("ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vn", "-ar", str(SR), "-ac", "1", "-af", af, str(dst))
        return
    p1 = subprocess.run(["ffmpeg", "-nostats", "-i", str(src), "-vn", "-af", f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=7:print_format=json", "-f", "null", "-"],
                        capture_output=True, text=True)
    st = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p1.stderr, re.S).group(0))
    af = (f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=7:measured_I={st['input_i']}:measured_TP={st['input_tp']}:"
          f"measured_LRA={st['input_lra']}:measured_thresh={st['input_thresh']}:offset={st['target_offset']}:linear=true")
    run("ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vn", "-ar", str(SR), "-ac", "1", "-af", af, str(dst))


def read_wav(p: Path) -> np.ndarray:
    with wave.open(str(p)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() > 1:
            x = x.reshape(-1, w.getnchannels()).mean(axis=1)
    return x


def tick_run(start: float, n: int, step: float, name: str = "tick") -> list[tuple[float, str]]:
    return [(start + i * step, name) for i in range(n)]


def sfx_events(w: dict[str, float]) -> dict[str, list[tuple[float, str]]]:
    """(seconds inside the scene, effect). Scenes that are sped up (warp) divide their animation times by the warp."""
    d, rp, en = w.get("demo", 1), w.get("repro", 1), w.get("end", 1)
    return {
        "intro": [(0.45, "swoosh"), (13.8, "whoosh"), (17.4, "shutter"), (17.5, "pop"), *tick_run(18.0, 27, 0.06), (22.7, "pop"),
                  (25.3, "pop"), (25.45, "pop"), (26.4, "thud"), (26.45, "buzz"), (26.6, "pop"), (30.5, "swoosh")],
        "measure": [(0.6, "swoosh"), *tick_run(1.2, 11, 0.07), (2.1, "scan"), *tick_run(2.1, 23, 0.055), (5.0, "scratch"), (5.5, "swoosh"),
                    (6.15, "pop"), (6.5, "pop"), (6.75, "pop"), (7.05, "whoosh"), (7.6, "swell"), (8.4, "ding")],
        "rubric": [(0.0, "swoosh"), *[(t, "pop") for t in (0.1, 0.5, 2.1, 2.5, 4.1, 4.5)], (5.2, "pop")],
        "machine": [(0.7, "pop"), (2.2, "swoosh"), *[(2.8 + 0.2 * i, "pop") for i in range(8)], (4.95, "slash"), (5.85, "slash"), (6.45, "slash"), (6.8, "ding")],
        "demo": [(0.0, "swoosh"), *[((1.0 + i * 0.95) / d, "tick") for i in range(14)], (3.0 / d, "swoosh"), (15.8 / d, "swoosh"), (21.0 / d, "ding"), (22.6 / d, "ding")],
        "gap": [(0.3, "swoosh"), (1.8, "swell"), (2.5, "swell"), (3.2, "swell"), (2.9, "ding")],
        "errors": [(2.2, "pop"), (3.9, "buzz"), (3.4, "pop"), (4.3, "swell"), *[(5.0 + 0.45 * i, "pop") for i in range(6)], (7.3, "buzz")],
        "cheat": [*[(0.3 + i * 0.35, "pop") for i in range(6)], *[(0.65 + i * 0.35, "tick") for i in range(6)], (3.6, "ding")],
        "repro": [*[(t / rp, "tick") for t in np.arange(0.9, 2.5, 0.1)], (3.2 / rp, "tick"), *[(t / rp, "tick") for t in np.arange(4.2, 5.0, 0.1)], (5.0 / rp, "ding"), *[(t / rp, "tick") for t in np.arange(6.0, 7.1, 0.1)]],
        "train": [(1.3, "pop"), (1.3, "scan"), (4.4, "ding")],
        "stoa": [(0.7, "swoosh"), (2.0, "pop"), *tick_run(2.1, 23, 0.045), (3.7, "pop"), (3.8, "swoosh"), (4.5, "ding")],
        "end": [(0.6 / en, "swoosh"), (2.4 / en, "swoosh"), (5.8 / en, "whoosh"), *[(7.0 / en + i * 0.05, "tick") for i in range(0)]],
    }


def build(scenes: list[dict], total: float, work: Path) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    n = int(total * SR)
    voice = np.zeros(n, dtype=np.float32)
    # 1) voiceovers and the phone clip, all normalized to the same loudness
    for s in scenes:
        srcs = []
        vo = HERE / "media" / "vo" / f"{s['id']}.mp3"
        if not s["noTTS"] and vo.exists():
            srcs.append((vo, False))
        if s["clip"] and s["clipAudio"] and (HERE / "media" / s["clip"]).exists():
            srcs.append((HERE / "media" / s["clip"], True))
        for path, comp in srcs:
            out = work / f"{s['id']}_{path.stem}.wav"
            normalize(path, out, compress=comp)
            x = read_wav(out)[: int(s["dur"] * SR)].copy()
            fi, fo = int(0.02 * SR), int(0.12 * SR)
            x[:fi] *= np.linspace(0, 1, fi); x[-fo:] *= np.linspace(1, 0, fo)
            i = int(s["start"] * SR)
            voice[i:i + len(x)] += x[: n - i]
    # 2) synthesized sound effects (quiet, under the voice)
    sfx = np.zeros(n, dtype=np.float32)
    cache = {p.stem: read_wav(p) for p in (HERE / "media" / "sfx").glob("*.wav")}
    warps = {s["id"]: s.get("warp") or 1 for s in scenes}
    ev = resolve(sfx_events(warps))
    gains = GAINS
    for s in scenes:
        for t, name in ev.get(s["id"], []):
            if name not in cache or t >= s["dur"]:
                continue
            x = cache[name] * gains.get(name, 0.3)
            i = int((s["start"] + t) * SR)
            sfx[i:i + len(x)] += x[: n - i]
    mix = voice + sfx * 0.55 + ambient_bed(total)
    mix = np.clip(mix, -0.98, 0.98)
    out = work / "mix.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    return out


GAINS = {"tap": 0.5, "key1": 0.2, "key2": 0.2, "key3": 0.2, "thump": 0.42, "whoosh": 0.34, "swish": 0.3, "riser": 0.24, "error": 0.4,
         "shutter": 0.5, "scratch": 0.25, "scan": 0.15}
ALIAS = {"pop": "tap", "ding": "thump", "tick": "key", "swell": "riser", "thud": "thump", "buzz": "error", "slash": "swish", "swoosh": "swish"}


def resolve(events: dict) -> dict:
    """map the event names used in sfx_events() to real sound files (typing keys rotate through three variants)"""
    out, k = {}, 0
    for sid, lst in events.items():
        o = []
        for t, name in lst:
            name = ALIAS.get(name, name)
            if name == "key":
                name = f"key{k % 3 + 1}"; k += 1
            o.append((t, name))
        out[sid] = o
    return out


def ambient_bed(total: float) -> np.ndarray:
    """a very quiet, slowly moving pad (Am - F - C - G) that runs under the whole video so the cuts feel continuous"""
    n = int(total * SR); x = np.arange(n) / SR
    chords = [(110, 164.8, 220, 261.6, 329.6), (87.3, 130.8, 174.6, 220, 261.6), (130.8, 196, 261.6, 329.6, 392), (98, 146.8, 196, 246.9, 293.7)]
    seg = 8.0
    out = np.zeros(n)
    for k in range(int(total / seg) + 2):
        notes = chords[k % 4]
        c0 = k * seg - 1.5
        w = np.clip((x - c0) / 3.0, 0, 1) * np.clip((c0 + seg + 3.0 - x) / 3.0, 0, 1)
        w = np.sin(np.pi / 2 * w) ** 2
        for f in notes:
            for d in (-0.4, 0.4):
                out += w * np.sin(2 * np.pi * (f + d) * x + f) * (1.0 / len(notes))
    out *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.13 * x)
    sos = butter(2, 1100, btype="low", fs=SR, output="sos")
    out = sosfilt(sos, out)
    out *= np.minimum(1, x / 1.5) * np.minimum(1, (total - x) / 2.5)
    return (out / (np.sqrt(np.mean(out ** 2)) + 1e-9) * 0.011).astype(np.float32)


def export_events(scenes: list[dict], path: Path) -> None:
    """events.json for the browser preview: {scene id: [[seconds in scene, effect], ...]} plus the gains"""
    ev = resolve(sfx_events({s["id"]: s.get("warp") or 1 for s in scenes}))
    path.write_text(json.dumps({"events": {k: [[round(t, 3), n] for t, n in v] for k, v in ev.items()}, "gains": GAINS}), encoding="utf-8")
