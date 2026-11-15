"""Render the pitch using the team's original voice takes and presentation slides."""
from __future__ import annotations

import math
import subprocess
import wave
from pathlib import Path

from render_final_video import CLIPS

ROOT = Path(__file__).resolve().parents[1]
PRESENTATION = ROOT / "presentation"
WORK = ROOT / "video" / "recorded_build"
OUT = ROOT / "results" / "final_pitch_video_v3.mp4"
TTS = ROOT / "video" / "clean_tts"

# Ordered by their embedded recording timestamp, not their downloaded filename.
SLIDES = ["0_environment.png", "1_gap.png", "2_components.png", "3_per_plan.png", "1_gap.png", "4_exploits.png", "5_example.png", "7_parallel_second_site11704.png"]
SCENES = [(f"tts_{index:02}.wav", slide, CLIPS[index][1]) for index, slide in enumerate(SLIDES)]


def run(*args: str) -> None:
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def duration(path: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)], text=True).strip())


def timecode(seconds: float) -> str:
    ms = round(seconds * 1000)
    return f"{ms // 3_600_000:02}:{(ms // 60_000) % 60:02}:{(ms // 1000) % 60:02},{ms % 1000:03}"


def make_subtitles(durations: list[float]) -> Path:
    entries, clock, number = [], 0.0, 1
    for (_, _, text), length in zip(SCENES, durations):
        words = text.split()
        chunks = [" ".join(words[i:i + 8]) for i in range(0, len(words), 8)]
        first, last = clock + .28, clock + length - .12
        span = max(.5, last - first)
        for index, chunk in enumerate(chunks):
            start = first + index * span / len(chunks)
            end = first + (index + 1) * span / len(chunks) - .06
            entries.append(f"{number}\n{timecode(start)} --> {timecode(max(start + .4, end))}\n{chunk}\n")
            number += 1
        clock += length
    out = WORK / "subtitles.srt"
    out.write_text("\n".join(entries), encoding="utf-8")
    return out


def make_sfx(total: float, starts: list[float]) -> Path:
    # Tiny transition ticks only: no generated music under the human narration.
    rate, count = 48_000, int(total * 48_000)
    samples = [0] * count
    for start in starts[1:]:
        base = int(start * rate)
        for n in range(min(int(.12 * rate), count - base)):
            samples[base + n] = int(1600 * math.exp(-n / (rate * .03)) * math.sin(2 * math.pi * 1100 * n / rate))
    out = WORK / "transition_ticks.wav"
    with wave.open(str(out), "w") as handle:
        handle.setparams((1, 2, rate, count, "NONE", "not compressed"))
        handle.writeframes(b"".join(value.to_bytes(2, "little", signed=True) for value in samples))
    return out


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    voice = [TTS / name for name, _, _ in SCENES]
    missing = [str(path) for path in voice if not path.exists()]
    if missing:
        raise SystemExit("Missing recording(s): " + ", ".join(missing))
    durations = [duration(path) for path in voice]
    (WORK / "audio.txt").write_text("".join(f"file '{path.as_posix()}'\n" for path in voice), encoding="utf-8")
    run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(WORK / "audio.txt"), "-c:a", "pcm_s16le", str(WORK / "narration.wav"))
    videos = []
    for index, ((_, image, _), seconds) in enumerate(zip(SCENES, durations)):
        source, target = PRESENTATION / image, WORK / f"scene_{index:02}.mp4"
        frames = max(1, round(seconds * 30))
        filters = f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=white,zoompan=z='min(zoom+0.00016,1.012)':d={frames}:s=1920x1080:fps=30,format=yuv420p"
        run("ffmpeg", "-y", "-loop", "1", "-i", str(source), "-vf", filters, "-t", f"{seconds:.3f}", "-an", str(target))
        videos.append(target)
    (WORK / "video.txt").write_text("".join(f"file '{path.as_posix()}'\n" for path in videos), encoding="utf-8")
    starts, clock = [], 0.0
    for length in durations:
        starts.append(clock); clock += length
    sfx, srt = make_sfx(clock, starts), make_subtitles(durations)
    run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(WORK / "video.txt"), "-i", str(WORK / "narration.wav"), "-i", str(sfx), "-filter_complex", "[1:a][2:a]amix=inputs=2:weights='1 0.15':normalize=0[a]", "-map", "0:v", "-map", "[a]", "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k", str(WORK / "base.mp4"))
    subtitle_filter = "subtitles='" + str(srt).replace("\\", "/").replace(":", "\\:") + "':force_style='FontName=Arial,FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,BorderStyle=1,Outline=2,Shadow=1,MarginV=50,Alignment=2'"
    run("ffmpeg", "-y", "-i", str(WORK / "base.mp4"), "-vf", subtitle_filter, "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "copy", "-movflags", "+faststart", str(OUT))
    (OUT.with_suffix(".srt")).write_bytes(srt.read_bytes())
    print(OUT)


if __name__ == "__main__":
    main()
