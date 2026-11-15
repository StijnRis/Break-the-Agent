"""Hackathon cut: first neon evidence-card treatment with verified clean TTS."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from render_final_video import CLIPS, WORK as TEMPLATE_BUILD, duration, make_card, make_sfx, make_srt


ROOT = Path(__file__).resolve().parents[1]
TTS = ROOT / "video" / "clean_tts"
WORK = ROOT / "video" / "hackathon_v4_build"
OUT = ROOT / "results" / "final_pitch_video_v4.mp4"


def run(*args: str) -> None:
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    narration = [TTS / f"tts_{index:02}.wav" for index in range(len(CLIPS))]
    missing = [str(path) for path in narration if not path.exists()]
    if missing:
        raise SystemExit("Missing verified narration: " + ", ".join(missing))
    durations = [duration(path) for path in narration]

    # Reuse the first-cut visual language exactly: evidence slide on a dark
    # construction grid with mint accents, then only add gentle camera motion.
    TEMPLATE_BUILD.mkdir(parents=True, exist_ok=True)
    cards = [make_card(index, headline, detail) for index, (_, _, headline, detail) in enumerate(CLIPS)]
    (WORK / "audio.txt").write_text("".join(f"file '{path.as_posix()}'\n" for path in narration), encoding="utf-8")
    run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(WORK / "audio.txt"), "-c:a", "pcm_s16le", str(WORK / "narration.wav"))

    scenes = []
    for index, (card, seconds) in enumerate(zip(cards, durations)):
        output = WORK / f"scene_{index:02}.mp4"
        frames = max(1, round(seconds * 30))
        run("ffmpeg", "-y", "-loop", "1", "-i", str(card), "-vf", f"zoompan=z='min(zoom+0.00036,1.035)':d={frames}:s=1920x1080:fps=30,format=yuv420p", "-t", f"{seconds:.3f}", "-an", str(output))
        scenes.append(output)
    (WORK / "video.txt").write_text("".join(f"file '{path.as_posix()}'\n" for path in scenes), encoding="utf-8")

    starts, elapsed = [], 0.0
    for seconds in durations:
        starts.append(elapsed)
        elapsed += seconds
    soundtrack = make_sfx(elapsed, starts)
    srt = make_srt(durations)
    shutil.copy2(srt, WORK / "subtitles.srt")
    run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(WORK / "video.txt"), "-i", str(WORK / "narration.wav"), "-i", str(soundtrack), "-filter_complex", "[1:a][2:a]amix=inputs=2:weights='1 0.20':normalize=0[a]", "-map", "0:v", "-map", "[a]", "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "aac", "-b:a", "192k", str(WORK / "base.mp4"))
    subtitle_filter = "subtitles='" + str(WORK / "subtitles.srt").replace("\\", "/").replace(":", "\\:") + "':force_style='FontName=Arial,FontSize=12,PrimaryColour=&H00FFFFFF,OutlineColour=&H0010150C,BorderStyle=1,Outline=2,Shadow=1,MarginV=50,Alignment=2'"
    run("ffmpeg", "-y", "-i", str(WORK / "base.mp4"), "-vf", subtitle_filter, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "copy", "-movflags", "+faststart", str(OUT))
    shutil.copy2(WORK / "subtitles.srt", OUT.with_suffix(".srt"))
    print(OUT)


if __name__ == "__main__":
    main()
