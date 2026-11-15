"""Synthesize the sound effects used by render_demo.py and the player (no downloads): video/media/sfx/<name>.wav

Design rules: soft and short, no bell/ping tones. Taps are low and woody, typing keys are tiny clicks (3 variants),
transitions are filtered-air whooshes, results land with a soft sub-bass thump, errors are a low double thud.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

SR = 44100
OUT = Path(__file__).resolve().parent / "media" / "sfx"
rng = np.random.default_rng(11)


def t(d: float) -> np.ndarray:
    return np.arange(int(d * SR)) / SR


def env(x: np.ndarray, attack=0.003, decay=0.1) -> np.ndarray:
    return np.minimum(1, x / max(attack, 1e-6)) * np.exp(-x / decay)


def band(x: np.ndarray, lo: float | None, hi: float | None, order: int = 2) -> np.ndarray:
    if lo and hi:
        sos = butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    elif hi:
        sos = butter(order, hi, btype="low", fs=SR, output="sos")
    else:
        sos = butter(order, lo, btype="high", fs=SR, output="sos")
    return sosfilt(sos, x)


def sweep_filter(n: np.ndarray, f0: float, f1: float, q_steps: int = 24) -> np.ndarray:
    """noise through a band-pass whose centre moves from f0 to f1 (done in blocks)"""
    out = np.zeros_like(n)
    blk = len(n) // q_steps
    for i in range(q_steps):
        f = f0 * (f1 / f0) ** (i / (q_steps - 1))
        seg = n[i * blk:(i + 1) * blk if i < q_steps - 1 else None]
        y = band(seg, f * 0.6, min(f * 1.6, SR / 2 - 100))
        out[i * blk:i * blk + len(y)] = y
    return out


def save(name: str, x: np.ndarray, gain: float = 0.8) -> None:
    x = x / (np.max(np.abs(x)) + 1e-9) * gain
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def main() -> None:
    for old in OUT.glob("*.wav"):
        old.unlink()
    # whoosh: air moving past, band-passed noise sweeping up then down
    x = t(0.8); n = rng.standard_normal(len(x))
    y = sweep_filter(n, 250, 3500)
    save("whoosh", y * np.sin(np.pi * x / 0.8) ** 2, 0.8)
    # swish: short light air for cards sliding / strike-throughs
    x = t(0.32); n = rng.standard_normal(len(x))
    save("swish", sweep_filter(n, 1200, 5000, 12) * np.sin(np.pi * x / 0.32) ** 1.5, 0.7)
    # tap: a soft low knock, like a finger on a desk
    x = t(0.12)
    knock = np.sin(2 * np.pi * (170 - 520 * x) * x) * env(x, 0.001, 0.03)
    save("tap", knock + band(rng.standard_normal(len(x)), 300, 2200) * env(x, 0.0008, 0.01) * 0.5, 0.75)
    # keys: three tiny keyboard clicks
    for i, f in enumerate((3200, 2600, 3800)):
        x = t(0.03)
        click = band(rng.standard_normal(len(x)), f * 0.6, f * 1.5) * env(x, 0.0003, 0.004)
        save(f"key{i + 1}", click + np.sin(2 * np.pi * 1100 * x) * env(x, 0.0003, 0.006) * 0.25, 0.7)
    # thump: soft sub-bass hit for results landing
    x = t(0.55)
    save("thump", np.sin(2 * np.pi * (62 - 20 * x) * x) * env(x, 0.004, 0.16) + band(rng.standard_normal(len(x)), None, 500) * env(x, 0.001, 0.03) * 0.5, 0.85)
    # riser: air sweep that builds, used while bars grow and numbers count
    x = t(1.0); n = rng.standard_normal(len(x))
    save("riser", sweep_filter(n, 400, 4500, 20) * (x / 1.0) ** 1.6 * np.minimum(1, (1.0 - x) / 0.08), 0.5)
    # error: low double thud
    x = t(0.5); y = np.zeros(len(x))
    for at in (0.0, 0.17):
        i = int(at * SR); k = t(0.28)
        y[i:i + len(k)] += np.sin(2 * np.pi * (95 - 40 * k) * k) * env(k, 0.002, 0.07)
    save("error", band(y, None, 700), 0.8)
    # shutter: two soft mechanical clicks
    x = t(0.25); c = np.zeros(len(x))
    for at, amp in [(0.0, 1.0), (0.075, 0.65)]:
        i = int(at * SR); k = t(0.05)
        c[i:i + len(k)] += (band(rng.standard_normal(len(k)), 700, 5000) * env(k, 0.0005, 0.01) + np.sin(2 * np.pi * 900 * k) * env(k, 0.0005, 0.012) * 0.4) * amp
    save("shutter", c, 0.7)
    # scratch: pencil / marker on paper
    x = t(0.75); n = rng.standard_normal(len(x))
    save("scratch", band(n, 2500, 9000) * (0.55 + 0.45 * np.sin(2 * np.pi * 13 * x + 1)) * np.minimum(1, x / 0.05) * np.minimum(1, (0.75 - x) / 0.1), 0.45)
    # scan: a slow air sweep under the scan line
    x = t(2.2); n = rng.standard_normal(len(x))
    save("scan", sweep_filter(n, 300, 2800, 30) * np.minimum(1, x / 0.3) * np.minimum(1, (2.2 - x) / 0.4), 0.4)
    print("wrote", sorted(p.name for p in OUT.glob("*.wav")))


if __name__ == "__main__":
    main()
