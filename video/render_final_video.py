"""Render the hackathon pitch video from the recorded voice-over clips.

Usage:
    python video/render_final_video.py
"""
from __future__ import annotations

import math
import shutil
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "presentation"
WORK = ROOT / "video" / "build"
OUT = ROOT / "results" / "final_pitch_video.mp4"
DEFAULT_AUDIO = Path(r"C:\Users\Stijn\Downloads\drive-download-20261114T180429Z-1-001")

# The clips are individual takes of the supplied script, in recording order.
CLIPS = [
    ("14 Nov at 20-00.m4a", "Blueprint Lab turns messy architectural floor plans into structured, machine-readable schematics.", "FROM BLUEPRINT → SCHEMATIC", "A real-world skill. A measurable agent challenge."),
    ("14 Nov at 20-01.m4a", "It sounds simple until you ask an AI agent to do it precisely.", "THE PRECISION GAP", "Seeing a line is easy. Locating it accurately is hard."),
    ("14 Nov at 20-01(1).m4a", "The agent can zoom into the drawing, read room labels, estimate scale, segment rooms, measure areas, preview its work, and submit a final schematic.", "TOOLS, NOT TRAINING WHEELS", "Zoom · OCR · scale · segmentation · measurement · preview"),
    ("14 Nov at 20-01(2).m4a", "Tools alone are not enough. The challenge is using them well.", "ACCESS ≠ ABILITY", "Every tool is available. The decisions are still difficult."),
    ("14 Nov at 20-01(3).m4a", "Across our benchmark, Gemini reaches roughly 0.26, while our deterministic computer-vision reference reaches 0.57. The agent often guesses the scale, traces rooms too roughly, and misses precise doors and windows.", "THE GAP IS REAL", "Gemini 0.26      CV reference 0.57"),
    ("14 Nov at 20-01(4).m4a", "That makes this a useful reinforcement-learning environment: every decision is inspectable, every action has a cost, and the reward checks actual geometric accuracy against surveyed ground truth.", "LEARNABLE. AUDITABLE.", "Reward follows geometry—not vibes."),
    ("14 Nov at 20-01(5).m4a", "No hidden answers. No shortcut for doing nothing. Just a hard, measurable real-world skill: reading construction drawings.", "NO EASY MODE", "Surveyed ground truth stays inside the verifier."),
    ("14 Nov at 20-02.m4a", "This is Blueprint Lab—where we break the agent, so it can learn to build better.", "BLUEPRINT LAB", "Break the agent. Build better agents."),
]


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)
    ], text=True).strip())


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    return ImageFont.truetype(name, size)


def contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    copy = image.convert("RGB")
    copy.thumbnail(size, Image.Resampling.LANCZOS)
    return copy


def make_card(index: int, headline: str, detail: str) -> Path:
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), "#07151d")
    d = ImageDraw.Draw(img)
    # Neon construction-grid background.
    for x in range(0, w, 48): d.line((x, 0, x, h), fill="#0b2430", width=1)
    for y in range(0, h, 48): d.line((0, y, w, y), fill="#0b2430", width=1)
    d.rectangle((0, 0, w, 14), fill="#5cf2b0")
    d.text((94, 78), "JUNCTION 2026  /  AFTERQUERY CHALLENGE", font=font(25, True), fill="#77c5ac")
    d.text((94, 137), headline, font=font(64, True), fill="white")
    d.text((98, 220), detail, font=font(31), fill="#b8c9c7")
    d.rounded_rectangle((94, 902, 545, 963), radius=17, fill="#163548", outline="#5cf2b0", width=2)
    d.text((120, 917), f"0{index + 1}  /  08", font=font(24, True), fill="#5cf2b0")
    image_names = ["0_environment.png", "1_gap.png", "2_components.png", "3_per_plan.png", "4_exploits.png", "5_example.png", "6_parallel_best_site980.png", "7_parallel_second_site11704.png"]
    source = ASSETS / image_names[index]
    if source.exists():
        visual = contain(Image.open(source), (1510, 595))
        plate = Image.new("RGB", (1550, 635), "#f4f5ee")
        plate.paste(visual, ((1550 - visual.width) // 2, (635 - visual.height) // 2))
        plate = plate.filter(ImageFilter.UnsharpMask(radius=1, percent=130, threshold=3))
        img.paste(plate, (280, 310))
        d.rounded_rectangle((280, 310, 1830, 945), radius=12, outline="#5cf2b0", width=3)
    img.save(WORK / f"card_{index:02}.png")
    return WORK / f"card_{index:02}.png"


def timecode(seconds: float) -> str:
    ms = round(seconds * 1000)
    return f"{ms // 3_600_000:02}:{(ms // 60_000) % 60:02}:{(ms // 1000) % 60:02},{ms % 1000:03}"


def make_srt(durations: list[float]) -> Path:
    now = 0.0
    entries = []
    index = 1
    for i, (_, text, _, _) in enumerate(CLIPS):
        words = text.split()
        # Caption-sized chunks, so a long narration never hides the evidence
        # graphic behind one giant block of text.
        chunks = [" ".join(words[n:n + 8]) for n in range(0, len(words), 8)]
        usable_start, usable_end = now + 0.32, now + durations[i] - 0.16
        span = max(.6, usable_end - usable_start)
        for chunk_index, chunk in enumerate(chunks):
            start = usable_start + span * chunk_index / len(chunks)
            end = usable_start + span * (chunk_index + 1) / len(chunks) - .08
            entries.append(f"{index}\n{timecode(start)} --> {timecode(max(start + .45, end))}\n{chunk}\n")
            index += 1
        now += durations[i]
    out = WORK / "subtitles.srt"
    out.write_text("\n".join(entries), encoding="utf-8")
    return out


def make_sfx(total: float, starts: list[float]) -> Path:
    rate, frames = 48_000, int(total * 48_000)
    samples = [0] * frames
    for start in starts:
        base = int(start * rate)
        for n in range(min(int(.26 * rate), frames - base)):
            envelope = math.exp(-n / (rate * .055))
            tone = math.sin(2 * math.pi * (880 + 220 * n / rate) * n / rate)
            samples[base + n] += int(4_400 * envelope * tone)
    # A deliberately quiet, copyright-free electronic bed: a slow arpeggio and
    # low pulse create hackathon energy without competing with narration.
    notes = (146.83, 174.61, 220.0, 293.66)
    for step in range(int(total * 2)):
        base = step * rate // 2
        freq = notes[step % len(notes)]
        for n in range(min(rate // 2, frames - base)):
            envelope = min(1, n / (rate * .035)) * math.exp(-n / (rate * .42))
            tone = math.sin(2 * math.pi * freq * n / rate) + .35 * math.sin(2 * math.pi * freq * 2 * n / rate)
            samples[base + n] += int(700 * envelope * tone)
    out = WORK / "tech_clicks.wav"
    with wave.open(str(out), "w") as wav:
        wav.setparams((1, 2, rate, frames, "NONE", "not compressed"))
        wav.writeframes(b"".join(int(max(-32768, min(32767, x))).to_bytes(2, "little", signed=True) for x in samples))
    return out


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-dir", type=Path, default=DEFAULT_AUDIO)
    parser.add_argument("--voiceover-dir", type=Path, default=WORK,
                        help="Directory containing Gemini-generated tts_00.wav through tts_07.wav.")
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    generated = [args.voiceover_dir / f"tts_{i:02}.wav" for i in range(len(CLIPS))]
    if all(path.exists() for path in generated):
        clips = generated
    else:
        audio_dir = args.audio_dir
        if not audio_dir.exists():
            raise SystemExit(f"Audio directory not found: {audio_dir}")
        missing = [name for name, *_ in CLIPS if not (audio_dir / name).exists()]
        if missing:
            raise SystemExit("Missing voice clips: " + ", ".join(missing))
        clips = [audio_dir / name for name, *_ in CLIPS]
    durations = [duration(path) for path in clips]
    cards = [make_card(i, headline, detail) for i, (_, _, headline, detail) in enumerate(CLIPS)]
    (WORK / "audio.txt").write_text("".join(f"file '{p.as_posix()}'\n" for p in clips), encoding="utf-8")
    run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(WORK / "audio.txt"), "-c:a", "pcm_s16le", str(WORK / "narration.wav"))
    starts, elapsed = [], 0.0
    for item in durations:
        starts.append(elapsed)
        elapsed += item
    sfx = make_sfx(elapsed, starts)
    srt = make_srt(durations)
    # One still per voice segment, gently zoomed and crossfaded into the next.
    segment_paths = []
    for i, (card, seconds) in enumerate(zip(cards, durations)):
        segment = WORK / f"segment_{i:02}.mp4"
        frames = max(1, round(seconds * 30))
        run("ffmpeg", "-y", "-loop", "1", "-i", str(card), "-vf", f"zoompan=z='min(zoom+0.00045,1.045)':d={frames}:s=1920x1080:fps=30,format=yuv420p", "-t", f"{seconds:.3f}", "-an", str(segment))
        segment_paths.append(segment)
    (WORK / "video.txt").write_text("".join(f"file '{p.as_posix()}'\n" for p in segment_paths), encoding="utf-8")
    run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(WORK / "video.txt"), "-i", str(WORK / "narration.wav"), "-i", str(sfx), "-filter_complex", "[1:a][2:a]amix=inputs=2:weights='1 0.34':normalize=0[a]", "-map", "0:v", "-map", "[a]", "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(WORK / "with_audio.mp4"))
    subtitle_filter = "subtitles='" + str(srt).replace("\\", "/").replace(":", "\\:") + "':force_style='FontName=Arial,FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H0010150C,BorderStyle=1,Outline=2,Shadow=1,MarginV=50,Alignment=2'"
    run("ffmpeg", "-y", "-i", str(WORK / "with_audio.mp4"), "-vf", subtitle_filter, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "copy", "-movflags", "+faststart", str(args.output))
    shutil.copy2(srt, args.output.with_suffix(".srt"))
    print(args.output)


if __name__ == "__main__":
    main()
